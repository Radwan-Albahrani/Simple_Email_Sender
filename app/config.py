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
Write a brief, genuine email body for a job application that reflects my personal experiences and interests.
Use specific details from my resume to highlight one or two key achievements or skills that set me apart.
If Additional Info is provided, mention a current trend or challenge in the industry that genuinely excites or interests me, based on that information.
If no Additional Info is given, omit this part. Keep the tone friendly but professional and conversational, as if I'm talking to a potential employer.

Example:
I am writing to apply for a part-time developer position at your organization.

As a full stack engineer with experience in FastAPI, Django, Flutter, and React, I am confident in my ability to contribute effectively to your team. I quickly adapt to new technologies, ensuring I can meet the dynamic needs of your projects.

Rules:
- Do not start the email with "I am excited to apply for..." or similar phrases.
- Start with "I am writing to apply for..." or similar. This keeps the tone professional.
- Avoid overly formal language or buzzwords that might sound artificial.
- Write only the email body, no greetings or closings.
- Use concrete details from my resume. Avoid vague or generic statements.
- If Additional Info is provided, naturally weave in a reference to the company's work.
- Don't include any placeholders, brackets, or requests for information insertion.
- If any part of the response can't be completed without a placeholder, omit that part entirely.
- Don't mention specific companies unless given in Additional Info.
- Write 2 short paragraphs, 1-2 sentences each, separated by a blank line.
- Be concise and authentic. Aim for a natural, conversational tone while staying professional.

Context (use if provided):
- Company Name: {company_name}
- Additional Info: {extra_info}
- My Resume: {resume_text}
- Email Template: {email_template}

Create an email body that sounds like it's genuinely written by me, based on my actual experiences and interests from the resume. Keep it professional but conversational,
and avoid sounding overly formal or artificial.
"""
    resume_text: str
    email_template: str
    search_url: str

    @model_validator(mode="before")
    def validate_model(cls, v):
        return {
            "key": v["key"],
            "search_url": v["search_url"],
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
    default_body: str = """My name is Radwan Albahrani, currently Studying at Imam Abdulrahman Bin Faisal University, Majoring in Artificial Intelligence.

I am writing to apply for a developer position at your organization.

As a full stack engineer with experience in App and Web development, as well as proficiency in backend implementation, I am confident in my ability to contribute effectively to your team. I quickly adapt to new technologies, ensuring I can meet the dynamic needs of your projects.
"""

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
