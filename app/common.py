import os
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import EmailModel, LoginSettings
from schemas import RecipientModel

login_settings = LoginSettings()


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


# ============== Send Single Email ==============
def send_single_email(
    subject: str,
    body: str,
    sender: EmailModel.SenderModel,
    recipient: RecipientModel,
    attachment_path: str,
):
    emails = recipient.emails
    formatted_name = recipient.name
    formatted_name = " ".join([name.capitalize() for name in formatted_name.lower().split(" ")])
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(login_settings.email, login_settings.password.get_secret_value())
        for email in emails:
            msg = get_message_object(subject, sender, attachment_path)
            msg.attach(MIMEText(body.format(name=formatted_name, sender_name=sender["name"]), "plain"))
            msg["to"] = email
            try:
                smtp_server.sendmail(sender["email"], email, msg.as_string())
                print(f"Email sent to {email}")
            except Exception as e:
                print(f"Failed to send email to {email}: {e}")


# ============== Send Emails using Multithreading ==============
def send_email(
    subject: str,
    body: str,
    sender: EmailModel.SenderModel,
    recipients: list[RecipientModel],
    attachment_path: str = None,
):
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(send_single_email, subject, body, sender, recipient, attachment_path)
            for recipient in recipients
        ]
        for future in futures:
            future.result()

    print("All Emails Sent!")
