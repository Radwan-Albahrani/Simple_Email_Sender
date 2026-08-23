"""One-off cleanup of raw scraped exhibitor data into recipient lists.

Reads the raw ``response*.json`` dumps and writes de-duplicated, ASCII-cleaned
``{name, emails}`` lists. Run it directly:

    python app/services/response_parser.py --input-dir assets/input --output-dir assets/output
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

Recipient = dict[str, Any]


def extract_recipients(raw_path: Path) -> list[Recipient]:
    """Pull ``{name, emails}`` entries out of a raw scrape dump."""
    with raw_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    nodes = data["data"]["response"]["exhibitors"]["nodes"]
    recipients: list[Recipient] = []
    for node in nodes:
        raw_email = node.get("email")
        if not raw_email:
            continue
        emails = [email.strip() for email in raw_email.split(",") if email.strip()]
        if emails:
            recipients.append({"name": node["name"], "emails": emails})
    return recipients


def deduplicate(recipients: list[Recipient]) -> list[Recipient]:
    """Drop repeated company names, keeping the first occurrence."""
    seen: set[str] = set()
    unique: list[Recipient] = []
    for recipient in recipients:
        name = recipient["name"]
        if name in seen:
            print(f"Duplicate: {name}")
            continue
        seen.add(name)
        unique.append(recipient)
    return unique


def clean(recipients: list[Recipient]) -> list[Recipient]:
    """Strip non-ASCII/punctuation noise out of names and addresses."""
    cleaned: list[Recipient] = []
    for recipient in recipients:
        name = re.sub(r"[^\x00-\x7F]+", "", recipient["name"])
        name = re.sub(r"[^A-Za-z0-9\s]+", "", name).strip()
        emails = [re.sub(r"[^\w.\-@]", "", email) for email in recipient["emails"]]
        cleaned.append({"name": name, "emails": emails})
    return cleaned


def write_json(path: Path, payload: list[Recipient]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Wrote {len(payload)} entries to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("assets/input"))
    parser.add_argument("--output-dir", type=Path, default=Path("assets/output"))
    args = parser.parse_args()

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir

    general = extract_recipients(input_dir / "response.json")
    startups = extract_recipients(input_dir / "response_startups.json")

    write_json(output_dir / "emails.json", general + startups)
    write_json(output_dir / "emails_startups.json", startups)
    write_json(output_dir / "emails_cleaned.json", clean(deduplicate(general + startups)))
    write_json(output_dir / "emails_startups_cleaned.json", clean(deduplicate(startups)))


if __name__ == "__main__":
    main()
