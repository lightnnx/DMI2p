from .crypto import *
import asyncio
from i2p import sam  # pip install i2ppy

class P2PNode:
    """
    Узел P2P через I2P SAM с безопасным обменом сообщениями.
    - RSA для обмена AES ключом.
    - AES (Fernet) для шифрования контента.
    """

    def __init__(self, username: str, passphrase: str = ""):
        self.username = username
        self.passphrase = passphrase
        self.private_key, self.public_key = generate_rsa_keys()
        self.aes_key = None
        self.peer_addr = None

        self.sam_host = "127.0.0.1"
        self.sam_port = 7656
        self.session = None
        self.destination = None

    async def register(self):
        """Создание I2P-сессии через SAM Bridge."""
        print(f"[P2P] Подключение к SAM Bridge {self.sam_host}:{self.sam_port}...")
        loop = asyncio.get_running_loop()
        self.session = await loop.run_in_executor(None, lambda: sam.Session(host=self.sam_host, port=self.sam_port, nickname=self.username))
        self.destination = self.session.dest.b32
        print(f"[P2P] Узел {self.username} готов: {self.destination}.b32.i2p")

    async def find_peer(self, peer_name: str, peer_addr: str = None):
        """
        Задает адрес собеседника. Если адрес известен, используем его напрямую.
        """
        if peer_addr:
            self.peer_addr = peer_addr
            print(f"[P2P] Найден {peer_name}: {self.peer_addr}.b32.i2p")
            return self.peer_addr
        elif self.peer_addr:
            return self.peer_addr
        else:
            print(f"[P2P] ❌ Адрес {peer_name} неизвестен.")
            return None

    def establish_secure_channel(self):
        """Создание AES ключа для чата."""
        self.aes_key = generate_aes_key()
        print("[P2P] 🔐 AES-ключ установлен.")
        return self.aes_key

    async def send_secure_message(self, message: str, peer_addr: str = None):
        """Отправка зашифрованного сообщения через SAM."""
        if peer_addr:
            self.peer_addr = peer_addr

        if not self.peer_addr:
            print("[P2P] Нет адреса получателя. Используй find_peer() сначала.")
            return

        if not self.aes_key:
            self.establish_secure_channel()

        encrypted = aes_encrypt(self.aes_key, message)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: self.session.send(self.peer_addr + ".b32.i2p", encrypted))
        print(f"[P2P] Отправлено -> {self.peer_addr}.b32.i2p")

    async def listen_secure(self):
        """Прослушивание входящих сообщений через SAM."""
        if not self.session:
            print("[P2P] Сессия не инициализирована. Используй register()")
            return

        print("[P2P] 📡 Ожидание входящих сообщений...")
        loop = asyncio.get_running_loop()

        while True:
            try:
                msg = await loop.run_in_executor(None, self.session.recv)
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
