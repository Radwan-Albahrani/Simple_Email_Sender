from pathlib import Path

from config import EmailModel, EmailPathsSettings, load
from schemas import RecipientModel
from services.email_sender import email_sender
from services.recipient_lists import (
    discover_recipient_lists,
    merge_recipients,
    select_recipient_lists,
)


def main() -> None:
    email_paths = load(EmailPathsSettings)
    email = load(EmailModel)

    # ============== Subject, template and blacklist ==============
    template = Path(email.template).read_text(encoding="utf-8")
    blacklist_path = Path(email_paths.blacklist_path)
    blacklist: list[RecipientModel] = (
        RecipientModel.from_file(blacklist_path) if blacklist_path.exists() else []
    )

    # ============== Pick recipient lists ==============
    available = discover_recipient_lists(exclude=(blacklist_path,))
    if not available:
        print("No recipient lists found under assets/.")
        return

    chosen = select_recipient_lists(available)
    if not chosen:
        print("Cancelled.")
        return

    recipients = merge_recipients(chosen, blacklist)
    selected_total = sum(len(item.recipients) for item in chosen)
    print(
        f"\nSelected {len(chosen)} list(s): {', '.join(item.label for item in chosen)}"
        f"\n{selected_total} entries -> {len(recipients)} after removing duplicates"
        f" and {len(blacklist)} blacklisted"
    )
    if not recipients:
        print("Nothing left to send after filtering.")
        return

    email_sender(
        subject=email.subject,
        sender=email.email_sender,
        recipients=recipients,
        attachment_path=email.attachment_path,
        template=template,
    )


if __name__ == "__main__":
    main()
