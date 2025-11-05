import asyncio
from p2p.node import P2PNode

active_users = {}  # username -> .b32.i2p

BROADCAST_INTERVAL = 5  # сек

async def broadcast_presence(node: P2PNode):
    """Рассылка своего username + destination всем известным узлам."""
    while True:
        for user, addr in active_users.items():
            if user != node.username:
                try:
                    await node.send_secure_message(f"[presence]{node.username}|{node.destination}", peer_addr=addr)
                except Exception:
                    pass
        await asyncio.sleep(BROADCAST_INTERVAL)

async def listen_presence(node: P2PNode):
    """Прослушивание входящих сообщений и обновление active_users."""
    print("[P2P] 📡 Прослушивание сети...")
    while True:
        msg = await node.session.recv()
        try:
            decoded = msg.decode()
        except Exception:
            continue

        if decoded.startswith("[presence]"):
            payload = decoded[len("[presence]"):].strip()
            if "|" in payload:
                username, addr = payload.split("|", 1)
                if username not in active_users or active_users[username] != addr:
                    active_users[username] = addr
        await asyncio.sleep(0.1)

async def main():
    print("🌐 DeChat I2P — глобальный P2P мессенджер")

    username = input("Введите имя пользователя: ").strip()
    node = P2PNode(username=username)
    await node.register()

    # Добавляем себя в список активных
    active_users[username] = node.destination

    # Запуск прослушивания и рассылки присутствия
    asyncio.create_task(listen_presence(node))
    asyncio.create_task(broadcast_presence(node))
    asyncio.create_task(node.listen_secure())

    while True:
        print(f"\n👥 Активные пользователи ({len(active_users)}):")
        for u in active_users:
            print(f" - {u}")

        print("\n1️⃣ — Написать пользователю")
        print("2️⃣ — Обновить список")
        print("3️⃣ — Выход")

        choice = input("Выбор: ").strip()

        if choice == "1":
            target = input("Имя получателя: ").strip()
            if target not in active_users:
                print("⚠️ Пользователь не найден.")
                continue

            message = input("Введите сообщение: ")
            await node.send_secure_message(message, peer_addr=active_users[target])

        elif choice == "2":
            continue
        elif choice == "3":
            print("Выход...")
            break

        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹ Завершение работы...")
