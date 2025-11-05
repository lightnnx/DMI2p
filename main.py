import asyncio
import contextlib
from p2p.dht import DHTManager
from chat.session import ChatSession


async def main():
    print("=== 🔒 DeChat I2P Prototype ===")
    username = input("Введите имя пользователя: ").strip()
    if not username:
        print("Имя не может быть пустым.")
        return

    passphrase = input("Discovery passphrase (оставь пустым, чтобы отключить шифрование): ").strip() or None

    # Запускаем DHT
    dht = DHTManager(username=username, port=55555, discovery_passphrase=passphrase)
    await dht.start()

    print("\n[+] Локальная P2P-сеть активна.")
    print("    - Ваше имя:", username)
    print("    - Шифрование broadcast:", "ВКЛ" if passphrase else "ВЫКЛ")
    print("    - Для выхода нажмите Ctrl+C\n")

    try:
        while True:
            print("------ Меню ------")
            print("1. Показать известных пользователей")
            print("2. Подключиться к пользователю")
            print("3. Отправить сообщение (если есть активная сессия)")
            print("4. Выход")
            choice = input("> ").strip()

            if choice == "1":
                if not dht.users:
                    print("[!] Пользователи пока не найдены.")
                else:
                    print("📡 Известные пользователи:")
                    for u, (addr, seen) in dht.users.items():
                        print(f"  - {u} @ {addr}")
                print()

            elif choice == "2":
                target = input("Введите имя пользователя для подключения: ").strip()
                addr = await dht.find_user(target)
                if not addr:
                    print("[!] Пользователь не найден.")
                    continue

                session = ChatSession(username, target, addr)
                print(f"[+] Подключение к {target} ({addr})...")
                await session.start()
                print(f"[+] Чат с {target} активен. Пишите сообщения (Ctrl+C для выхода из чата).")
                await session.interactive_loop()

            elif choice == "3":
                print("⚠️ Эта функция активируется автоматически при подключении к чату.")

            elif choice == "4":
                break

            else:
                print("Неизвестная команда.\n")

    except KeyboardInterrupt:
        print("\n[!] Завершение работы...")
    finally:
        await shutdown(dht)


async def shutdown(dht: DHTManager):
    """Закрывает все процессы корректно."""
    print("[~] Завершаю DHT...")
    with contextlib.suppress(Exception):
        await dht.close()
    print("[✓] Выход завершён.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nВыход.")
