import os
from cryptography.fernet import Fernet

def verify_env():
    """Called on app startup to enforce the security rule: fail loudly if missing."""
    if not os.environ.get("FERNET_KEY"):
        raise RuntimeError("FERNET_KEY environment variable is missing.")

def _get_cipher() -> Fernet:
    key = os.environ.get("FERNET_KEY")
    if not key:
        raise RuntimeError("FERNET_KEY environment variable is missing.")
    return Fernet(key.encode())

def encrypt(plain_text: str) -> str:
    """Returns base64 ciphertext string. Never log the plain_text."""
    return _get_cipher().encrypt(plain_text.encode()).decode()

def decrypt(cipher_text: str) -> str:
    """Returns original plain text from the ciphertext."""
    return _get_cipher().decrypt(cipher_text.encode()).decode()
    