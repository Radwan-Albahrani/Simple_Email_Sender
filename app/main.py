from config import EmailModel, EmailPathsSettings
from schemas import RecipientModel
from services.email_sender import email_sender
from tinydb import TinyDB


def main():
    email_paths = EmailPathsSettings()
    email = EmailModel()

    # ============== Email Sender ==============
    sender = email.email_sender.model_dump()

    # ============== Subject and body ==============
    subject = email.subject
    template = open(email.template).read()

    # TinyDB
    # tinydb = TinyDB("./assets/input/dammam/small_company_size.json")

    # ============== Recipients ==============
    recipients: list[RecipientModel] = RecipientModel.from_file(email_paths.test_path)
    blacklist: list[RecipientModel] = RecipientModel.from_file(email_paths.blacklist_path)

    recipients = [recipient for recipient in recipients if recipient not in blacklist]

    email_sender(
        subject=subject,
        sender=sender,
        recipients=recipients,
        attachment_path=email.attachment_path,
        template=template,
    )


if __name__ == "__main__":
    main()
