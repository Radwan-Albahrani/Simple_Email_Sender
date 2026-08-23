"""Discovery and selection of recipient list files under ``assets/``."""

from dataclasses import dataclass
from pathlib import Path

from schemas import RecipientModel

DEFAULT_SEARCH_ROOT = Path("assets")
TEST_HINTS = ("test",)


@dataclass(frozen=True)
class RecipientList:
    path: Path
    recipients: list[RecipientModel]

    @property
    def label(self) -> str:
        return self.path.as_posix()

    @property
    def is_test(self) -> bool:
        parts = {part.casefold() for part in self.path.parts}
        return any(hint in parts for hint in TEST_HINTS)


def discover_recipient_lists(
    search_root: Path = DEFAULT_SEARCH_ROOT,
    exclude: tuple[Path, ...] = (),
) -> list[RecipientList]:
    """Find every JSON file under ``search_root`` that parses as a recipient list.

    Files with a different shape (raw scrape dumps, config, ...) are skipped
    silently, as is anything in ``exclude`` -- normally the blacklist.
    """
    excluded = {path.resolve() for path in exclude}
    found: list[RecipientList] = []

    for path in sorted(search_root.rglob("*.json")):
        if path.resolve() in excluded:
            continue
        try:
            recipients = RecipientModel.from_file(path)
        except (OSError, ValueError):
            # Not a recipient list (raw scrape dump, config file, ...) -- skip it.
            continue
        if recipients:
            found.append(RecipientList(path=path, recipients=recipients))

    # Test lists first, then largest to smallest -- the common picks sit at the top.
    found.sort(key=lambda item: (not item.is_test, -len(item.recipients), item.label))
    return found


def parse_selection(raw: str, count: int) -> list[int]:
    """Turn a selection string into a list of 0-based indices.

    Accepts ``all``, ``test``, single numbers, comma-separated numbers and
    ``a-b`` ranges, in any combination (e.g. ``1,3-5``). Raises ``ValueError``
    on anything it can't make sense of.
    """
    raw = raw.strip().casefold()
    if not raw:
        raise ValueError("nothing selected")
    if raw == "all":
        return list(range(count))

    indices: list[int] = []
    for token in raw.replace(" ", ",").split(","):
        if not token:
            continue
        if "-" in token[1:]:
            start_text, _, end_text = token.partition("-")
            start, end = _to_index(start_text, count), _to_index(end_text, count)
            if start > end:
                start, end = end, start
            indices.extend(range(start, end + 1))
        else:
            indices.append(_to_index(token, count))

    if not indices:
        raise ValueError("nothing selected")
    # Preserve order, drop repeats.
    return list(dict.fromkeys(indices))


def _to_index(text: str, count: int) -> int:
    text = text.strip()
    if not text.isdigit():
        raise ValueError(f"{text!r} is not a list number")
    index = int(text) - 1
    if not 0 <= index < count:
        raise ValueError(f"{text} is out of range (1-{count})")
    return index


def merge_recipients(
    lists: list[RecipientList],
    blacklist: list[RecipientModel],
) -> list[RecipientModel]:
    """Concatenate the chosen lists, dropping duplicates and blacklisted names."""
    blocked = {entry.key for entry in blacklist}
    seen: set[str] = set()
    merged: list[RecipientModel] = []
    for recipient_list in lists:
        for recipient in recipient_list.recipients:
            if recipient.key in blocked or recipient.key in seen:
                continue
            seen.add(recipient.key)
            merged.append(recipient)
    return merged


def format_table(lists: list[RecipientList]) -> str:
    """Render the numbered menu of discovered lists."""
    width = len(str(len(lists)))
    label_width = max((len(item.label) for item in lists), default=0)
    rows: list[str] = []
    for number, item in enumerate(lists, start=1):
        tag = "  [test]" if item.is_test else ""
        count = f"{len(item.recipients):>5} recipients"
        rows.append(f"  {number:>{width}}) {item.label:<{label_width}}  {count}{tag}")
    return "\n".join(rows)


def select_recipient_lists(lists: list[RecipientList]) -> list[RecipientList]:
    """Prompt until the user makes a valid selection, or returns nothing to cancel."""
    print("\nAvailable recipient lists:")
    print(format_table(lists))
    print("\nSelect with numbers (1), several (1,3), a range (1-3), 'all', or 'test'.")

    while True:
        raw = input("Selection (blank to cancel): ")
        if not raw.strip():
            return []
        if raw.strip().casefold() == "test":
            chosen = [item for item in lists if item.is_test]
            if not chosen:
                print("No test list found. Pick a number instead.")
                continue
            return chosen
        try:
            indices = parse_selection(raw, len(lists))
        except ValueError as exc:
            print(f"Invalid selection: {exc}")
            continue
        return [lists[index] for index in indices]
