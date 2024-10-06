import socket
import json

# Server setup
SERVER_IP = 'localhost'
SERVER_PORT = 23456
BUFFER_SIZE = 1024

# Single room to store clients and game objects
clients = set()   # Track connected clients
game_objects = {} # Track game objects and their positions

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

print(f"UDP server listening on {SERVER_IP}:{SERVER_PORT}")

def broadcast_update(message, sender_addr):
    message = json.dumps(message).encode('utf-8')
    for client in clients:
        if client != sender_addr:  # Don't send the message back to the sender
            sock.sendto(message, client)
    print(message)

while True:
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        message = json.loads(data.decode('utf-8'))

        if addr not in clients:
            clients.add(addr)
            print(f"New client {addr} connected: {message["name"]}")

        broadcast_update(message, addr)
    except Exception as e:
        print(f"Unexpected error: {e}")
