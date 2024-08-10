from common import send_email
from config import EmailModel
from schemas import RecipientModel


# ============== Send Emails ==============
def email_sender(
    subject: str,
    sender: EmailModel.SenderModel,
    recipients: list[RecipientModel],
    attachment_path: str,
    template: str,
):
    print(f"Sending Emails.. Total count: {len(recipients)}")
    use_llm = False
    ans = input("Use llm? y/n: ")
    if ans == "y":
        use_llm = True
    sure = input("Are you sure you want to send these emails? (YES/n): ")
    if sure == "YES":
        send_email(
            subject=subject,
            body=template,
            sender=sender,
            recipients=recipients,
            attachment_path=attachment_path,
            use_llm=use_llm,
        )
