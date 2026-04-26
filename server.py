import socket
import threading
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5555
KEY = b'0123456789abcdef0123456789abcdef'  # 32 bytes

clients = {}   # socket : username
log_file = "chat_log.txt"

# Colors
RESET = "\033[0m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"

def colored(text, color):
    return f"{color}{text}{RESET}"

def log_message(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")

def encrypt_message(message: str) -> bytes:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padding = 16 - (len(message) % 16)
    padded = message + chr(padding) * padding
    ct = encryptor.update(padded.encode()) + encryptor.finalize()
    return iv + ct

def decrypt_message(data: bytes) -> str:
    iv = data[:16]
    ct = data[16:]
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    return padded[:-padded[-1]].decode()

def broadcast(msg: str, sender=None):
    for c in list(clients.keys()):
        if sender is None or c != sender:
            try:
                c.send(encrypt_message(msg))
            except:
                pass

def handle_client(client_socket, addr):
    try:
        # Username receive with small delay to avoid race condition
        import time
        time.sleep(0.5)
        username_bytes = client_socket.recv(1024)
        username = username_bytes.decode('utf-8', errors='ignore').strip() or f"User_{addr[1]}"
        
        clients[client_socket] = username

        print(colored(f"[+] {username} joined", GREEN))
        log_message(f"{username} joined")

        broadcast(colored(f"*** {username} joined the chat ***", CYAN))

        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            try:
                msg = decrypt_message(data)
            except:
                continue

            if msg.strip().lower() == "/users":
                online = ", ".join(clients.values())
                try:
                    client_socket.send(encrypt_message(colored(f"Online: {online}", YELLOW)))
                except:
                    pass
                continue

            full_msg = f"{username}: {msg}"
            print(colored(full_msg, MAGENTA))
            log_message(full_msg)
            broadcast(full_msg, client_socket)

    except:
        pass
    finally:
        if client_socket in clients:
            uname = clients[client_socket]
            print(colored(f"[-] {uname} left", RED))
            broadcast(colored(f"*** {uname} left the chat ***", CYAN))
            del clients[client_socket]
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    print(colored(f"[*] Encrypted Chat Server started on port {PORT}", "\033[1;92m"))
    print(colored("[*] AES-256 Encryption Active", CYAN))
    print(colored("[*] /online users list", YELLOW))

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    start_server()