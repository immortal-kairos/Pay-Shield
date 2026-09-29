import pyotp
import secrets

class TOTPService:
    @staticmethod
    def generate_secret() -> str:
        return pyotp.random_base32()

    @staticmethod
    def generate_totp_uri(secret: str, email: str) -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="PayShield")

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        return pyotp.TOTP(secret).verify(code, valid_window=1)

    @staticmethod
    def generate_backup_codes(count: int = 8) -> list[str]:
        codes = []
        for _ in range(count):
            part1 = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(4))
            part2 = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(4))
            codes.append(f"{part1}-{part2}")
        return codes