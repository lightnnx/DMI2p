import asyncio
import contextlib
from p2p.dht import DHTManager
from p2p.node import P2PNode

async def main():
    print("🌐 DeChat I2P — глобальный P2P мессенджер")
    username = input("Введите имя пользователя: ").strip()
    passphrase = input("Введите общий пароль (passphrase): ").strip()

    # Инициализация DHT/I2P
    dht = DHTManager(username=username, passphrase=passphrase)
    await dht.start()

    # Инициализация P2P узла
    node = P2PNode(username=username, dht=dht, passphrase=passphrase)
    await node.register()

    print("\n📡 Поиск активных пользователей...")
    await asyncio.sleep(2)

    try:
        while True:
            users = dht.get_known_users()
            print(f"\n👥 Активных пользователей: {len(users)}")
            for u in users:
                print(f" - {u}")

            print("\n1️⃣ — Обновить список")
            print("2️⃣ — Написать пользователю")
            print("3️⃣ — Выход")

            choice = input("Выбор: ").strip()

            if choice == "1":
                continue
            elif choice == "2":
                target = input("Введите имя получателя: ").strip()
                if target not in users:
                    print("⚠️ Пользователь не найден в сети.")
                    continue
                message = input("Введите сообщение: ")
                await node.find_peer(target)
                await node.send_secure_message(message)
            elif choice == "3":
                break

            # Обновление каждые 5 секунд
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\n⏹ Завершение работы...")

    await dht.stop()

if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
