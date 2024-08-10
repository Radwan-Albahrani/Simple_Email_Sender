from config import EmailModel, EmailPathsSettings
from schemas import RecipientModel
from services.email_sender import email_sender


def main():
    email_paths = EmailPathsSettings()
    email = EmailModel()

    # ============== Email Sender ==============
    sender = email.email_sender.model_dump()

    # ============== Subject and body ==============
    subject = email.subject
    template = open(email.template).read()

    # ============== Recipients ==============
    recipients: list[RecipientModel] = RecipientModel.from_file(email_paths.test_path)
    email_sender(
        subject=subject,
        sender=sender,
        recipients=recipients,
        attachment_path=email.attachment_path,
        template=template,
    )


if __name__ == "__main__":
    main()
