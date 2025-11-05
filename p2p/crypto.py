from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet

def generate_rsa_keys():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key()
    return private, public

def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def load_public_key(pem_data):
    return serialization.load_pem_public_key(pem_data)

def rsa_encrypt(public_key, message: bytes):
    return public_key.encrypt(
        message,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

def rsa_decrypt(private_key, ciphertext: bytes):
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

def generate_aes_key():
    return Fernet.generate_key()

def get_fernet(aes_key):
    return Fernet(aes_key)

def aes_encrypt(aes_key, text: str):
    return get_fernet(aes_key).encrypt(text.encode())

def aes_decrypt(aes_key, token: bytes):
    return get_fernet(aes_key).decrypt(token).decode()
