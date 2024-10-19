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
class UDPServer:
    def __init__(self, ip, port, buffer_size=1024):
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.clients = set()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        print(f"UDP server listening on {self.ip}:{self.port}")

    def broadcast(self, message, sender_addr):
        message = json.dumps(message).encode('utf-8')
        for client in self.clients:
            if client.addr != sender_addr:
                self.sock.sendto(message, client.addr)

    def action(self, addr, message):
        if message['action'] == 'join':
            c = Client(message['name'], addr, None)
            if c not in self.clients:
                self.clients.add(c)
                print(f"New client {c} connected udp")
                return
        self.broadcast(message, addr)

    def handle(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
                message = json.loads(data.decode('utf-8'))
                self.action(addr, message)
            except Exception as e:
                print(f"UDP error: {e}")

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = []

    def add_player(self, player_name):
        if player_name in self.players:
            return False
        self.players.append(player_name)
        return True

class RoomManager:
    def __init__(self):
        self.rooms = {}

    def create_room(self, room_id):
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id)

    def resolve_join(self, room_id, player_name):
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if room.add_player(player_name):
                return (True, {"action": "join", "result": "success"})
            return (False, {
                "action": "join",
                "result": "fail",
                "message": "Player with name already exists"
            })
        return (False, {
            "action": "join",
            "result": "fail",
            "message": "Wrong room code"
        })

room_manager = RoomManager()
room_manager.create_room("1")

# TCP logic
class TCPServer:
    def __init__(self, ip, port, buffer_size=4096 * 4):
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.clients = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port))
        self.sock.listen(5)
        print(f"TCP server listening on {self.ip}:{self.port}")

    def send(self, socket, message):
        socket.send(message)
        socket.send(MESSAGE_END)

    def broadcast(self, message, sender_addr):
        message = json.dumps(message).encode('utf-8')
        for client in self.clients:
            if client.addr != sender_addr and client.socket:
                try:
                    self.send(client.socket, message)
                    print(f"Send message tcp: {message}")
                except Exception as e:
                    print(f"Failed to send TCP message to {client.name}: {e}")

    def send_file(self, client_socket):
        result = {"action": "get_game_state"}
        try:
            with open('from_server.zip', 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            result["game_state"] = encoded
            message = json.dumps(result).encode('utf-8')
            self.send(client_socket, message)
            print("Zip send to client")
        except Exception as e:
            print(f"Failed to send file: {e}")

    def action(self, client_socket, addr, message):
        if message['action'] == 'join':
            room = message["room"]
            name = message["name"]
            joined, send_message = room_manager.resolve_join(room, name)
            if joined:
                c = Client(message['name'], addr, client_socket)
                self.clients.append(c)
            # Send back result
            self.send(client_socket, json.dumps(send_message).encode('utf-8'))
            return
        self.broadcast(message, addr)

    def handle_client(self, client_socket, addr):
        tcp_data = bytearray()
        try:
            while True:
                data = client_socket.recv(self.buffer_size)
                if not data:
                    break
                tcp_data.extend(data)

                while True:
                    # Extract message
                    pos = tcp_data.find(MESSAGE_END)
                    if pos == -1:
                        break
                    before_message = tcp_data[:pos].decode('utf-8')
                    tcp_data = tcp_data[pos + len(MESSAGE_END):]
                    message = json.loads(before_message)
                    # Validate
                    if "action" not in message:
                        continue
                    self.action(client_socket, addr, message)
            self.clients = [c for c in self.clients if c.addr != addr]
        except json.JSONDecodeError:
            print("Received malformed JSON message.")
        except socket.error as sock_err:
            print(f"TCP socket error: {sock_err}")
        finally:
            client_socket.close()

    def handle(self):
        while True:
            client_socket, addr = self.sock.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

# Run both UDP and TCP handlers in parallel
udp_server = UDPServer(SERVER_IP, SERVER_UDP_PORT)
udp_thread = threading.Thread(target=udp_server.handle)
udp_thread.start()

tcp_server = TCPServer(SERVER_IP, SERVER_TCP_PORT)
tcp_thread = threading.Thread(target=tcp_server.handle)
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
