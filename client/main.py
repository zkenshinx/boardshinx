import json
import socket
import os
import pygame, sys
from random import randint
from functools import lru_cache
import random

hah_id = 0
def uuid4():
    global hah_id
    ret_val = str(hah_id)
    hah_id += 1
    return ret_val

class Zoomable:
    def update_zoom(self):
        pass

class Card(pygame.sprite.Sprite, Zoomable):

    """Represents a card in the game."""
    def __init__(self, back_path, front_path, x, y, width, height, group):
        super().__init__(group)
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.group = group
        self.back_image_path = back_path
        self.front_image_path = front_path

        self.is_front = False
        self.z_index = 0
        self.render = True
        self._type = "card"
        self.draggable = True

        self.set_image()

    def set_image(self):
        if self.is_front:
            self.display = Card.create_combined_image(self.front_image_path, self.rect.width, self.rect.height)
        else:
            self.display = Card.create_combined_image(self.back_image_path, self.rect.width, self.rect.height)

    @staticmethod
    @lru_cache(maxsize=4096)
    def create_combined_image(image_path, width, height):
        """Create a new image combining the original image and its outline."""
        border_thickness = 2
        white_space = int(height * 0.05)
        border_radius = int((width + 19) / 20)
        # border_thickness = int((height + 99) / 100)
        # white_space = int((height + 19) / 20)
        # border_radius = int((width + 19) / 20)
        image = pygame.image.load(image_path).convert_alpha()
        scaled_width = width - 2 * border_thickness
        scaled_height = height - (2 * border_thickness + 2 * white_space)
        scaled_image = pygame.transform.smoothscale(image, (scaled_width, scaled_height))
        combined_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw a filled rectangle with rounded corners
        pygame.draw.rect(combined_surface, (255, 255, 255),  # White fill
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         border_radius=border_radius)
        
        # Draw the border
        pygame.draw.rect(combined_surface, (0, 0, 0),  # Black border
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         width=border_thickness, border_radius=border_radius)
        
        combined_surface.blit(scaled_image, (border_thickness, white_space))
        return combined_surface

    def update_zoom(self):
        self.set_image()

    def flip(self):
        self.is_front = not self.is_front
        self.set_image()

    def to_json(self):
        return {
            "type": "card",
            "x": self.x,
            "y": self.y
            # "path": "assets/
        }

class CardDeck(pygame.sprite.Sprite, Zoomable):
    """Represents a card deck in the game."""
    def __init__(self, x, y, width, height, group):
        super().__init__(group)
        self.group = group
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.z_index = 0
        self._type = "card_deck"
        self.draggable = False
        self.deck = []
        self.render = True
        self.last_focused = True
        self.is_focused = False
        self.create_deck_display()

    def create_deck_display(self):
        # if self.is_focused == self.last_focused: # Optimization
        #     return
        # self.last_focused = self.is_focused
        
        # TODO: change to width and height
        border_thickness = int((self.rect.height + 99) / 100)
        border_radius = int((self.rect.width + 19) / 20)
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Draw white fill
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         border_radius=border_radius)
        
        # Draw black border
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         width=border_thickness, border_radius=border_radius)

        # Add top of card
        if len(self.deck) > 0:
            top_card = self.deck[-1]
            top_card_x = (self.rect.width - top_card.rect.width) // 2
            top_card_y = (self.rect.height - top_card.rect.height) // 2
            surface.blit(top_card.display, (top_card_x, top_card_y))


        if self.is_focused:
            gray_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            gray_overlay.fill((128, 128, 128, 80))
            surface.blit(gray_overlay, (0, 0))
        
        self.display = surface

    def add_card(self, card):
        card.render = False
        self.deck.append(card)
        self.create_deck_display()

    def pop_card(self):
        if len(self.deck) == 0:
            return None
        last = self.deck[-1]
        self.deck = self.deck[:-1]
        self.create_deck_display()
        last.render = True
        return last

    def flip_top(self):
        if len(self.deck) == 0:
            return
        self.deck[-1].flip()
        self.create_deck_display()

    # TODO: I don't like how is this done
    def shuffle(self, shuffled=[]):
        if len(shuffled) == 0:
            self.deck = random.sample(self.deck, len(self.deck))
        else:
            self.deck = shuffled
        for card in self.deck:
            if card.is_front:
                card.flip()
        self.create_deck_display()

    def mark_focused(self, is_focused):
        self.is_focused = is_focused
        self.create_deck_display()

    def update_zoom(self):
        self.create_deck_display()

