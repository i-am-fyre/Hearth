from cryptography.fernet import Fernet

def generate_encryption_key() -> str:
    """Generate a new Fernet key. Returns string for database storage."""
    return Fernet.generate_key().decode('utf-8')

def encrypt_data(data: bytes, key: str) -> bytes:
    """Encrypt binary data using a string key."""
    f = Fernet(key.encode('utf-8'))
    return f.encrypt(data)

def decrypt_data(encrypted_data: bytes, key: str) -> bytes:
    """Decrypt binary data using a string key."""
    f = Fernet(key.encode('utf-8'))
    return f.decrypt(encrypted_data)
