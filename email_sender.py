from common import send_email
from config import EmailModel, EmailPathsSettings
from schema import RecipientModel

email_paths = EmailPathsSettings()
email = EmailModel()

# ============== Email Sender ==============
sender = email.email_sender.model_dump()

# ============== Subject and body ==============
subject = email.subject
template = open(email.template).read()

# ============== Recipients ==============
recipients: list[RecipientModel] = RecipientModel.from_file(email_paths.test_path)

# ============== Send Emails ==============
if __name__ == "__main__":
    print(f"Sending Emails.. Total count: {len(recipients)}")
    sure = input("Are you sure you want to send these emails? (YES/n): ")
    if sure == "YES":
        send_email(
            subject=subject,
            body=template,
            sender=sender,
            recipients=recipients,
            attachment_path=email.attachment_path,
        )
