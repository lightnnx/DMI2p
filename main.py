import asyncio
import json
import contextlib
from p2p.dht import DHTManager
from chat.session import ChatSession

async def main():
    print("🔐 DeChat I2P Prototype — Secure P2P Messenger")
    username = input("Введите имя пользователя: ").strip()
    passphrase = input("Введите общий пароль (passphrase): ").strip()

    dht = DHTManager(username=username, passphrase=passphrase)
    await dht.start()

    print("\n📡 Поиск активных пользователей...")
    await asyncio.sleep(2)

    while True:
        users = dht.get_known_users()
        print(f"\n👥 Активных пользователей: {len(users)}")
        for u in users:
            print(f" - {u}")

        print("\n1️⃣ — Обновить список   2️⃣ — Написать пользователю   3️⃣ — Выход")
        choice = input("Выбор: ").strip()

        if choice == "1":
            continue
        elif choice == "2":
            target = input("Введите имя получателя: ").strip()
            if target not in users:
                print("⚠️ Пользователь не найден в сети.")
                continue
            message = input("Введите сообщение: ")
            session = ChatSession(username, target, dht)
            await session.send_message(message)
        elif choice == "3":
            break

    print("⏹ Завершение работы...")
    await dht.stop()

if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
