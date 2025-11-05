from .crypto import *
import asyncio

class P2PNode:
    def __init__(self, username: str, dht):
        self.username = username
        self.dht = dht
        self.private_key, self.public_key = generate_rsa_keys()
        self.aes_key = None
        self.peer_addr = None

    async def register(self):
        await self.dht.start()

    async def find_peer(self, peer_name: str):
        addr = await self.dht.find_user(peer_name)
        if not addr:
            print(f"[P2P] Пользователь {peer_name} не найден в DHT.")
            return None
        self.peer_addr = addr
        return addr

    def establish_secure_channel(self):
        self.aes_key = generate_aes_key()
        print("[P2P] AES-ключ установлен.")
        return self.aes_key

    def encrypt(self, msg: str):
        return aes_encrypt(self.aes_key, msg)

    def decrypt(self, data: bytes):
        return aes_decrypt(self.aes_key, data)
