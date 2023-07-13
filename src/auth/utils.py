import hmac

from config import SHA_KEY

def encrypt(string: str) -> bytes:
    return hmac.new(SHA_KEY, string.encode(), 'sha256').digest()