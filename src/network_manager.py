import random
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
        self.udp_client.send(message)

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
        self.tcp_client.send(message)

    def flip_image_received(self, message):
        image = self.game.mp[message["image_id"]]
        image.assign_front(message["is_front"])
        for holder in self.game.GIP.get_holders():
            if image in holder.deck:
                holder.create_display()

    def add_image_to_holder_send(self, holder, image):
        if not self.networking_status:
            return
        message = {
            "action": "add_image_to_holder",
            "image_id": image._id,
            "holder_id": holder._id
        }
        self.tcp_client.send(message)

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
        self.tcp_client.send(message)

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
        self.tcp_client.send(message)

    def add_image_to_hand_received(self, message):
        image = self.game.mp[message["image_id"]]
        image.render = False

    def remove_image_from_hand_send(self, image):
        if not self.networking_status:
            return
        message = {
            "action": "remove_image_from_hand",
            "image_id": image._id
        }
        self.tcp_client.send(message)

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
        self.tcp_client.send(message)

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
        self.tcp_client.send(message)

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
        self.tcp_client.send(message)

    def retrieve_button_clicked_received(self, message):
        self.game.mp[message["button_id"]].retrieve()

    def shuffle_button_clicked_send(self, button):
        if not self.networking_status:
            return
        message = {
            "action": "shuffle_button_clicked",
            "button_id": button._id
        }
        self.tcp_client.send(message)

    def shuffle_button_clicked_received(self, message):
        self.game.mp[message["button_id"]].shuffle()

    def dice_rolled_send(self, dice, dice_result):
        if not self.networking_status:
            return
        message = {
            "action": "dice_rolled",
            "dice_id": dice._id,
            "result": dice_result
        }
        self.tcp_client.send(message)

    def dice_rolled_received(self, message):
        dice = self.game.mp[message["dice_id"]]
        dice.roll(result=message["result"], send_message=False)

    def cursor_moved_send(self, x, y, name, color):
        if not self.networking_status or random.randint(1, 4) <= 1:
            return
        message = {
            "action": "cursor_moved",
            "x": x,
            "y": y,
            "name": name,
            "color": color
        }
        self.udp_client.send(message)

    def cursor_moved_received(self, message):
        x = message["x"]
        y = message["y"]
        name = message["name"]
        color = message["color"]
        self.game.cursor_moved(x, y, name, color)

    def get_game_state(self):
        message = {
            "action": "get_game_state",
            "name": str(uuid4())
        }

    def get_game_state_received(self, message):
        game_name = f"{str(uuid4())}.zip"
        with open(game_name, "wb") as f:
            f.write(base64.b64decode(message["game_state"]))
        #from random import randint
        #from time import sleep
        #sleep(randint(1, 100) * 0.01)
        GameStateManager.load_game_state(self.game, game_name)
        self.set_networking(True)

    def init_functions(self):
        fns = {
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
            "dice_rolled": self.dice_rolled_received,
            "cursor_moved": self.cursor_moved_received
        }
        for action_name, fn in fns.items():
            self.tcp_client.add_callback(action_name, fn)
            self.udp_client.add_callback(action_name, fn)

    def set_networking(self, status):
        self.networking_status = status

    def process_networking(self):
        for i in range(8):
            if i < 4:
                self.tcp_client.process()
            else:
                self.udp_client.process()

    def __init__(self, game, tcp_client, udp_client):
        self.networking_status = False
        self.game = game
        self.tcp_client = tcp_client
        self.udp_client = udp_client
        self.init_functions()

class NetworkClient:
    def __init__(self):
        self.callbacks = dict()

    def add_callback(self, action_message, callback_fn):
        self.callbacks[action_message] = callback_fn

    def validate(self, data):
        try:
            if "action" not in data:
                return None
            message = json.dumps(data).encode('utf-8')
            return message
        except (TypeError, ValueError, json.JSONDecodeError):
            print(f"Invalid data: {data}")
            return None

    def process(self):
        message = self.get()
        if message is not None and "action" in message:
            action = message["action"]
            if action in self.callbacks:
                self.callbacks[message["action"]](message)

    def send(self, data):
        pass

    def get(self):
        pass

class UDPClient(NetworkClient):

    def __init__(self, ip="localhost", port=23456):
        super().__init__()
        self.SERVER_IP = ip
        self.SERVER_UDP_PORT = port
        self.UDP_BUFFER_SIZE = 1024

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setblocking(False)

    def send(self, data):
        message = self.validate(data)
        if message is not None:
            self.udp_sock.sendto(message, (self.SERVER_IP, self.SERVER_UDP_PORT))

    def get(self):
        try:
            data, _ = self.udp_sock.recvfrom(self.UDP_BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))
            print(message)
            return message
        except BlockingIOError:
            return None
        except json.JSONDecodeError:
            print("Received malformed UDP JSON")
            return None

class TCPClient(NetworkClient):

    def __init__(self, ip="localhost", port=23457):
        super().__init__()
        self.SERVER_IP = ip
        self.SERVER_TCP_PORT = port
        with open('server/port', 'r') as f:
            self.SERVER_TCP_PORT = int(f.read())
        self.TCP_BUFFER_SIZE = 4096 * 4 * 4
        self.tcp_data = bytearray()

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((self.SERVER_IP, self.SERVER_TCP_PORT))
        self.tcp_sock.setblocking(False)

    def send(self, data):
        message = self.validate(data)
        if message is not None:
            self.tcp_sock.send(message)
            self.tcp_sock.send(MESSAGE_END)

    def get(self):
        try:
            pos = self.tcp_data.find(MESSAGE_END)
            if pos != -1:
                before_message = self.tcp_data[:pos].decode('utf-8')
                self.tcp_data = self.tcp_data[pos + len(MESSAGE_END):]
                return json.loads(before_message)
            data = self.tcp_sock.recv(self.TCP_BUFFER_SIZE)
            if data:
                self.tcp_data.extend(data)
            return None
        except BlockingIOError:
            return None
        except json.JSONDecodeError:
            print("Received malformed TCP JSON")
            return None



