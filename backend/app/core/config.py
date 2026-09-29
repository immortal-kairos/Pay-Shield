from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    
    # Razorpay Credentials
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RAZORPAY_WEBHOOK_SECRET: str
    RAZORPAY_SOURCE_ACCOUNT: str

    # US-09 SendGrid Credentials
    SENDGRID_API_KEY: str
    ALERT_SENDER_EMAIL: str = "alerts@payshield.example.com"

    class Config:
        env_file = ".env"

settings = Settings()