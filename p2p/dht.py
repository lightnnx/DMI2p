import asyncio
import json
import socket
import hashlib
import base64
import time
from cryptography.fernet import Fernet

class DHTManager:
    def __init__(self, username: str, passphrase: str = ""):
        self.username = username
        self.passphrase = passphrase
        self.running = False
        self.known_users = {}
        self.broadcast_port = 50505
        self.loop = asyncio.get_event_loop()

        key = hashlib.sha256(passphrase.encode() or b"default").digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key[:32]))

    async def start(self):
        self.running = True
        asyncio.create_task(self._broadcast_loop())
        asyncio.create_task(self._listen_loop())

    async def stop(self):
        self.running = False

    async def _broadcast_loop(self):
        """Периодически рассылает зашифрованные объявления о себе."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = json.dumps({
            "username": self.username,
            "timestamp": time.time(),
        }).encode()

        while self.running:
            try:
                encrypted = self.fernet.encrypt(msg)
                sock.sendto(encrypted, ("255.255.255.255", self.broadcast_port))
            except Exception:
                pass
            await asyncio.sleep(5)

    async def _listen_loop(self):
        """Принимает зашифрованные пакеты и обновляет список пользователей."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.broadcast_port))
        sock.setblocking(False)

        while self.running:
            await asyncio.sleep(0.1)
            try:
                data, addr = sock.recvfrom(4096)
                info = json.loads(self.fernet.decrypt(data).decode())
                user = info.get("username")
                if user and user != self.username:
                    self.known_users[user] = time.time()
            except Exception:
                pass

            # Очистка неактивных пользователей
            now = time.time()
            self.known_users = {u: t for u, t in self.known_users.items() if now - t < 15}

    def get_known_users(self):
        """Возвращает список известных активных пользователей."""
        return list(self.known_users.keys())

