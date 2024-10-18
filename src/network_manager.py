import base64
import zipfile
import io
import socket
import json
from uuid import uuid4

from src.state_manager import GameStateManager

MESSAGE_END = b'json_end_zk3nsh1nx'

class NetworkManager:

    def move_object_send(self, obj):
        if not self.networking_status:
            return
        message = {
            "action": "move_object",
            "object_id": obj._id,
            "x": obj.world_rect.x,
            "y": obj.world_rect.y
        }
        self.send_to_server(message)

    def move_object_received(self, message):
        x = message["x"]
        y = message["y"]
        self.game.transform_manager.move_sprite_to(self.game.mp[message["object_id"]], x, y)

    def flip_image_send(self, image):
        if not self.networking_status:
            return
        message = {
            "action": "flip_image",
            "image_id": image._id,
            "is_front": image.is_front
        }
        self.send_to_server(message, "tcp")

    def flip_image_received(self, message):
        image = self.game.mp[message["image_id"]]
        image.assign_front(message["is_front"])
        for holder in self.game.GIP.get_holders():
            if image in holder.deck:
                holder.create_display()

    def add_image_to_holder_send(self, holder, image):
        if not self.networking_status:
            return
        print(self.networking_status)
        message = {
            "action": "add_image_to_holder",
            "image_id": image._id,
            "holder_id": holder._id
        }
        self.send_to_server(message, "tcp")

    def add_image_to_holder_received(self, message):
        holder = self.game.mp[message["holder_id"]]
        image = self.game.mp[message["image_id"]]
        holder.add_image(image, False)

    def remove_image_from_holder_send(self, holder, image):
        if not self.networking_status:
            return
        message = {
            "action": "remove_image_from_holder",
            "image_id": image._id,
            "holder_id": holder._id
        }
        self.send_to_server(message, "tcp")

    def remove_image_from_holder_received(self, message):
        holder = self.game.mp[message["holder_id"]]
        holder.pop_image(self.game.mp[message["image_id"]], False)

    def add_image_to_hand_send(self, image):
        if not self.networking_status:
            return
        message = {
            "action": "add_image_to_hand",
            "image_id": image._id
        }
        self.send_to_server(message)

    def add_image_to_hand_received(self, message):
        image = self.game.mp[message["image_id"]]
        image.render = False

    def remove_image_from_hand_send(self, image):
        if not self.networking_status:
            return
        message = {
            "action": "remove_image_front_hand",
            "image_id": image._id
        }
        self.send_to_server(message)

    def remove_image_from_hand_received(self, message):
        image = self.game.mp[message["image_id"]]
        image.assign_front(False)
        image.render = True

    def shuffle_holder_send(self, holder):
        if not self.networking_status:
            return
        message = {
            "action": "shuffle_holder",
            "holder_id": holder._id,
            "deck": [f._id for f in holder.deck]
        }
        self.send_to_server(message, "tcp")

    def shuffle_holder_received(self, message):
        holder = self.game.mp[message["holder_id"]]
        holder.shuffle([self.game.mp[image_id] for image_id in message["deck"]])

    def rotate_object_send(self, obj, direction):
        if not self.networking_status:
            return
        message = {
            "action": "rotate_object",
            "object_id": obj._id,
            "direction": direction
        }
        self.send_to_server(message, "tcp")

    def rotate_object_received(self, message):
        obj = self.game.mp[message["object_id"]]
        self.game.GOM.try_rotate_obj(message["direction"], obj, False)

    def retrieve_button_clicked_send(self, button):
        if not self.networking_status:
            return
        message = {
            "action": "retrieve_button_clicked",
            "button_id": button._id
        }
        self.send_to_server(message, "tcp")

    def retrieve_button_clicked_received(self, message):
        self.game.mp[message["button_id"]].retrieve()

    def shuffle_button_clicked_send(self, button):
        if not self.networking_status:
            return
        message = {
            "action": "shuffle_button_clicked",
            "button_id": button._id
        }
        self.send_to_server(message, "tcp")

    def shuffle_button_clicked_received(self, message):
        self.game.mp[message["button_id"]].shuffle()

    def connect_to_server(self):
        message = {
            "action": "join",
            "name": str(uuid4())
        }
        self.send_to_server(message, "udp")
        self.send_to_server(message, "tcp")

    def connect_to_server_received(self, message):
        game_name = f"{str(uuid4())}.zip"
        with open(game_name, "wb") as f:
            f.write(base64.b64decode(message["game_state"]))
        GameStateManager.load_game_state(self.game, game_name)
        self.set_networking(True)

    def process_networking(self):
        for i in range(16):
            if i < 8:
                message = self.get_from_server_tcp()
            else:
                message = self.get_from_server_udp()
            if message is not None:
                self.received_mapping[message["action"]](message)
    
    def get_from_server_udp(self):
        try:
            data, _ = self.udp_sock.recvfrom(self.UDP_BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))
            return message
        except BlockingIOError:
            return None
        except json.JSONDecodeError:
            print("Received malformed UDP JSON")
            return None

    def get_from_server_tcp(self):
        try:
            data = self.tcp_sock.recv(self.TCP_BUFFER_SIZE)
            if not data:
                return None
            self.tcp_data.extend(data)
            pos = self.tcp_data.find(MESSAGE_END)
            if pos != -1:
                before_message = self.tcp_data[:pos].decode('utf-8')
                self.tcp_data = self.tcp_data[pos + len(MESSAGE_END):]
                return json.loads(before_message)
            return None
        except BlockingIOError:
            return None
        except json.JSONDecodeError:
            print("Received malformed TCP JSON")
            return None

    def send_to_server(self, data, protocol='udp'):
        message = json.dumps(data).encode('utf-8')
        if protocol == 'udp':
            self.udp_sock.sendto(message, (self.SERVER_IP, self.SERVER_UDP_PORT))
        else:
            self.tcp_sock.send(message)
            self.tcp_sock.send(MESSAGE_END)

    def init_networking(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setblocking(False)

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((self.SERVER_IP, self.SERVER_TCP_PORT))
        self.tcp_sock.setblocking(False)

    def init_functions(self):
        self.received_mapping = {
            "flip_image": self.flip_image_received,
            "move_object": self.move_object_received,
            "add_image_to_holder": self.add_image_to_holder_received,
            "remove_image_from_holder": self.remove_image_from_holder_received,
            "add_image_to_hand": self.add_image_to_hand_received,
            "remove_image_from_hand": self.remove_image_from_hand_received,
            "shuffle_holder": self.shuffle_holder_received,
            "rotate_object": self.rotate_object_received,
            "retrieve_button_clicked": self.retrieve_button_clicked_received,
            "shuffle_button_clicked": self.shuffle_button_clicked_received,
            "join": self.connect_to_server_received
        }

    def set_networking(self, status):
        self.networking_status = status

    def start_networking():
        self.init_functions()
        self.init_networking()
        self.connect_to_server()

    def __init__(self, game, ip):
        self.networking_status = False
        self.game = game
        self.tcp_data = bytearray()
        self.SERVER_IP = ip
        self.SERVER_UDP_PORT = 23456
        with open('server/port', 'r') as f:
            self.SERVER_TCP_PORT = int(f.read())
        self.UDP_BUFFER_SIZE = 1024
        self.TCP_BUFFER_SIZE = 4096 * 4

