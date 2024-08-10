from pydantic import BaseModel, model_validator
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


# ============== Email Paths ==============
class EmailPathsSettings(BaseSettings):
    test_path: str
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
