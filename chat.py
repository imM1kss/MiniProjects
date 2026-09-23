import random
import socket
import threading

PORT_RANGE = range(50000, 50005)
BUFFER_SIZE = 4096
CLIENT_ID = hex(random.randint(0x1000, 0xFFFF))[2:]

def get_local_prefix() -> str:
    # Хак для быстрого определения своего IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    
    # Отрезаем последнее число: '10.10.22.222' -> '10.10.22.'
    return ip.rsplit('.', 1)[0] + '.'


def listen_messages(sock: socket.socket) -> None:
    seen_messages = set()

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8", errors="replace")

            parts = message.split(":", 3)
            if len(parts) == 4:
                sender_id, msg_id, nick, text = parts
                
                # Игнорим свои же сообщения и дубли
                if sender_id == CLIENT_ID or msg_id in seen_messages:
                    continue

                seen_messages.add(msg_id)
                if len(seen_messages) > 1000:
                    seen_messages.clear()

                print(f"\r\033[K[{nick}]: {text}\n> ", end="")
            else:
                print(f"\r\033[K[Raw @ {addr[0]}]: {message}\n> ", end="")
        
        except ConnectionResetError:
            # Костыль для Windows: игнорим недоступные IP
            continue
        except OSError:
            break


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
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

    # Автоматически получаем диапазон подсети (например, 10.10.22.)
    prefix = get_local_prefix()
    
    nickname = input("Введи никнейм: ").strip() or f"User_{CLIENT_ID}"
    
    print(f"--- Чат запущен на порту {current_port} (ID: {CLIENT_ID}) ---")
    print(f"--- Режим: Ковровая рассылка по подсети {prefix}* ---")
    print("Напиши сообщение и нажми Enter. Для выхода: /exit\n")

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

            # Спамим точечно на каждый из 254 адресов локалки
            for port in PORT_RANGE:
                for i in range(1, 255):
                    target_ip = f"{prefix}{i}"
                    try:
                        sock.sendto(payload, (target_ip, port))
                    except OSError:
                        pass
                
                # И на локалхост
                try:
                    sock.sendto(payload, ("127.0.0.1", port))
                except OSError:
                    pass
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        sock.close()
        print("\nЧат закрыт.")


if __name__ == "__main__":
    main()
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
