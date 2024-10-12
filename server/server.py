import socket
import json
from collections import namedtuple

SERVER_IP = 'localhost'
SERVER_PORT = 23456
BUFFER_SIZE = 1024

Client = namedtuple('Client', ['name', 'addr'])

clients = set()
game_objects = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

print(f"UDP server listening on {SERVER_IP}:{SERVER_PORT}")

def broadcast_update(message, sender_addr):
    message = json.dumps(message).encode('utf-8')
    for client in clients:
        if client.addr != sender_addr:
            sock.sendto(message, client.addr)
    print(message)

while True:
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        message = json.loads(data.decode('utf-8'))

        if message['action'] == 'join':
            name = message['name']
            c = Client(message['name'], addr)
            if c not in clients:
                clients.add(c)
                print(f"New client {c} connected")
            continue

        broadcast_update(message, addr)
    except Exception as e:
        print(f"Unexpected error: {e}")
