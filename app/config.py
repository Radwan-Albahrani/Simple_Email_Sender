from pathlib import Path
from typing import Any, cast

from pydantic import Field, model_validator
from pydantic.types import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ASSETS_DIR = Path("assets")
ATTACHMENTS_DIR = ASSETS_DIR / "attachments"
TEMPLATES_DIR = ASSETS_DIR / "templates"

DEFAULT_PROMPT_PATH = TEMPLATES_DIR / "gemini_prompt.txt"
DEFAULT_BODY_PATH = TEMPLATES_DIR / "default_body.txt"
DEFAULT_EMAIL_TEMPLATE_PATH = TEMPLATES_DIR / "email_template.txt"
DEFAULT_RESUME_TEXT_PATH = ATTACHMENTS_DIR / "resume_text.txt"
DEFAULT_BLACKLIST_PATH = ASSETS_DIR / "output" / "blacklist.json"
DEFAULT_SEARCH_URL = "http://localhost:8080/search?q={query}&format=json&categories=general&engines=google,bing"


def load[SettingsT: BaseSettings](settings_cls: type[SettingsT]) -> SettingsT:
    """Build a settings object from the environment / .env file.

    Type checkers see every settings field as a required constructor argument
    even though the values come from the environment, so the no-argument
    construction is centralised here rather than ignored at each call site.
    """
    return settings_cls()  # pyright: ignore[reportCallIssue]


def discover_file(directory: Path, suffix: str, preferred: Path) -> str:
    """Pick a file so it doesn't have to be spelled out in .env.

    Uses ``preferred`` when it exists, otherwise the only file in ``directory``
    with that suffix. Returns an empty string when the choice is ambiguous or
    there is nothing to find, leaving the field for .env to supply.
    """
    if preferred.is_file():
        return preferred.as_posix()
    if not directory.is_dir():
        return ""
    candidates = sorted(path for path in directory.glob(f"*{suffix}") if path.is_file())
    if len(candidates) == 1:
        return candidates[0].as_posix()
    return ""


def _read_text_fields(data: Any, fields: dict[str, str]) -> Any:
    """Replace path-valued fields with the contents of the files they point at.

    ``fields`` maps a field name to the path used when the environment does not
    set one; an empty default means the field is required from .env.
    """
    if not isinstance(data, dict):
        return data
    values = dict(cast(dict[str, Any], data))
    for field, default_path in fields.items():
        path = values.get(field) or default_path
        if not isinstance(path, str) or not path:
            continue
        try:
            values[field] = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"could not read {field} from {path!r}: {exc}") from exc
    return values


# ============== Login Settings ==============
class LoginSettings(BaseSettings):
    email: str
    password: SecretStr

    model_config = SettingsConfigDict(env_prefix="LOGIN_", env_file=".env", extra="ignore")


# ============== Gemini API ==============
class GeminiApi(BaseSettings):
    key: SecretStr
    model: str = "gemini-3.6-flash"
    search_url: str = DEFAULT_SEARCH_URL
    # The three fields below are set to file paths and replaced by their contents.
    prompt: str = ""
    resume_text: str = ""
    email_template: str = ""

    @model_validator(mode="before")
    @classmethod
    def load_files(cls, data: Any) -> Any:
        return _read_text_fields(
            data,
            {
                "prompt": DEFAULT_PROMPT_PATH.as_posix(),
                "resume_text": discover_file(ATTACHMENTS_DIR, ".txt", DEFAULT_RESUME_TEXT_PATH),
                "email_template": DEFAULT_EMAIL_TEMPLATE_PATH.as_posix(),
            },
        )

    model_config = SettingsConfigDict(env_prefix="GEMINI_API_", env_file=".env", extra="ignore")


# ============== Email Paths ==============
class EmailPathsSettings(BaseSettings):
    """Recipient lists are discovered under ``assets/``; only the blacklist is configurable."""

    blacklist_path: str = DEFAULT_BLACKLIST_PATH.as_posix()

    model_config = SettingsConfigDict(env_prefix="EMAIL_PATHS_", env_file=".env", extra="ignore")


# ============== Sender ==============
class SenderSettings(BaseSettings):
    name: str
    email: str

    model_config = SettingsConfigDict(env_prefix="EMAIL_BASE_SENDER_", env_file=".env", extra="ignore")


# ============== Email Settings ==============
class EmailModel(BaseSettings):
    subject: str = "Developer Position - Job Application"
    email_sender: SenderSettings = Field(default_factory=lambda: load(SenderSettings))
    attachment_path: str = Field(
        default_factory=lambda: discover_file(ATTACHMENTS_DIR, ".pdf", ATTACHMENTS_DIR / "resume.pdf")
    )
    template: str = DEFAULT_EMAIL_TEMPLATE_PATH.as_posix()
    # Set to a file path and replaced by its contents.
    default_body: str = ""

    @model_validator(mode="before")
    @classmethod
    def load_files(cls, data: Any) -> Any:
        return _read_text_fields(data, {"default_body": DEFAULT_BODY_PATH.as_posix()})

    model_config = SettingsConfigDict(env_prefix="EMAIL_BASE_", env_file=".env", extra="ignore")
