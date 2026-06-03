import base64, secrets
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from shared.config import get_settings

settings = get_settings()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _fernet():
    key = settings.ENCRYPTION_KEY[:32].encode().ljust(32, b"0")
    return Fernet(base64.urlsafe_b64encode(key))

def hash_password(plain): return pwd_ctx.hash(plain)
def verify_password(plain, hashed): return pwd_ctx.verify(plain, hashed)

def create_access_token(data, expires_minutes=1440):
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try: return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError: return {}

def encrypt(text): return _fernet().encrypt(text.encode()).decode()
def decrypt(token): return _fernet().decrypt(token.encode()).decode()
def generate_api_key(): return secrets.token_urlsafe(32)
