import asyncio

class ChatSession:
    def __init__(self, node):
        self.node = node
        self.running = True

    async def start_chat(self, peer_name: str):
        peer = await self.node.find_peer(peer_name)
        if not peer:
            return

        self.node.establish_secure_channel()
        print(f"[Chat] Чат с {peer_name} запущен. Пишите сообщения!")

        loop = asyncio.get_event_loop()
        loop.create_task(self.listen(peer))

        while self.running:
            msg = input(f"{self.node.username} > ")
            if msg.lower() in ("exit", "quit"):
                self.running = False
                break
            enc = self.node.encrypt(msg)
            await self.send(enc, peer)

    async def send(self, data: bytes, addr):
        transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=addr
        )
        transport.sendto(data)
        transport.close()

    async def listen(self, peer_addr):
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.Receiver(self.node),
            local_addr=("0.0.0.0", 0)
        )
        while self.running:
            await asyncio.sleep(1)

    class Receiver(asyncio.DatagramProtocol):
        def __init__(self, node):
            self.node = node

        def datagram_received(self, data, addr):
            try:
                msg = self.node.decrypt(data)
                print(f"\n[{addr}] {msg}")
            except Exception:
                pass
