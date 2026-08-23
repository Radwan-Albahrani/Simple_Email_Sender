import logging
import os
import random
import re
import smtplib
import time
from concurrent.futures import ThreadPoolExecutor
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import httpx
import requests
from google import genai
from google.genai import errors as genai_errors
from pydantic import ValidationError

from config import EmailModel, GeminiApi, LoginSettings, SenderSettings, load
from schemas import RecipientModel, SearchResponse, SearchResult

login_settings = load(LoginSettings)

# Retry/pacing knobs
MAX_SMTP_ATTEMPTS = 5
SMTP_RETRY_DELAY = (60, 70)
SEARCH_TIMEOUT_SECONDS = 15
SEARCH_RESULT_LIMIT = 5
BATCH_SIZE = 10
MAX_WORKERS = 8

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging
logging.basicConfig(
    filename=os.path.join(log_dir, "email_logs.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============== Prepare message ==============
def get_message_object(
    subject: str,
    sender: SenderSettings,
    attachment_path: str | None = None,
) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = formataddr((sender.name, sender.email))
    if attachment_path:
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)
    return msg


def parse_search_query_response(gemini_api: GeminiApi, search_query: str = "") -> list[SearchResult]:
    """Query the local SearXNG instance for context about a company.

    Returns an empty list if the search instance is unreachable or returns
    something unexpected -- the caller falls back to a body with no extra info.
    """
    url = gemini_api.search_url.format(query=search_query)
    try:
        response = requests.get(url, timeout=SEARCH_TIMEOUT_SECONDS)
        response.raise_for_status()
        response_json = response.json()
        parsed = SearchResponse.model_validate(response_json)
    except (requests.RequestException, ValueError, ValidationError) as exc:
        logger.warning(f"Search lookup failed for {search_query!r}: {exc}")
        return []

    return parsed.results[:SEARCH_RESULT_LIMIT]


def parse_generated_content(content: str, default_body: str) -> str:
    """Reject a generated body that still contains [placeholders]."""
    if re.search(r"\[.*?\]", content):
        return default_body
    return content


def generate_email_body(
    client: genai.Client,
    gemini_api: GeminiApi,
    company_name: str,
    default_body: str,
) -> str:
    """Generate a personalised body, falling back to the default on any failure."""
    search_query = f"{company_name} Company Projects Saudi Arabia"
    list_of_results = parse_search_query_response(gemini_api, search_query=search_query)

    try:
        # The SDK's own `contents` union references an optional Pillow type we don't install.
        response = client.models.generate_content(  # pyright: ignore[reportUnknownMemberType]
            model=gemini_api.model,
            contents=gemini_api.prompt.format(
                resume_text=gemini_api.resume_text,
                company_name=company_name,
                email_template=gemini_api.email_template,
                extra_info=[result.model_dump() for result in list_of_results],
            ),
        )
        generated_body = response.text
    except (genai_errors.APIError, httpx.HTTPError, ValueError) as exc:
        logger.error(f"Gemini generation failed for {company_name}: {exc}")
        return default_body

    if not generated_body:
        logger.warning(f"Gemini returned an empty body for {company_name}; using the default")
        return default_body

    return parse_generated_content(generated_body.strip(), default_body)


# ============== Send Single Email ==============
def send_single_email(
    subject: str,
    body: str,
    sender: SenderSettings,
    recipient: RecipientModel,
    attachment_path: str | None,
    default_body: str,
    gemini_api: GeminiApi | None = None,
    client: genai.Client | None = None,
) -> None:
    formatted_name = " ".join(name.capitalize() for name in recipient.name.lower().split(" "))

    if client is not None and gemini_api is not None:
        generated_body = generate_email_body(client, gemini_api, formatted_name, default_body)
    else:
        generated_body = default_body

    use_llm = client is not None
    body = body.format(name=formatted_name, sender_name=sender.name, body=generated_body)

    # Track what already went out so an SMTP reconnect never re-sends to the same address.
    pending = list(recipient.emails)
    for attempt in range(1, MAX_SMTP_ATTEMPTS + 1):
        if not pending:
            return
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
                smtp_server.login(login_settings.email, login_settings.password.get_secret_value())
                for email in list(pending):
                    msg = get_message_object(subject, sender, attachment_path)
                    msg.attach(MIMEText(body, "plain"))
                    msg["To"] = email
                    try:
                        smtp_server.sendmail(sender.email, email, msg.as_string())
                        pending.remove(email)
                        logger.info(f"Email sent successfully to {email} - LLM: {use_llm}")
                        print(f"Email sent to {email}")
                    except smtplib.SMTPRecipientsRefused as exc:
                        # Permanently bad address -- don't retry it.
                        pending.remove(email)
                        logger.error(f"Recipient refused {email}: {exc}")
                        print(f"Recipient refused {email}: {exc}")
            return
        except (smtplib.SMTPException, OSError) as exc:
            error_message = f"SMTP failure (attempt {attempt}/{MAX_SMTP_ATTEMPTS}) for {recipient.name}: {exc}"
            logger.error(error_message)
            print(error_message)
            if attempt < MAX_SMTP_ATTEMPTS:
                time.sleep(random.randint(*SMTP_RETRY_DELAY))

    logger.error(f"Giving up on {recipient.name} after {MAX_SMTP_ATTEMPTS} attempts; unsent: {pending}")
    print(f"Giving up on {recipient.name}; unsent: {pending}")


# ============== Send Emails using Multithreading ==============
def send_email(
    subject: str,
    body: str,
    sender: SenderSettings,
    recipients: list[RecipientModel],
    attachment_path: str | None = None,
    use_llm: bool = False,
    starting_position: int = 0,
) -> None:
    logger.info(f"Starting email sending process for {len(recipients)} recipients. LLM: {use_llm}")
    default_body = load(EmailModel).default_body

    gemini_api: GeminiApi | None = None
    client: genai.Client | None = None
    if use_llm:
        gemini_api = load(GeminiApi)
        client = genai.Client(api_key=gemini_api.key.get_secret_value())

    for i in range(starting_position, len(recipients), BATCH_SIZE):
        batch = recipients[i : i + BATCH_SIZE]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(
                    send_single_email,
                    subject,
                    body,
                    sender,
                    recipient,
                    attachment_path,
                    default_body,
                    gemini_api,
                    client,
                )
                for recipient in batch
            ]
            for future in futures:
                future.result()

        logger.info(f"Sent emails to recipients {i + 1} to {min(i + BATCH_SIZE, len(recipients))} - LLM: {use_llm}")

        if i + BATCH_SIZE < len(recipients):
            wait_label = "one minute" if use_llm else "10 seconds"
            logger.info(f"Waiting {wait_label} before sending next batch")
            time.sleep(60 if use_llm else 10)

    logger.info("All Emails Sent!")
    print("All Emails Sent!")
