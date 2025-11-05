from .crypto import *
from .i2p_node import I2PNode
import asyncio

class P2PNode:
    """
    Узел P2P, поддерживающий безопасный обмен сообщениями через I2P.
    - RSA используется для обмена симметрическим AES ключом.
    - AES (Fernet) используется для шифрования контента.
    """

    def __init__(self, username: str, dht=None, passphrase: str = ""):
        self.username = username
        self.dht = dht
        self.private_key, self.public_key = generate_rsa_keys()
        self.aes_key = None
        self.peer_addr = None
        self.i2p = I2PNode(username)
        self.passphrase = passphrase

    async def register(self):
        """Регистрирует узел в DHT или I2P."""
        print(f"[P2P] Регистрация узла {self.username}...")
        await self.i2p.connect()
        if self.dht:
            await self.dht.start()
        print("[P2P] Узел успешно запущен через I2P.")

    async def find_peer(self, peer_name: str):
        """Поиск собеседника по имени через DHT или I2P lookup."""
        print(f"[P2P] Поиск пользователя {peer_name}...")
        addr = None
        if self.dht:
            addr = await self.dht.find_user(peer_name)
        if not addr:
            addr = await self.i2p.lookup_user(peer_name)

        if not addr:
            print(f"[P2P] ❌ Пользователь {peer_name} не найден.")
            return None

        self.peer_addr = addr
        print(f"[P2P] ✅ Найден {peer_name}: {addr[:50]}...")
        return addr

    def establish_secure_channel(self):
        """Создание нового AES-ключа для зашифрованного чата."""
        self.aes_key = generate_aes_key()
        print("[P2P] 🔐 AES-ключ установлен.")
        return self.aes_key

    async def send_secure_message(self, message: str):
        """Отправка зашифрованного сообщения через I2P."""
        if not self.peer_addr:
            print("[P2P] Нет адреса получателя. Используй find_peer() сначала.")
            return

        if not self.aes_key:
            self.establish_secure_channel()

        encrypted = aes_encrypt(self.aes_key, message)
        await self.i2p.send_message(self.peer_addr, encrypted.decode())

    async def listen_secure(self):
        """Прослушивание входящих сообщений через I2P."""
        print("[P2P] 📡 Ожидание входящих сообщений...")
        while True:
            try:
                msg = await asyncio.to_thread(input, "")
                if self.aes_key:
                    try:
                        decrypted = aes_decrypt(self.aes_key, msg)
                        print(f"📩 Расшифровано: {decrypted}")
                    except Exception:
                        print(f"📥 Получено (недешифр.): {msg}")
            except KeyboardInterrupt:
                break

    def encrypt(self, msg: str):
        return aes_encrypt(self.aes_key, msg)

    def decrypt(self, data: bytes):
        return aes_decrypt(self.aes_key, data)