class PlayerHand(pygame.sprite.Sprite, Zoomable):
    def __init__(self, group):
        self.group = group
        self._type = "player_hand"
        self.draggable = False
        self.deck = []
        self.render = True
        self.last_focused = True
        self.is_focused = False
        self.create_hand_display()

    def create_hand_display(self):
        window_width, window_height = self.group.display_surface.get_size()
        width = window_width * 0.8
        height = 250 * self.group.zoom_scale
        x = (window_width - width) / 2
        y = window_height - height
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        
        # TODO: change to width and height
        border_thickness = int((self.rect.height + 99) / 100)
        border_radius = int((self.rect.width + 79) / 80)
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Draw white fill
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         border_radius=border_radius)
        
        # Draw black border
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         width=border_thickness, border_radius=border_radius)

        # Add top of card
        if len(self.deck) > 0:
            top_card = self.deck[-1]
            top_card_x = (self.rect.width - top_card.rect.width) // 2
            top_card_y = (self.rect.height - top_card.rect.height) // 2
            surface.blit(top_card.display, (top_card_x, top_card_y))


        if self.is_focused:
            gray_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            gray_overlay.fill((128, 128, 128, 80))
            surface.blit(gray_overlay, (0, 0))
        
        self.display = surface


    def add_card(self, card):
        card.render = False
        self.deck.append(card)
        self.create_hand_display()

    def mark_focused(self, is_focused):
        self.is_focused = is_focused
        self.create_hand_display()

    def update_zoom(self):
        pass
        # self.create_deck_display()

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.zoom_scale = 1
        self.rel_x = 0
        self.rel_y = 0

    def custom_draw(self):
        self.display_surface.fill('#71ddee')

        screen_rect = self.display_surface.get_rect()
        screen_rect.x = (screen_rect.x - self.rel_x)
        screen_rect.y = (screen_rect.y - self.rel_y)
        screen_rect.width  /= self.zoom_scale
        screen_rect.height /= self.zoom_scale
        for sprite in sorted([s for s in self.sprites() if s.render] + [self.player_hand], key= lambda x : x.z_index):
            if sprite._type == "player_hand":
                self.display_surface.blit(self.player_hand.display, self.player_hand.rect.topleft)
                continue
            if screen_rect.colliderect(sprite.original_rect):
                topleft = sprite.rect.topleft
                offset_pos = ((topleft[0] + self.rel_x) * self.zoom_scale, (topleft[1] + self.rel_y) * self.zoom_scale)
                self.display_surface.blit(sprite.display,offset_pos)

    def zoom(self, new_zoom_scale):
        self.zoom_scale = new_zoom_scale
        order_priority = {
            "card": 1,
            "card_deck": 2
        }
        for sprite in sorted(self.sprites(), key=lambda x : order_priority[x._type]):
            self.update_sprite_pos(sprite)
            sprite.update_zoom()

    def move_camera(self, rel):
        rel2 = (rel[0] / self.zoom_scale, rel[1] / self.zoom_scale)
        self.rel_x += rel2[0]
        self.rel_y += rel2[1]

    def move_sprite_rel(self, sprite, rel):
        rel2 = (rel[0] / self.zoom_scale, rel[1] / self.zoom_scale)
        sprite.original_rect.move_ip(rel2)
        sprite.rect.move_ip(rel2)

    def move_sprite_to(self, sprite, x, y):
        sprite.original_rect.x = x
        sprite.original_rect.y = y
        sprite.rect.x = x
        sprite.rect.y = y

    def update_sprite_pos(self, sprite):
        scale_factor = self.zoom_scale
        center_x = self.display_surface.get_size()[0] // 2 - self.rel_x
        center_y = self.display_surface.get_size()[1] // 2 - self.rel_y
        sprite.rect.width = sprite.original_rect.width * scale_factor
        sprite.rect.height = sprite.original_rect.height * scale_factor
        pos_x = center_x + (sprite.original_rect.x - center_x) * scale_factor + self.rel_x
        pos_y = center_y + (sprite.original_rect.y - center_y) * scale_factor + self.rel_y

    def collidepoint(self, rect, mouse_pos):
        scaled_mouse_pos = (
            (mouse_pos[0] / self.zoom_scale) - self.rel_x,
            (mouse_pos[1] / self.zoom_scale) - self.rel_y
        )
        return rect.collidepoint(scaled_mouse_pos)

    def add_player_hand(self, player_hand):
        self.player_hand = player_hand

