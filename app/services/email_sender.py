import time

from common import send_email
from config import SenderSettings
from schemas import RecipientModel


def prompt_yes_no(question: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    answer = input(f"{question} ({suffix}): ").strip().casefold()
    if not answer:
        return default
    return answer in {"y", "yes"}


def prompt_starting_position(total: int) -> int:
    """Ask which recipient to resume from; blank means start at the beginning."""
    while True:
        raw = input(f"Start from position (0-{total - 1}, blank for 0): ").strip()
        if not raw:
            return 0
        if raw.isdigit() and 0 <= int(raw) < total:
            return int(raw)
        print(f"Enter a number between 0 and {total - 1}.")


# ============== Send Emails ==============
def email_sender(
    subject: str,
    sender: SenderSettings,
    recipients: list[RecipientModel],
    attachment_path: str,
    template: str,
) -> None:
    total_addresses = sum(len(recipient.emails) for recipient in recipients)
    print(f"\nReady to send: {len(recipients)} recipients / {total_addresses} addresses")
    print(f"From:    {sender.name} <{sender.email}>")
    print(f"Subject: {subject}")
    print(f"Attach:  {attachment_path}")

    use_llm = prompt_yes_no("Personalise each email with the LLM?")
    starting_position = prompt_starting_position(len(recipients))

    remaining = len(recipients) - starting_position
    print(f"\nAbout to send {remaining} emails. This cannot be undone.")
    if input("Type YES to confirm: ") != "YES":
        print("Cancelled.")
        return

    start_time = time.time()
    send_email(
        subject=subject,
        body=template,
        sender=sender,
        recipients=recipients,
        attachment_path=attachment_path,
        use_llm=use_llm,
        starting_position=starting_position,
    )
    print(f"Time taken: {time.time() - start_time:.1f}s")
