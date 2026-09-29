from pydantic import BaseModel, Field

class TOTPVerify(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)

class TOTPBackup(BaseModel):
    backup_code: str = Field(..., min_length=9, max_length=9)