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

class BoardObject:
    def update_zoom(self):
        pass

    def clicked(self):
        pass

    def holding(self):
        return self

    def hovering(self):
        pass

    def not_hovering(self):
        pass

    def release(self):
        pass

class Card(pygame.sprite.Sprite, BoardObject):

    """Represents a card in the game."""
    def __init__(self, back_path, front_path, x, y, width, height, group, game):
        super().__init__(group)
        self.game  = game
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
        image = pygame.image.load(image_path).convert_alpha()
        scaled_width = width - 2 * border_thickness
        scaled_height = height - (2 * border_thickness + 2 * white_space)
        scaled_image = pygame.transform.smoothscale(image, (scaled_width, scaled_height))
        combined_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        pygame.draw.rect(combined_surface, (255, 255, 255), 
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         border_radius=border_radius)
        pygame.draw.rect(combined_surface, (0, 0, 0),
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         width=border_thickness, border_radius=border_radius)
        combined_surface.blit(scaled_image, (border_thickness, white_space))
        return combined_surface

    def update_zoom(self):
        self.set_image()

    def assign_front(self, is_front):
        self.is_front = is_front
        self.set_image()

    def clicked(self):
        self.flip()

    def holding(self):
        if self in self.game.player_hand.deck:
            self.game.player_hand.remove_card(self)
        for card_deck in self.game.get_card_decks():
            if self.group.colliderect(self.rect, card_deck.rect):
                card_deck.mark_focused(True)
            else:
                card_deck.mark_focused(False)
        self.game.player_hand.check_collide_with_hand(self)
        return self

    def release(self):
        def try_add_card_to_deck(self):
            for card_deck in self.game.get_card_decks():
                if self.group.colliderect(self.rect, card_deck.rect):
                    self.game.add_card_to_card_deck(card_deck, self)
                    return True
            return False

        if try_add_card_to_deck(self):
            return
        
        if self.game.player_hand.check_collide_with_hand(self):
            self.game.add_card_to_hand(self)

    def flip(self):
        self.is_front = not self.is_front
        self.set_image()

class CardDeck(pygame.sprite.Sprite, BoardObject):
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
        self.counter = 0
        self.create_deck_display()


    def create_deck_display(self):
        border_thickness = int((self.rect.height + 99) / 100)
        border_radius = int((self.rect.width + 19) / 20)
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         border_radius=border_radius)
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         width=border_thickness, border_radius=border_radius)

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

    def clicked(self):
        self.flip_top()

    def hovering(self):
        self.mark_focused(True)

    def not_hovering(self):
        self.mark_focused(False)

    def holding(self):
        return self.pop_card()

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
        if self.is_focused != is_focused:
            self.is_focused = is_focused
            self.create_deck_display()

    def update_zoom(self):
        self.create_deck_display()

