import socket
import threading
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

HOST = '127.0.0.1'
PORT = 5555
KEY = b'0123456789abcdef0123456789abcdef'

RESET = "\033[0m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"

def colored(text, color):
    return f"{color}{text}{RESET}"

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

def receive(client_socket):
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            msg = decrypt_message(data)
            print(f"\n{msg}")
            print(colored(f"{username}> ", BLUE), end='', flush=True)
        except:
            break

username = ""

def start_client():
    global username
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    
    print(colored("[*] Connected to Encrypted Chat Server", GREEN))
    
    username = input(colored("Enter your username: ", YELLOW)).strip() or "Anonymous"
    client.send(username.encode('utf-8'))
    
    print(colored(f"[*] Welcome {username}! All messages AES-256 encrypted", "\033[1;92m"))
    print(colored("[*] Type /users to see online users", CYAN))
    
    threading.Thread(target=receive, args=(client,), daemon=True).start()
    
    while True:
        msg = input(colored(f"{username}> ", BLUE))
        if msg.lower() in ['quit', 'exit', '/quit']:
            break
        if msg.strip():
            client.send(encrypt_message(msg))

if __name__ == "__main__":
    start_client()