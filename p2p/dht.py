import asyncio
import time
import json
import hashlib
import base64
from cryptography.fernet import Fernet

# Попробуем импортировать I2P библиотеки
try:
    import i2plib
    from i2plib import SAMSession, Tunnel, get_sam_socket
    _I2P_AVAILABLE = True
except ImportError:
    _I2P_AVAILABLE = False

class DHTManager:
    """
    Универсальный DHT: локальный UDP broadcast fallback + I2P discovery.
    - username → адрес узла
    - passphrase шифрует объявления
    """

    def __init__(self, username: str, passphrase: str = "", port: int = 50505):
        self.username = username
        self.passphrase = passphrase
        self.users = {}  # {username: last_seen_timestamp}
        self.running = False
        self.port = port
        self.fernet = Fernet(self._derive_key())
        self.i2p_session = None
        self.tunnel = None

    def _derive_key(self):
        key = hashlib.sha256(self.passphrase.encode() or b"default").digest()
        return base64.urlsafe_b64encode(key[:32])

    async def start(self):
        self.running = True
        if _I2P_AVAILABLE:
            print("[I2P] Запуск I2P-сессии...")
            self.i2p_session = SAMSession(nickname=self.username, destination=None)
            self.tunnel = Tunnel(self.i2p_session)
            await self.tunnel.start()
            print(f"[I2P] Адрес: {self.i2p_session.dest.base32}.b32.i2p")
        asyncio.create_task(self._broadcast_loop())
        asyncio.create_task(self._listen_loop())

    async def stop(self):
        self.running = False
        if self.tunnel:
            await self.tunnel.stop()
        if self.i2p_session:
            await self.i2p_session.close()

    async def _broadcast_loop(self):
        """Рассылаем объявление о себе (UDP + I2P)."""
        while self.running:
            payload = {
                "user": self.username,
                "timestamp": time.time()
            }
            data = json.dumps(payload).encode()
            data_enc = self.fernet.encrypt(data)

            # Локальный UDP broadcast
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(data_enc, ("255.255.255.255", self.port))
                sock.close()
            except Exception:
                pass

            # I2P публикация
            if _I2P_AVAILABLE:
                try:
                    sock_i2p = get_sam_socket()
                    msg = b"namestore.set key=" + self.username.encode() + b" value=" + data_enc + b"\n"
                    sock_i2p.send(msg)
                    sock_i2p.close()
                except Exception:
                    pass

            await asyncio.sleep(10)

    async def _listen_loop(self):
        """Приём объявлений от других узлов (UDP + I2P)."""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.port))
        sock.setblocking(False)

        while self.running:
            await asyncio.sleep(0.1)

            # Локальный UDP
            try:
                data, addr = sock.recvfrom(4096)
                payload = json.loads(self.fernet.decrypt(data).decode())
                user = payload["user"]
                ts = payload["timestamp"]
                if user != self.username:
                    self.users[user] = ts
            except Exception:
                pass

            # Очистка старых пользователей
            now = time.time()
            self.users = {u: t for u, t in self.users.items() if now - t < 30}

    async def find_user(self, username: str):
        """Возвращает адрес пользователя, если он активен."""
        ts = self.users.get(username)
        if ts and (time.time() - ts) < 30:
            if _I2P_AVAILABLE:
                return await self._i2p_lookup(username)
            else:
                return "udp"
        return None

    async def _i2p_lookup(self, username):
        """Простейший lookup в I2P Namestore (можно расширить на DHT)."""
        try:
            sock = get_sam_socket()
            sock.send(b"namestore.list\n")
            resp = sock.recv(8192)
            sock.close()
            for line in resp.splitlines():
                if line.startswith(b"value=") and username.encode() in line:
                    return line.decode().split("value=")[-1]
        except Exception:
            pass
        return None

    def active_count(self):
        """Количество активных пользователей."""
        return len(self.users)

    def get_known_users(self):
        """Список активных пользователей."""
        return list(self.users.keys())

