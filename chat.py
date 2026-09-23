import random
import socket
import threading

PORT_RANGE = range(50000, 50005)
BUFFER_SIZE = 4096
CLIENT_ID = hex(random.randint(0x1000, 0xFFFF))[2:]


def listen_messages(sock: socket.socket) -> None:
    seen_messages = set()

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8", errors="replace")

            # Формат пакета: CLIENT_ID:MSG_ID:NICK:TEXT
            parts = message.split(":", 3)
            if len(parts) == 4:
                sender_id, msg_id, nick, text = parts
                
                # Игнорируем свои сообщения и дубликаты
                if sender_id == CLIENT_ID or msg_id in seen_messages:
                    continue

                seen_messages.add(msg_id)
                # Ограничиваем размер кэша
                if len(seen_messages) > 1000:
                    seen_messages.clear()

                print(f"\r\033[K[{nick}]: {text}\n> ", end="")
            else:
                print(f"\r\033[K[Raw @ {addr[0]}]: {message}\n> ", end="")
        
        except ConnectionResetError:
            # Костыль для Windows: игнорируем ICMP-ответы от закрытых портов
            continue
        except OSError:
            # Срабатывает при штатном закрытии сокета
            break


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    current_port = None
    for port in PORT_RANGE:
        try:
            sock.bind(("", port))
            current_port = port
            break
        except OSError:
            continue

    if current_port is None:
        print("Ошибка: все порты диапазона заняты.")
        sock.close()
        return

    nickname = input("Введи никнейм: ").strip() or f"User_{CLIENT_ID}"
    
    # НОВОЕ: Спрашиваем IP соседа
    print("\nУзнай IP соседа через команду ipconfig (строка IPv4-адрес)")
    target_ip = input("Введи IP соседа (или нажми Enter для всех): ").strip() or "<broadcast>"
    
    print(f"\n--- Чат запущен на порту {current_port} ---")
    print(f"--- Шлем пакеты на: {target_ip} ---")

    listener = threading.Thread(target=listen_messages, args=(sock,), daemon=True)
    listener.start()

    try:
        while True:
            text = input("> ").strip()
            if not text:
                continue
            if text == "/exit":
                break

            msg_id = str(random.randint(100000, 999999))
            payload = f"{CLIENT_ID}:{msg_id}:{nickname}:{text}".encode("utf-8")

            # Бьем точечно по IP соседа и на всякий случай на локалхост
            for port in PORT_RANGE:
                for ip in (target_ip, "127.0.0.1"):
                    try:
                        sock.sendto(payload, (ip, port))
                    except OSError:
                        pass
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        sock.close()



if __name__ == "__main__":
    main()
