import asyncio
import base64
import json
import time
import hashlib
from i2plib import Tunnel, SAMSession, get_sam_socket
from cryptography.fernet import Fernet


class DHTManager:
    def __init__(self, username, discovery_passphrase=None, port=55555):
        self.username = username
        self.discovery_passphrase = discovery_passphrase
        self.session = None
        self.tunnel = None
        self.users = {}
        self.running = False

    async def start(self):
        print("[I2P] Запуск SAM-сессии...")
        self.session = SAMSession(nickname=self.username, destination=None)
        self.tunnel = Tunnel(self.session)
        await self.tunnel.start()

        print(f"[I2P] Ваш скрытый адрес: {self.session.dest.base32}.b32.i2p")
        self.running = True
        asyncio.create_task(self.broadcast_presence())
        asyncio.create_task(self.listen_loop())

    async def broadcast_presence(self):
        """Отправка своего адреса в I2P DHT."""
        while self.running:
            payload = {
                "user": self.username,
                "addr": self.session.dest.base32,
                "timestamp": time.time()
            }
            data = json.dumps(payload).encode()
            if self.discovery_passphrase:
                fernet = Fernet(self._derive_key())
                data = fernet.encrypt(data)

            # Публикация в I2P DHT (через локальный SAM API)
            try:
                sock = get_sam_socket()
                msg = b"namestore.set key=" + self.username.encode() + b" value=" + data + b"\n"
                sock.send(msg)
                sock.close()
            except Exception as e:
                print("[!] Ошибка публикации:", e)

            await asyncio.sleep(15)

    async def listen_loop(self):
        """Периодически опрашивает I2P DHT о других пользователях."""
        while self.running:
            try:
                sock = get_sam_socket()
                sock.send(b"namestore.list\n")
                resp = sock.recv(8192)
                sock.close()

                for line in resp.splitlines():
                    if not line.startswith(b"value="):
                        continue
                    try:
                        raw = line.split(b"value=")[1]
                        if self.discovery_passphrase:
                            raw = Fernet(self._derive_key()).decrypt(raw)
                        payload = json.loads(raw.decode())
                        user = payload["user"]
                        addr = payload["addr"]
                        if user != self.username:
                            self.users[user] = (addr, payload["timestamp"])
                    except Exception:
                        pass
            except Exception as e:
                print("[!] Ошибка опроса DHT:", e)

            await asyncio.sleep(20)

    async def find_user(self, name):
        return self.users.get(name, (None, None))[0]

    def _derive_key(self):
        """Создаёт 32-байтный AES ключ из passphrase."""
        key = hashlib.sha256(self.discovery_passphrase.encode()).digest()
        return base64.urlsafe_b64encode(key)

    async def close(self):
        self.running = False
        if self.tunnel:
            await self.tunnel.stop()
        if self.session:
            await self.session.close()

