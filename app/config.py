from pydantic import model_validator
from pydantic.types import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============== Login Settings ==============
class LoginSettings(BaseSettings):
    email: str
    password: SecretStr

    class Config(SettingsConfigDict):
        env_prefix = "LOGIN_"
        env_file = ".env"
        extra = "ignore"


class GeminiApi(BaseSettings):
    key: SecretStr
    prompt: str = """
Generate a brief and professional email body that can be used for job applications across various companies. The response should showcase my skills, experience, and background in a general manner that could apply to multiple potential employers. Include mentions of common industry trends, versatile professional skills, and how I can contribute value to any team. Use general industry keywords and technologies that are widely applicable.

Rules:
- ONLY GENERATE THE BODY SECTION OF THE EMAIL.
- DO NOT ADD ANY PLACEHOLDERS OR ADDITIONAL TEXT. THE RESPONSE SHOULD BE A COMPLETE EMAIL BODY.
- DO NOT ASK ME TO PROVIDE ANY ADDITIONAL INFORMATION.
- DO NOT ASK ME TO MENTION ANY SPECIFIC COMPANY NAME OR PROJECT.
- KEEP IT AT MOST 2 PARAGRAPHS LONG. EACH PARAGRAPH SHOULD BE NO MORE THAN 3 LINES.


Here is the additional context for the email:
- Company Name: {company_name}
- My Resume: {resume_text}
- Email Template: {email_template}
When responding, use the provided resume information to create a general, adaptable email body that could be sent to various companies.
"""
    resume_text: str
    email_template: str

    @model_validator(mode="before")
    def validate_model(cls, v):
        return {
            "key": v["key"],
            "resume_text": open(v["resume_text"]).read(),
            "email_template": open(v["email_template"]).read(),
        }

    class Config(SettingsConfigDict):
        env_prefix = "GEMINI_API_"
        env_file = ".env"
        extra = "ignore"


# ============== Email Paths ==============
class EmailPathsSettings(BaseSettings):
    test_path: str | None = None
    startups_path: str
    full_path: str

    class Config(SettingsConfigDict):
        env_prefix = "EMAIL_PATHS_"
        env_file = ".env"
        extra = "ignore"


# ============== Email Settings ==============
class EmailModel(BaseSettings):
    class SenderModel(BaseSettings):
        name: str
        email: str

        class Config(SettingsConfigDict):
            env_prefix = "EMAIL_BASE_SENDER_"
            env_file = ".env"
            extra = "ignore"

    subject: str
    email_sender: SenderModel
    attachment_path: str
    template: str

    @model_validator(mode="before")
    def validate_model(cls, v):
        sender = cls.SenderModel(**v)
        return {
            "subject": v["subject"],
            "email_sender": sender,
            "attachment_path": v["attachment_path"],
            "template": v["template"],
        }

    class Config(SettingsConfigDict):
        env_prefix = "EMAIL_BASE_"
        env_file = ".env"
        extra = "ignore"
