# p2p/dht.py
import asyncio
import json
import socket
import hashlib
import base64
from cryptography.fernet import Fernet

class DHTManager:
    """
    UDP-based discovery with encrypted broadcasts.
    discovery_passphrase: str or None. If provided, announce payloads are encrypted using a symmetric key
    derived from the passphrase. Only peers with the same passphrase can decrypt and learn usernames.
    """
    def __init__(self, username: str, port: int = 55555, discovery_passphrase: str | None = None):
        self.username = username
        self.port = port
        self.users = {}  # username -> (addr, seen_time)
        self.transport = None
        self._loop = asyncio.get_event_loop()

        # prepare Fernet key from passphrase (if provided)
        if discovery_passphrase:
            h = hashlib.sha256(discovery_passphrase.encode()).digest()  # 32 bytes
            self._fernet_key = base64.urlsafe_b64encode(h)  # valid for Fernet
            self._fernet = Fernet(self._fernet_key)
        else:
            self._fernet_key = None
            self._fernet = None

    async def start(self):
        # create a UDP endpoint that will call datagram_received on this instance
        listen = self._loop.create_datagram_endpoint(
            lambda: self,
            local_addr=("0.0.0.0", self.port),
            allow_broadcast=True
        )
        self.transport, _ = await listen
        print(f"[DHT] Слушаю UDP {self.port} (encrypted discovery {'ON' if self._fernet else 'OFF'})")

        # Periodic broadcast announce
        self._announce_task = asyncio.create_task(self._periodic_announce())

    async def _periodic_announce(self):
        try:
            while True:
                await self.broadcast_announce()
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    async def broadcast_announce(self):
        """
        Build announce payload and broadcast it.
        If Fernet configured -> encrypt payload; else send plaintext JSON.
        """
        payload = {
            "type": "announce",
            "user": self.username
            # you can add extra fields like 'pubkey' here if needed (careful about size)
        }
        plain = json.dumps(payload).encode()

        if self._fernet:
            token = self._fernet.encrypt(plain)
            msg = token
        else:
            msg = plain

        # send to broadcast address
        try:
            self.transport.sendto(msg, ("255.255.255.255", self.port))
        except Exception as e:
            # sometimes on Windows binding/broadcast settings might fail; ignore for robustness
            # fallback: send to localhost
            try:
                self.transport.sendto(msg, ("127.0.0.1", self.port))
            except Exception:
                pass

    # DatagramProtocol callbacks ------------------------------------------------
    def connection_made(self, transport):
        # required by asyncio.DatagramProtocol, but we already store transport externally
        self.transport = transport

    def datagram_received(self, data: bytes, addr):
        """
        Called by asyncio when UDP packet arrives.
        Try to decrypt if _fernet is set; otherwise parse JSON.
        """
        try:
            if self._fernet:
                # try decrypt; if fails, ignore packet
                try:
                    plain = self._fernet.decrypt(data, ttl=None)
                except Exception:
                    # not decryptable with our key — ignore
                    return
            else:
                plain = data

            msg = json.loads(plain.decode())
            if msg.get("type") == "announce":
                user = msg.get("user")
                if user and user != self.username:
                    # store last-seen address and timestamp
                    self.users[user] = (addr, self._loop.time())
                    print(f"[DHT] Обнаружен {user} по адресу {addr}")
        except Exception:
            # ignore malformed packets
            return

    async def find_user(self, username: str):
        """
        Return address tuple of the username if known (from recent announces), else None.
        """
        entry = self.users.get(username)
        if not entry:
            return None
        addr, seen = entry
        # optional: expire entries older than e.g. 300s
        if self._loop.time() - seen > 300:
            del self.users[username]
            return None
        return addr

    async def close(self):
        if hasattr(self, "_announce_task"):
            self._announce_task.cancel()
            with contextlib.suppress(Exception):
                await self._announce_task
        if self.transport:
            self.transport.close()
