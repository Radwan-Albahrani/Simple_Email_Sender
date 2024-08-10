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
    use_llm = False
    ans = input("Use llm? y/n: ")
    if ans == "y":
        use_llm = True
    email_sender(
        subject=subject,
        sender=sender,
        recipients=recipients,
        email=email,
        template=template,
        use_llm=use_llm,
    )


if __name__ == "__main__":
    main()