class PlayerHand(pygame.sprite.Sprite, BoardObject):
    def __init__(self, group, game):
        super().__init__(group)
        self.game = game
        self.group = group
        self._type = "player_hand"
        self.draggable = False
        self.deck = []
        self.render = True
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
        
        border_thickness = int((self.rect.height + 99) / 100)
        border_radius = int((self.rect.width + 79) / 80)
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         border_radius=border_radius)
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()), 
                         width=border_thickness, border_radius=border_radius)

        self.game.assign_z_index(self)
        margin = 10
        for i in range(len(self.deck)):
            card = self.deck[i]
            start_x = (x - self.group.zoom_scale * self.group.offset_x) / self.group.zoom_scale
            start_y = (y - self.group.zoom_scale * self.group.offset_y) / self.group.zoom_scale
            card.rect.x = start_x + (i + 1) * margin + i * card.rect.width / self.group.zoom_scale
            card.rect.y = start_y + 7
            card.original_rect.x = card.rect.x
            card.original_rect.y = card.rect.y
            self.game.assign_z_index(card)

        if self.is_focused:
            gray_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            gray_overlay.fill((128, 128, 128, 80))
            surface.blit(gray_overlay, (0, 0))
        
        self.display = surface

    def add_card(self, card):
        if card not in self.deck:
            if not card.is_front:
                card.flip()
            self.deck.append(card)
            self.create_hand_display()

    def remove_card(self, card):
        if card in self.deck:
            if card.is_front:
                card.flip()
            self.deck.remove(card)
            self.create_hand_display()

    def mark_focused(self, is_focused):
        if self.is_focused != is_focused:
            self.is_focused = is_focused
            self.create_hand_display()

    def check_collide_with_hand(self, card):
        card_rect = card.rect.copy()
        card_rect.topleft = self.group.apply_zoom(*card_rect.topleft)
        if card_rect.colliderect(self.rect):
            self.mark_focused(True)
            return True
        else:
            self.mark_focused(False)
            return False

    def update_zoom(self):
        self.create_hand_display()

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.zoom_scale = 1
        self.offset_x = 0
        self.offset_y = 0

    def custom_draw(self):
        self.display_surface.fill('#71ddee')

        screen_rect = self.display_surface.get_rect()
        screen_rect.x = (screen_rect.x - self.offset_x)
        screen_rect.y = (screen_rect.y - self.offset_y)
        screen_rect.width  /= self.zoom_scale
        screen_rect.height /= self.zoom_scale
        s = 0
        for sprite in sorted([s for s in self.sprites() if s.render], key= lambda x : x.z_index):
            if sprite._type == "player_hand":
                self.display_surface.blit(sprite.display, sprite.rect.topleft)
                continue
            if self.colliderect(screen_rect, sprite.rect):
                offset_pos = self.apply_zoom(*sprite.rect.topleft)
                self.display_surface.blit(sprite.display, offset_pos)
                s += 1
        print(s)

    def zoom(self, new_zoom_scale):
        self.zoom_scale = new_zoom_scale
        order_priority = {
            "card": 1,
            "card_deck": 2,
            "player_hand": 3
        }
        for sprite in sorted(self.sprites(), key=lambda x : order_priority[x._type]):
            self.update_sprite_pos(sprite)
            sprite.update_zoom()

    def move_camera(self, rel):
        rel2 = (rel[0] / self.zoom_scale, rel[1] / self.zoom_scale)
        self.offset_x += rel2[0]
        self.offset_y += rel2[1]

    def move_sprite_rel(self, sprite, rel):
        rel2 = (rel[0] / self.zoom_scale, rel[1] / self.zoom_scale)
        sprite.original_rect.move_ip(rel2)
        sprite.rect.move_ip(rel2)

    def move_sprite_to(self, sprite, x, y):
        sprite.original_rect.topleft = (x, y)
        sprite.rect.topleft = (x, y)

    def move_sprite_to_centered_zoomed(self, sprite, x, y):
        sprite.rect.center = self.reverse_zoom(x, y)
        sprite.original_rect.center = sprite.rect.center

    def update_sprite_pos(self, sprite):
        scale_factor = self.zoom_scale
        center_x = self.display_surface.get_size()[0] // 2 - self.offset_x
        center_y = self.display_surface.get_size()[1] // 2 - self.offset_y
        sprite.rect.width = sprite.original_rect.width * scale_factor
        sprite.rect.height = sprite.original_rect.height * scale_factor
        pos_x = center_x + (sprite.original_rect.x - center_x) * scale_factor + self.offset_x
        pos_y = center_y + (sprite.original_rect.y - center_y) * scale_factor + self.offset_y

    def colliderect(self, rect1, rect2):
        def normalize(rect):
            rect_copy = rect.copy()
            rect_copy.width /= self.zoom_scale
            rect_copy.height /= self.zoom_scale
            return rect_copy
        return normalize(rect1).colliderect(normalize(rect2))

    def collidepoint(self, rect, mouse_pos):
        return rect.collidepoint(self.reverse_zoom(*mouse_pos))

    def apply_zoom(self, x, y):
        zoomed_x = (x + self.offset_x) * self.zoom_scale
        zoomed_y = (y + self.offset_y) * self.zoom_scale
        return zoomed_x, zoomed_y

    def reverse_zoom(self, x, y):
        reversed_x = (x / self.zoom_scale) - self.offset_x
        reversed_y = (y / self.zoom_scale) - self.offset_y
        return reversed_x, reversed_y

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
        self.zoom_index = 3
        self.zooms = [0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]

        self.mp = {}

        self.load_game_state()

        self.player_hand = PlayerHand(self.camera_group, self)
        self.player_hand._id = "player_hand"
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

    def key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self.running = False
        if event.key == pygame.K_r:
            for obj in self.camera_group.sprites():
                if obj._type == "card_deck":
                    self.shuffle_card_deck(obj)

    def mouse_motion(self, event):
        if random.randint(1, 10) == 10:
            # transformed = self.camera_group.apply_zoom(*event.pos)
            transformed = self.camera_group.reverse_zoom(*event.pos)
        if self.moving_around_board and pygame.mouse.get_pressed()[1]:
            self.process_moving_around_board(event)
        elif self.is_holding_object and self.held_object is not None:
            self.move_held_object(event)
        elif not self.is_holding_object:
            self.process_mouse_hovering(event.pos)

    def process_moving_around_board(self, event):
        self.camera_group.move_camera(event.rel)
        self.player_hand.create_hand_display()

    def process_mouse_hovering(self, mouse_pos):
        for sprite in self.get_rendered_objects():
            if self.camera_group.collidepoint(sprite.original_rect, mouse_pos):
                sprite.hovering()
            else:
                sprite.not_hovering()

    def mouse_button_down(self, event):
        if event.button == 2:
            self.moving_around_board = True
            return 
        elif event.button != 1:
            return

        mouse_pos = event.pos
        for obj in sorted(self.get_rendered_objects(), key= lambda x : -x.z_index):
            if self.camera_group.collidepoint(obj.original_rect, mouse_pos):
                self.is_holding_object = True
                self.held_object = obj
                if obj.draggable:
                    self.assign_inf_z_index(obj)
                break

    def mouse_button_up(self, event):
        if event.button == 2:
            self.moving_around_board = False
            return

        if event.button != 1:
            return

        if not self.is_holding_object:
            return
        self.handle_held_object_release(event.pos)

    def handle_held_object_release(self, pos):
        if not self.moved_holding_object:
            self.process_click(pos)
        else:
            self.process_release()
        self.reset_held_object()

    def reset_held_object(self):
        self.is_holding_object = False
        self.held_object = None
        self.moved_holding_object = False

    def move_held_object(self, event):
        self.held_object = self.held_object.holding()
        if self.held_object.draggable:
            self.moved_holding_object = True
            self.camera_group.move_sprite_to_centered_zoomed(self.held_object, event.pos[0], event.pos[1])
            self.assign_inf_z_index(self.held_object)

        message = {
            "action": "move_object",
            "object_id": self.held_object._id,
            "x": self.held_object.original_rect.x,
            "y": self.held_object.original_rect.y
        }
        send_to_server(message)

    def process_release(self):
        self.held_object.release()

    def process_click(self, mouse_pos):
        """
        Processes a mouse click by checking if any rendered object is clicked.
        It triggers the clicked object's 'clicked' method. 

        Args:
            mouse_pos (tuple): The (x, y) position of the mouse click.

        Returns:
            bool: True if an object was clicked, False otherwise.
        """
        for obj in sorted([s for s in self.camera_group.sprites() if s.render], key= lambda x : -x.z_index):
            if self.camera_group.collidepoint(obj.original_rect, mouse_pos):
                obj.clicked()
                return True
        return False

    def assign_z_index(self, obj):
        """
        Assigns a unique z-index to the given object. 
        Each object is assigned a higher z-index sequentially.
        
        Args:
            obj: The object to assign the z-index to.
        """
        if obj is not None:
            obj.z_index = self.z_index_iota
            self.z_index_iota += 1

    def assign_inf_z_index(self, obj):
        """
        Assigns an infinite z-index to the given object. This effectively ensures 
        that the object is always rendered on top of any other object.
        
        Args:
            obj: The object to assign the infinite z-index to.
        """
        if obj is not None:
            obj.z_index = float('inf')

    def handle_zoom(self, event):
        next_zoom_index = self.zoom_index + event.y
        if 0 <= next_zoom_index < len(self.zooms):
            self.zoom_index = next_zoom_index
            self.camera_group.zoom(self.zooms[self.zoom_index])

    def get_card_decks(self):
        return [item for item in self.camera_group.sprites() if item._type == "card_deck"]

    def get_rendered_objects(self):
        return [s for s in self.camera_group.sprites() if s.render]

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

    def add_card_to_hand(self, card, send_message=True):
        self.player_hand.mark_focused(False)
        self.player_hand.add_card(card)
        if send_message:
            message = {
                "action": "add_card_to_hand",
                "object_id": card._id
            }
            send_to_server(message)

    def remove_card_from_hand(self, card, send_message=True):
        self.player_hand.mark_focused(False)
        self.player_hand.remove_card(card)
        card.render = True
        if send_message:
            message = {
                "action": "remove_card_from_hand",
                "object_id": card._id
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
        elif message["action"] == "add_card_to_hand":
            obj = self.mp[message["object_id"]]
            obj.assign_front(True)
            obj.render = False
        elif message["action"] == "remove_card_from_hand":
            obj = self.mp[message["object_id"]]
            obj.assign_front(False)
            obj.render = True

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
                card = Card(sprite["back_path"], sprite["front_path"], sprite["x"], sprite["y"], sprite["width"], sprite["height"], self.camera_group, self)
                card.z_index = sprite["z_index"]
                card.render = sprite["render"]
                card._id = sprite["id"]
                self.mp[card._id] = card
        for sprite in game_state:
            if sprite["type"] == "card_deck":
                card_deck = CardDeck(sprite["x"], sprite["y"], sprite["width"], sprite["height"], self.camera_group)
                card_deck.z_index = sprite["z_index"]
                for card_id in sprite["deck"]:
                    card_deck.add_card(self.mp[card_id])
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

SERVER_IP = 'localhost'
SERVER_PORT = 23456
BUFFER_SIZE = 1024
sock = init_networking()

g = Game()
g.run()