class Game:
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60
    CLICKED_OBJECT_SCALE = 1.1

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Boardshinx")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "playing"
        self.camera_group = CameraGroup()
        self.font = pygame.font.SysFont(None, 36)
        self.moving_around_board = False

        self.is_holding_object = False
        self.moved_holding_object = False
        self.held_object = None
        self.z_index_iota = 0
        self.zoom_index = 2
        self.zooms = [0.6, 0.8, 1.0, 1.2, 1.4, 1.6]

        self.mp = {}

        #card_width = 230 / 1.3
        #card_height = 330 / 1.3
        #card_deck = CardDeck(0, 0, card_width, card_height, self.camera_group)
        #card_deck._id = str(uuid4())
        #self.mp[card_deck._id] = card_deck

        #directory = 'assets/66/cards/'
        #files = os.listdir(directory)
        #all_cards = [file for file in files if os.path.isfile(os.path.join(directory, file))]

        #hero = "tomoe-gozen"
        #deck = [f for f in os.listdir(f"assets/{hero}/deck/")]
        #for c in all_cards:
        #        front_path = f"assets/66/cards/{c}"
        #        back_path = f"assets/66/back.webp"
        #        card = Card(back_path, front_path, 210/1.39, 329/1.39, 230 / 1.4, 329 / 1.4, self.camera_group)
        #        card._id = str(uuid4())
        #        self.mp[card._id] = card
        #        self.add_card_to_card_deck(card_deck, card)

        #self.save_game_state()
        self.load_game_state()

        self.player_hand = PlayerHand(self.camera_group)
        self.player_hand._id = "player_hand"
        self.camera_group.add_player_hand(self.player_hand)
        self.assign_z_index(self.player_hand)

    def run(self):
        """Main game loop."""
        self.connect_to_server()
        while self.running:
            self.handle_events()
            self.camera_group.update()
            self.camera_group.custom_draw()
            self.process_networking()
            pygame.display.update()
            self.clock.tick(self.FPS)

    def connect_to_server(self):
        message = {
            "action": "join",
            "name": str(uuid4())
        }
        send_to_server(message)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.WINDOW_WIDTH, self.WINDOW_HEIGHT = event.w, event.h
                # TODO: remove this
                self.player_hand.create_hand_display()
            self.handle_input(event)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            self.key_down(event)
        if event.type == pygame.MOUSEMOTION:
            self.mouse_motion(event)
        elif event.type == pygame.MOUSEWHEEL:
            self.handle_zoom(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_button_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_button_up(event)
        elif event.type == pygame.MOUSEMOTION and self.moving_around_board:
            pass

    def key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self.running = False
        if event.key == pygame.K_r:
            for obj in self.camera_group.sprites():
                if obj._type == "card_deck":
                    self.shuffle_card_deck(obj)


    def mouse_motion(self, event):
        self.camera_group.mouse_pos = event.pos
        if self.moving_around_board and pygame.key.get_mods() & pygame.KMOD_ALT:
            self.camera_group.move_camera(event.rel)
            self.assign_z_index(self.player_hand)
        elif self.is_holding_object and self.held_object is not None:
            if self.held_object._type == 'card_deck':
                card_deck = self.held_object
                self.held_object = self.remove_card_from_card_deck(card_deck)
                if self.held_object is not None:
                    self.camera_group.move_sprite_to(self.held_object, card_deck.original_rect.x, card_deck.rect.y)
                    self.move_held_object(event)
            else:
                self.move_held_object(event)
        else: # Just moving
            # Check collision with card_deck
            mouse_pos = event.pos
            for card_deck in self.get_card_decks():
                if self.camera_group.collidepoint(card_deck.original_rect, mouse_pos):
                    self.set_card_deck_focus(card_deck, True)
                else:
                    self.set_card_deck_focus(card_deck, False)

    def mouse_button_down(self, event):
        if event.button == 1 and pygame.key.get_mods() & pygame.KMOD_ALT:
            self.moving_around_board = True
        elif event.button == 1:
            self.is_holding_object = True
            mouse_pos = event.pos
            for obj in sorted([s for s in self.camera_group.sprites() if s.render], key= lambda x : -x.z_index):
                # Check if card deck was clicked
                if self.camera_group.collidepoint(obj.original_rect, mouse_pos):
                    if obj._type == 'card_deck':
                        self.held_object = obj
                        break
                    elif obj.draggable:
                        self.assign_z_index(obj)
                        self.held_object = obj
                        break

    def mouse_button_up(self, event):
        if event.button == 1:
            if self.is_holding_object:
                if not self.moved_holding_object:
                    self.check_click_on_object(event)
                else:
                    if self.held_object._type == "card":
                        # Check collission with all card decks
                        # TODO: optimize this
                        card_decks = [item for item in self.camera_group.sprites() if item._type == "card_deck"]
                        for card_deck in card_decks:
                            if pygame.sprite.collide_rect(self.held_object, card_deck):
                                self.add_card_to_card_deck(card_deck, self.held_object)
                                break
                self.is_holding_object = False
                self.held_object = None
                self.moved_holding_object = False
            elif self.moving_around_board:
                self.moving_around_board = False

    def move_held_object(self, event):
        self.moved_holding_object = True
        self.camera_group.move_sprite_rel(self.held_object, event.rel)
        # Check if it's card and it goes into card deck
        if self.held_object._type == "card":
            # Check collission with all card decks
            for card_deck in self.get_card_decks():
                if pygame.sprite.collide_rect(self.held_object, card_deck):
                    self.set_card_deck_focus(card_deck, True)
                else:
                    self.set_card_deck_focus(card_deck, False)
        # also broadcast
        message = {
            "action": "move_object",
            "object_id": self.held_object._id,
            "x": self.held_object.original_rect.x,
            "y": self.held_object.original_rect.y
        }
        send_to_server(message)

    def check_click_on_object(self, event):
        mouse_pos = event.pos
        # Check if something was clicked
        for obj in sorted([s for s in self.camera_group.sprites() if s.render], key= lambda x : -x.z_index):
            if self.camera_group.collidepoint(obj.original_rect, mouse_pos):
                if obj._type == "card_deck":
                    self.card_deck_clicked(obj)
                    break
                elif obj._type == "card":
                    self.card_clicked(obj)
                    break

    def assign_z_index(self, obj):
        if obj is not None:
            obj.z_index = self.z_index_iota
            self.z_index_iota += 1

    def handle_zoom(self, event):
        next_zoom_index = self.zoom_index + event.y
        if 0 <= next_zoom_index < len(self.zooms):
            self.zoom_index = next_zoom_index
            self.camera_group.zoom(self.zooms[self.zoom_index])
            # Player hand
            self.player_hand.create_hand_display()
            self.assign_z_index(self.player_hand)

    def get_card_decks(self):
        # TODO: optimize this
        return [item for item in self.camera_group.sprites() if item._type == "card_deck"]

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()

    # Action functions below
    def card_clicked(self, card, send_message=True):
        self.assign_z_index(card)
        card.flip()
        if send_message:
            message = {
                "action": "flip_card",
                "card_id": card._id
            }
            send_to_server(message)

    def card_deck_clicked(self, card_deck, send_message=True):
        card_deck.flip_top()
        if send_message:
            message = {
                "action": "flip_card_deck",
                "card_deck_id": card_deck._id
            }
            send_to_server(message)

    def add_card_to_card_deck(self, card_deck, card, send_message=True):
        card_deck.mark_focused(False)
        card_deck.add_card(card)
        if send_message:
            message = {
                "action": "add_card_to_card_deck",
                "card_id": card._id,
                "card_deck_id": card_deck._id
            }
            send_to_server(message)

    def remove_card_from_card_deck(self, card_deck, send_message=True):
        top_card = card_deck.pop_card()
        if send_message:
            message = {
                "action": "remove_card_from_card_deck",
                "card_deck_id": card_deck._id
            }
            send_to_server(message)
        if top_card is not None:
            self.assign_z_index(top_card)
        return top_card

    def set_card_deck_focus(self, card_deck, focused, send_message=True):
        if focused:
            card_deck.mark_focused(True)
        else:
            card_deck.mark_focused(False)
        if send_message:
            message = {
                "action": "set_card_deck_focus",
                "card_deck_id": card_deck._id,
                "focused": focused
            }
            send_to_server(message)

    def shuffle_card_deck(self, card_deck, send_message=True):
        card_deck.shuffle()
        if send_message:
            message = {
                "action": "shuffle_card_deck",
                "card_deck_id": card_deck._id,
                "deck": [f._id for f in card_deck.deck]
            }
            send_to_server(message)

    def process_networking(self):
        for i in range(15):
            message = get_from_server()
            if message is not None:
                self.process_message_from_server(message)
    
    def process_message_from_server(self, message):
        if message["action"] == 'move_object':
            x = message["x"]
            y = message["y"]
            self.camera_group.move_sprite_to(self.mp[message["object_id"]], x, y)
        elif message["action"] == "flip_card":
            card = self.mp[message["card_id"]]
            self.card_clicked(card, False)
        elif message["action"] == "flip_card_deck":
            card_deck = self.mp[message["card_deck_id"]]
            self.card_deck_clicked(card_deck, False)
        elif message["action"] == "add_card_to_card_deck":
            card_deck = self.mp[message["card_deck_id"]]
            card = self.mp[message["card_id"]]
            self.add_card_to_card_deck(card_deck, card, False)
        elif message["action"] == "remove_card_from_card_deck":
            card_deck = self.mp[message["card_deck_id"]]
            top_card = self.remove_card_from_card_deck(card_deck, False)
        elif message["action"] == "set_card_deck_focus":
            # TODO: this can be optimized?
            card_deck = self.mp[message["card_deck_id"]]
            focused = message["focused"]
            self.set_card_deck_focus(card_deck, focused, False)
        elif message["action"] == "shuffle_card_deck":
            card_deck = self.mp[message["card_deck_id"]]
            card_deck.shuffle([self.mp[card_id] for card_id in message["deck"]])

    def save_game_state(self):
        game_state = []
        for sprite in self.camera_group.sprites():
            if sprite._type == "card":
                game_state.append({
                    "type": "card",
                    "id": sprite._id,
                    "x": sprite.original_rect.x,
                    "y": sprite.original_rect.y,
                    "width": sprite.original_rect.width,
                    "height": sprite.original_rect.height,
                    "back_path": sprite.back_image_path,
                    "front_path": sprite.front_image_path,
                    "z_index": sprite.z_index,
                    "render": sprite.render,
                })
        for sprite in self.camera_group.sprites():
            if sprite._type == "card_deck":
                game_state.append({
                    "type": "card_deck",
                    "id": sprite._id,
                    "x": sprite.original_rect.x,
                    "y": sprite.original_rect.y,
                    "width": sprite.original_rect.width,
                    "height": sprite.original_rect.height,
                    "z_index": sprite.z_index,
                    "deck": [f._id for f in sprite.deck]
                })
        with open('game_state.json', 'w') as file:
            json.dump(game_state, file, indent=4)

    def load_game_state(self):
        with open('game_state.json', 'r') as file:
            game_state = json.load(file)
        for sprite in game_state:
            if sprite["type"] == "card":
                card = Card(sprite["back_path"], sprite["front_path"], sprite["x"], sprite["y"], sprite["width"], sprite["height"], self.camera_group)
                card.z_index = sprite["z_index"]
                card.render = sprite["render"]
                card._id = sprite["id"]
                self.mp[card._id] = card
        for sprite in game_state:
            if sprite["type"] == "card_deck":
                card_deck = CardDeck(sprite["x"], sprite["y"], sprite["width"], sprite["height"], self.camera_group)
                card_deck.z_index = sprite["z_index"]
                card_deck.deck = [self.mp[card_id] for card_id in sprite["deck"]]
                card_deck._id = sprite["id"]
                self.mp[card_deck._id] = card_deck


def get_from_server():
    try:
        data, _ = sock.recvfrom(BUFFER_SIZE)
        message = json.loads(data.decode('utf-8'))
        return message
    except BlockingIOError:
        return None

def send_to_server(data):
    message = json.dumps(data).encode('utf-8')
    sock.sendto(message, (SERVER_IP, SERVER_PORT))

def init_networking():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    return sock

SERVER_IP = '16.171.34.99'
SERVER_PORT = 23456
SERVER_IP = 'localhost'
SERVER_PORT = 23456
BUFFER_SIZE = 1024
sock = init_networking()

g = Game()
g.run()

