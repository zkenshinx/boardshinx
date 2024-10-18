import base64
import socket
import json
from collections import namedtuple
import threading
import signal
import sys

MESSAGE_END = b'json_end_zk3nsh1nx'
SERVER_IP = 'localhost'
SERVER_UDP_PORT = 23456
from random import randint
SERVER_TCP_PORT = randint(25000, 28000)
f = open('port', 'w') 
f.write(str(SERVER_TCP_PORT))
f.flush()
UDP_BUFFER_SIZE = 1024
TCP_BUFFER_SIZE = 4096 * 4

Client = namedtuple('Client', ['name', 'addr', 'socket'])

game_objects = {}

# UDP logic
clients_udp = set()

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((SERVER_IP, SERVER_UDP_PORT))

print(f"UDP server listening on {SERVER_IP}:{SERVER_UDP_PORT}")

def broadcast_update_udp(message, sender_addr):
    message = json.dumps(message).encode('utf-8')
    for client in clients_udp:
        if client.addr != sender_addr:
            udp_sock.sendto(message, client.addr)

def handle_udp():
    while True:
        try:
            data, addr = udp_sock.recvfrom(UDP_BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))

            if message['action'] == 'join':
                name = message['name']
                c = Client(message['name'], addr, None)
                if c not in clients_udp:
                    clients_udp.add(c)
                    print(f"New client {c} connected")
                continue

            broadcast_update_udp(message, addr)
        except Exception as e:
            print(f"UDP error: {e}")

udp_thread = threading.Thread(target=handle_udp)
udp_thread.start()

# TCP logic
clients_tcp = []

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.bind((SERVER_IP, SERVER_TCP_PORT))
tcp_sock.listen(5)

print(f"TCP server listening on {SERVER_IP}:{SERVER_TCP_PORT}")

def broadcast_update_tcp(message, sender_addr):
    message = json.dumps(message).encode('utf-8')
    for client in clients_tcp:
        if client.addr != sender_addr and client.socket:
            try:
                client.socket.send(message)
                client.socket.send(MESSAGE_END)
                print(f"Send message tcp: {message}")
            except Exception as e:
                print(f"Failed to send TCP message to {client.name}: {e}")

def send_file_to_client(client_socket):
    result = {
        "action": "join"
    }
    try:
        with open('from_server.zip', 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        result["game_state"] = encoded
        message = json.dumps(result).encode('utf-8')
        client_socket.send(message)
        client_socket.send(MESSAGE_END)
        print("Zip send to client")
    except Exception as e:
        print(f"Failed to send file: {e}")

def handle_tcp_client(client_socket, addr):
    tcp_data = bytearray()
    try:
        while True:
            data = client_socket.recv(TCP_BUFFER_SIZE)
            if not data:
                break
            tcp_data.extend(data)
            while True:
                pos = tcp_data.find(MESSAGE_END)
                if pos == -1:
                    break

                before_message = tcp_data[:pos].decode('utf-8')
                tcp_data = tcp_data[pos + len(MESSAGE_END):]
                message = json.loads(before_message)
                if message['action'] == 'join':
                    c = Client(message['name'], addr, client_socket)
                    clients_tcp.append(c)
                    send_file_to_client(client_socket)
                    continue
                broadcast_update_tcp(message, addr)
        # TODO: race condition
        for i in range(len(clients_tcp)):
            if clients_tcp[i].addr == addr:
                del clients_tcp[i]
    except json.JSONDecodeError:
        print("Received malformed JSON message.")
    except Exception as e:
        print(f"TCP client error: {e}")
    finally:
        client_socket.close()

def handle_tcp():
    while True:
        client_socket, addr = tcp_sock.accept()
        threading.Thread(target=handle_tcp_client, args=(client_socket, addr)).start()

# Run both UDP and TCP handlers in parallel
tcp_thread = threading.Thread(target=handle_tcp)
tcp_thread.start()

def signal_handler(sig, frame):
    print("\nShutting down server...")
    threading.Event.set()
    udp_sock.close()
    tcp_sock.close()
    exit()

signal.signal(signal.SIGINT, signal_handler)
udp_thread.join()
tcp_thread.join()
