import logging
import os
import re
import smtplib
import time
from concurrent.futures import ThreadPoolExecutor
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import google.generativeai as genai
import requests
from config import EmailModel, GeminiApi, LoginSettings
from schemas import RecipientModel

login_settings = LoginSettings()
gemini_api = GeminiApi()

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
def get_message_object(subject, sender, attachment_path=None):
    msg = MIMEMultipart()
    msg["subject"] = subject
    msg["from"] = sender["name"]
    if attachment_path:
        filename = os.path.basename(attachment_path)
        attachment = open(attachment_path, "rb")
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {filename}")
        msg.attach(part)
    return msg


def parse_search_query_response(search_query=""):
    url = gemini_api.search_url
    url = url.format(query=search_query)
    response = requests.get(url)
    response_json = response.json()
    search_results = response_json.get("results", [])
    list_of_results = []
    if search_results:
        for result in search_results[:5]:
            title = result.get("title", "")
            content = result.get("content", "")
            list_of_results.append({"title": title, "content": content})
    return list_of_results


def parse_generated_content(
    content: str,
    email: EmailModel,
):
    # find any brackets that contain any thing
    matches = re.findall(r"\[.*?\]", content)
    if matches:
        return email.default_body
    return content


# ============== Send Single Email ==============
def send_single_email(
    subject: str,
    body: str,
    sender: EmailModel.SenderModel,
    recipient: RecipientModel,
    attachment_path: str,
    use_llm: bool = False,
):
    email = EmailModel()
    emails = recipient.emails
    formatted_name = recipient.name
    formatted_name = " ".join([name.capitalize() for name in formatted_name.lower().split(" ")])
    if use_llm:
        global model
        search_query = f"{formatted_name} Company Projects Saudi Arabia"
        list_of_results = parse_search_query_response(search_query=search_query)

        generated_body = model.generate_content(
            gemini_api.prompt.format(
                resume_text=gemini_api.resume_text,
                company_name=formatted_name,
                email_template=gemini_api.email_template,
                extra_info=list_of_results,
            )
        ).text

        generated_body = parse_generated_content(generated_body, email)
    if use_llm:
        body = body.format(name=formatted_name, sender_name=sender["name"], body=generated_body)
    else:
        body = body.format(name=formatted_name, sender_name=sender["name"], body=email.default_body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(login_settings.email, login_settings.password.get_secret_value())
        for email in emails:
            msg = get_message_object(subject, sender, attachment_path)
            msg.attach(MIMEText(body, "plain"))
            msg["to"] = email
            try:
                smtp_server.sendmail(sender["email"], email, msg.as_string())
                logger.info(f"Email sent successfully to {email}")
                print(f"Email sent to {email}")
            except Exception as e:
                error_message = f"Failed to send email to {email}: {str(e)}"
                logger.error(error_message)
                print(error_message)


# ============== Send Emails using Multithreading ==============
def send_email(
    subject: str,
    body: str,
    sender: EmailModel.SenderModel,
    recipients: list[RecipientModel],
    attachment_path: str = None,
    use_llm: bool = False,
):
    logger.info(f"Starting email sending process for {len(recipients)} recipients")
    if use_llm:
        global model
        gemini = genai.configure(api_key=gemini_api.key.get_secret_value())
        model = genai.GenerativeModel("gemini-1.5-flash")

    batch_size = 10
    for i in range(0, len(recipients), batch_size):
        batch = recipients[i : i + batch_size]

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(send_single_email, subject, body, sender, recipient, attachment_path, use_llm)
                for recipient in batch
            ]
            for future in futures:
                future.result()

        logger.info(f"Sent emails to recipients {i+1} to {min(i+batch_size, len(recipients))}")

        if i + batch_size < len(recipients):
            logger.info("Waiting 1 minute before sending next batch")
            time.sleep(60)  # Wait for 60 seconds (1 minute)

    logger.info("All Emails Sent!")
    print("All Emails Sent!")
