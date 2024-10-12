from uuid import uuid4
import json
import socket
import os
import pygame, sys
from random import randint
from functools import lru_cache
import random

class BoardObject:
    
    def __init__(self):
        self.static_rendering = False
        self.is_focused = False

    def update_zoom(self):
        pass

    def clicked(self):
        pass

    def holding(self):
        return self

    def hovering(self):
        self.mark_focused(True)

    def not_hovering(self):
        self.mark_focused(False)

    def mark_focused(self, is_focused):
        if self.is_focused != is_focused:
            self.is_focused = is_focused
            self.create_display()

    def release(self):
        pass

class Card(pygame.sprite.Sprite, BoardObject):

    """Represents a card in the game."""
    def __init__(self, back_path, front_path, x, y, width, height, group, game):
        super().__init__(group)
        BoardObject.__init__(self)
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
            self.display = Card.create_display(self.front_image_path, self.rect.width, self.rect.height)
        else:
            self.display = Card.create_display(self.back_image_path, self.rect.width, self.rect.height)

    @staticmethod
    @lru_cache(maxsize=4096)
    def create_display(image_path, width, height):
        """Create a new image combining the original image and its outline."""
        image = pygame.image.load(image_path).convert_alpha()
        scaled_image = pygame.transform.smoothscale(image, (width, height))
        return scaled_image

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
                    card_deck.add_card(self)
                    return True
            return False

        if try_add_card_to_deck(self):
            return
        
        if self.game.player_hand.check_collide_with_hand(self):
            self.game.player_hand.add_card(self)

    def flip(self):
        self.is_front = not self.is_front
        self.game.network_mg.flip_card_send(self)
        self.set_image()

    def mark_focused(self, is_focused):
        pass

class OngoingMove:
    def __init__(self, start_pos, end_pos, count, move_obj, callback_fn):
        self.start_pos = pygame.Vector2(*start_pos)
        self.end_pos = pygame.Vector2(*end_pos)
        self.count = count
        self.current_count = 0
        self.move_obj = move_obj
        self.callback_fn = callback_fn

    def lerp(self, t):
        return self.start_pos + (self.end_pos - self.start_pos) * t

    def update(self, game):
        self.current_count += 1
        if self.is_finished():
            pos = self.end_pos
        else:
            t = self.current_count / self.count 
            pos = self.lerp(t)
        game.camera_group.move_sprite_to(self.move_obj, pos.x, pos.y)

    def callback(self):
        self.callback_fn(self)

    def is_finished(self):
        return self.current_count >= self.count

class CardDeck(pygame.sprite.Sprite, BoardObject):
    """Represents a card deck in the game."""
    def __init__(self, x, y, width, height, group, game):
        super().__init__(group)
        BoardObject.__init__(self)
        self.game = game
        self.group = group
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.z_index = 0
        self._type = "card_deck"
        self.draggable = False
        self.deck = []
        self.render = True
        self.last_focused = True
        self.counter = 0
        self.create_display()


    def create_display(self):
        border_thickness = int((self.rect.height + 99) / 100)
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()))
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()),
                         width=border_thickness)

        if len(self.deck) > 0:
            top_card = self.deck[-1]
            top_card_x = (self.rect.width - top_card.rect.width) // 2
            top_card_y = (self.rect.height - top_card.rect.height) // 2
            surface.blit(top_card.display, (top_card_x, top_card_y))

        if self.is_focused:
            gray_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            gray_overlay.fill((80, 80, 80, 99))
            surface.blit(gray_overlay, (0, 0))
        self.display = surface

    def add_card(self, card, send_message=True):
        if card not in self.deck:
            if send_message:
                self.game.network_mg.add_card_to_card_deck_send(self, card)
            self.mark_focused(False)
            card.render = False
            self.deck.append(card)
            self.create_display()

    def pop_card(self, card=None, send_message=True):
        if len(self.deck) == 0:
            return None
        if card is None:
            last = self.deck[-1]
            if send_message:
                self.game.network_mg.remove_card_from_card_deck_send(self, last)
            self.deck = self.deck[:-1]
            self.create_display()
            last.render = True
            return last
        else:
            # In case of networking race condition
            if card in self.deck:
                self.deck.remove(card)
                self.create_display()
                card.render = True
                self.game.assign_z_index(card)
                return card
        return None

    def hovering(self):
        pass

    def clicked(self):
        self.flip_top()

    def holding(self):
        return self.pop_card()

    def flip_top(self):
        if len(self.deck) == 0:
            return
        self.deck[-1].flip()
        self.create_display()

    # TODO: I don't like how is this done
    def shuffle(self, shuffled=[]):
        if len(shuffled) == 0:
            self.deck = random.sample(self.deck, len(self.deck))
        else:
            self.deck = shuffled
        for card in self.deck:
            if card.is_front:
                card.flip()
        self.create_display()

    def update_zoom(self):
        self.create_display()

class PlayerHand(pygame.sprite.Sprite, BoardObject):
    def __init__(self, group, game):
        super().__init__(group)
        BoardObject.__init__(self)
        self.static_rendering = True
        self.game = game
        self.group = group
        self._type = "player_hand"
        self.draggable = False
        self.deck = []
        self.render = True
        self.hovering_card_middle_x = 0
        self.hovering_card_index = 0
        self.create_display()

    def create_display(self):
        window_width, window_height = self.group.display_surface.get_size()
        width = window_width * 0.8
        height = 250 * self.group.zoom_scale
        x = (window_width - width) / 2
        y = window_height - height
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        
        border_thickness = int((self.rect.height + 99) / 100)
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()))
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()),
                         width=border_thickness)

        self.game.assign_z_index(self)
        margin = 10
        # Needed to determine where hovering card goes
        self.hovering_card_index = 0
        closest_dist = float('inf')

        for i in range(len(self.deck)):
            card = self.deck[i]
            start_x = (x - self.group.zoom_scale * self.group.offset_x) / self.group.zoom_scale
            start_y = (y - self.group.zoom_scale * self.group.offset_y) / self.group.zoom_scale
            card.rect.x = start_x + (i + 1) * margin + i * card.rect.width / self.group.zoom_scale
            card.rect.y = start_y + 7
            card.original_rect.x = card.rect.x
            card.original_rect.y = card.rect.y
            self.game.assign_z_index(card)

            dist = abs(self.hovering_card_middle_x - card.rect.centerx)
            if dist < closest_dist:
                closest_dist = dist
                self.hovering_card_index = i

        if self.is_focused and self.hovering_card_index is not None:
            if len(self.deck) > 0 and closest_dist > self.deck[0].rect.width // 2:
                self.hovering_card_index = len(self.deck)
            for i in range(self.hovering_card_index, len(self.deck)):
                card = self.deck[i]
                start_x = (x - self.group.zoom_scale * self.group.offset_x) / self.group.zoom_scale
                start_y = (y - self.group.zoom_scale * self.group.offset_y) / self.group.zoom_scale
                card.rect.x = start_x + (i + 2) * margin + (i + 1) * card.rect.width / self.group.zoom_scale
                card.rect.y = start_y + 7
                card.original_rect.x = card.rect.x
                card.original_rect.y = card.rect.y

            gray_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            gray_overlay.fill((80, 80, 80, 99))
            surface.blit(gray_overlay, (0, 0))
        
        return surface

    @property
    def display(self):
        return self.create_display()

    def add_card(self, card):
        if card not in self.deck:
            self.game.network_mg.add_card_to_hand_send(card)
            self.mark_focused(False)
            if not card.is_front:
                card.flip()
            self.deck.insert(self.hovering_card_index, card)

    def remove_card(self, card):
        if card in self.deck:
            self.game.network_mg.remove_card_from_hand_send(card)
            if card.is_front:
                card.flip()
            self.deck.remove(card)

    def hovering(self):
        pass

    def not_hovering(self):
        self.mark_focused(False)

    def mark_focused(self, is_focused):
        if self.is_focused != is_focused:
            self.is_focused = is_focused

    def check_collide_with_hand(self, card):
        card_rect = card.rect.copy()
        card_rect.topleft = self.group.apply_zoom(*card_rect.topleft)
        if card_rect.colliderect(self.rect):
            self.hovering_card_middle_x = card_rect.centerx
            self.mark_focused(True)
            return True
        else:
            self.mark_focused(False)
            return False

class Button(pygame.sprite.Sprite, BoardObject):
    def __init__(self, group, game, text, x, y, width, height, font_size=25):
        super().__init__(group)
        BoardObject.__init__(self)
        self.game = game
        self.group = group
        self._type = "button"
        self.draggable = False
        self.render = True
        self.text = text
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.original_rect = self.rect.copy()
        self.font_size = font_size
        self.create_display()

    def create_display(self):
        text_color = (0, 0, 0)
        button_color = (255, 255, 255)
        border_color = (0, 0, 0)
        
        border_thickness = max(1, int(self.rect.height / 50))
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, button_color, (0, 0, self.rect.width, self.rect.height), border_radius=7)
        
        pygame.draw.rect(surface, border_color, (0, 0, self.rect.width, self.rect.height), 
                         width=border_thickness, border_radius=7)

        font = pygame.font.Font(None, self.font_size)
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=(self.rect.width / 2, self.rect.height / 2))
        surface.blit(text_surface, text_rect)

        if self.is_focused:
            gray_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            gray_overlay.fill((0, 0, 0, 0))
            pygame.draw.rect(gray_overlay, (128, 128, 128, 80), (0, 0, self.rect.width, self.rect.height), border_radius=10)
            surface.blit(gray_overlay, (0, 0))
        
        self.display = surface
        self.game.assign_z_index(self)

    def clicked(self):
        pass

    def update_zoom(self):
        self.create_display()

class ShuffleButton(Button):

    def __init__(self, group, game, x, y, width, height, decks, font_size=25):
        super().__init__(group, game, "Shuffle", x, y, width, height, font_size)
        self.game = game
        self.decks = decks

    def clicked(self):
        for card_deck in self.decks:
            card_deck.shuffle()

class RetrieveButton(Button):

    def __init__(self, group, game, x, y, width, height, deck, cards_to_retrieve, font_size=25):
        super().__init__(group, game, "Retrieve", x, y, width, height, font_size)
        self.game = game
        self.deck = deck
        self.cards_to_retrieve = cards_to_retrieve


    def clicked(self):
        for card in self.cards_to_retrieve:
            if card in self.game.player_hand.deck:
                self.game.player_hand.remove_card(card)
            if card not in self.deck.deck:
                def callback(event):
                    self.deck.add_card(event.move_obj)
                ongoing_event = OngoingMove(card.rect.topleft, self.deck.rect.topleft, 60, card, callback)
                game.add_ongoing(ongoing_event)

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.zoom_scale = 1
        self.offset_x = 0
        self.offset_y = 0

    def custom_draw(self):
        self.display_surface.fill('#E1E1E1')

        screen_rect = self.display_surface.get_rect()
        screen_rect.x = (screen_rect.x - self.offset_x)
        screen_rect.y = (screen_rect.y - self.offset_y)
        screen_rect.width  /= self.zoom_scale
        screen_rect.height /= self.zoom_scale
        for sprite in sorted([s for s in self.sprites() if s.render], key= lambda x : x.z_index):
            if sprite.static_rendering:
                self.display_surface.blit(sprite.display, sprite.rect.topleft)
                continue
            if self.colliderect(screen_rect, sprite.rect):
                offset_pos = self.apply_zoom(*sprite.rect.topleft)
                self.display_surface.blit(sprite.display, offset_pos)

    def zoom(self, new_zoom_scale):
        self.zoom_scale = new_zoom_scale
        order_priority = {
            "card": 1,
            "card_deck": 2,
            "player_hand": 3,
            "button": 4
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
        self.network_mg = NetworkManager(self)
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
        self.ongoing = []

        self.mp = {}

        self.load_game_state()

        # Stuff
        button_width, button_height = 140, 40
        button_y = (253 / 2 - button_height / 2)
        button_x = (-150)
        button = ShuffleButton(self.camera_group, self, button_x, button_y, button_width, button_height, [self.mp["0"]], 25)
        button = RetrieveButton(self.camera_group, self,  button_x, button_y - 50, button_width, button_height, self.mp["0"], list(self.mp["0"].deck), 25)

        self.player_hand = PlayerHand(self.camera_group, self)
        self.player_hand._id = "player_hand"
        self.assign_z_index(self.player_hand)
        self.network_mg.set_networking(True)

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.handle_ongoing()
            self.camera_group.custom_draw()
            self.network_mg.process_networking()
            pygame.display.update()
            self.clock.tick(self.FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.WINDOW_WIDTH, self.WINDOW_HEIGHT = event.w, event.h
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
                    obj.shuffle()
                    self.network_mg.shuffle_card_deck_send(obj)

    def mouse_motion(self, event):
        if self.moving_around_board and pygame.mouse.get_pressed()[1]:
            self.process_moving_around_board(event)
        elif self.is_holding_object and self.held_object is not None:
            self.move_held_object(event)
        elif not self.is_holding_object:
            self.process_mouse_hovering(event.pos)

    def process_moving_around_board(self, event):
        self.camera_group.move_camera(event.rel)

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
            self.network_mg.move_object_send(self.held_object)

    def process_release(self):
        self.held_object.release()
        self.assign_z_index(self.held_object)

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
                self.assign_z_index(obj)
                return True
        return False

    def handle_ongoing(self):
        for event in self.ongoing[:]:
            event.update(self)
            if event.is_finished():
                self.ongoing.remove(event)
                event.callback()

    def add_ongoing(self, ongoing_event):
        self.ongoing.append(ongoing_event)

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
                card_deck = CardDeck(sprite["x"], sprite["y"], sprite["width"], sprite["height"], self.camera_group, self)
                card_deck.z_index = sprite["z_index"]
                card_deck._id = sprite["id"]
                for card_id in sprite["deck"]:
                    card_deck.add_card(self.mp[card_id])
                self.mp[card_deck._id] = card_deck

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()


class NetworkManager:

    def move_object_send(self, obj):
        if not self.networking_status:
            return
        message = {
            "action": "move_object",
            "object_id": obj._id,
            "x": obj.original_rect.x,
            "y": obj.original_rect.y
        }
        self.send_to_server(message)

    def move_object_received(self, message):
        x = message["x"]
        y = message["y"]
        self.game.camera_group.move_sprite_to(self.game.mp[message["object_id"]], x, y)

    def flip_card_send(self, card):
        if not self.networking_status:
            return
        message = {
            "action": "flip_card",
            "card_id": card._id,
            "is_front": card.is_front
        }
        self.send_to_server(message)

    def flip_card_received(self, message):
        card = self.game.mp[message["card_id"]]
        card.assign_front(message["is_front"])
        for card_deck in self.game.get_card_decks():
            if card in card_deck.deck:
                card_deck.create_display()

    def add_card_to_card_deck_send(self, card_deck, card):
        if not self.networking_status:
            return
        message = {
            "action": "add_card_to_card_deck",
            "card_id": card._id,
            "card_deck_id": card_deck._id
        }
        self.send_to_server(message)

    def add_card_to_card_deck_received(self, message):
        card_deck = self.game.mp[message["card_deck_id"]]
        card = self.game.mp[message["card_id"]]
        card_deck.add_card(card, False)

    def remove_card_from_card_deck_send(self, card_deck, card):
        if not self.networking_status:
            return
        message = {
            "action": "remove_card_from_card_deck",
            "card_id": card._id,
            "card_deck_id": card_deck._id
        }
        self.send_to_server(message)

    def remove_card_from_card_deck_received(self, message):
        card_deck = self.game.mp[message["card_deck_id"]]
        card_deck.pop_card(self.game.mp[message["card_id"]], False)

    def add_card_to_hand_send(self, card, send_message=True):
        if not self.networking_status:
            return
        message = {
            "action": "add_card_to_hand",
            "card_id": card._id
        }
        self.send_to_server(message)

    def add_card_to_hand_received(self, message):
        card = self.game.mp[message["card_id"]]
        card.render = False

    def remove_card_from_hand_send(self, card, send_message=True):
        if not self.networking_status:
            return
        message = {
            "action": "remove_card_from_hand",
            "card_id": card._id
        }
        self.send_to_server(message)

    def remove_card_from_hand_received(self, message):
        card = self.game.mp[message["card_id"]]
        card.assign_front(False)
        card.render = True

    def shuffle_card_deck_send(self, card_deck, send_message=True):
        if not self.networking_status:
            return
        message = {
            "action": "shuffle_card_deck",
            "card_deck_id": card_deck._id,
            "deck": [f._id for f in card_deck.deck]
        }
        self.send_to_server(message)

    def shuffle_card_deck_received(self, message):
        card_deck = self.game.mp[message["card_deck_id"]]
        card_deck.shuffle([self.game.mp[card_id] for card_id in message["deck"]])

    def connect_to_server(self):
        message = {
            "action": "join",
            "name": str(uuid4())
        }
        self.send_to_server(message)

    def process_networking(self):
        for i in range(15):
            message = self.get_from_server()
            if message is not None:
                self.received_mapping[message["action"]](message)
    
    def get_from_server(self):
        try:
            data, _ = self.sock.recvfrom(self.BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))
            return message
        except BlockingIOError:
            return None

    def send_to_server(self, data):
        message = json.dumps(data).encode('utf-8')
        self.sock.sendto(message, (self.SERVER_IP, self.SERVER_PORT))

    def init_networking(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

    def init_functions(self):
        self.received_mapping = {
            "flip_card": self.flip_card_received,
            "move_object": self.move_object_received,
            "add_card_to_card_deck": self.add_card_to_card_deck_received,
            "remove_card_from_card_deck": self.remove_card_from_card_deck_received,
            "add_card_to_hand": self.add_card_to_hand_received,
            "remove_card_from_hand": self.remove_card_from_hand_received,
            "shuffle_card_deck": self.shuffle_card_deck_received,
        }

    def set_networking(self, status):
        self.networking_status = status

    def __init__(self, game):
        self.networking_status = False
        self.game = game
        if len(sys.argv) > 1:
            self.SERVER_IP = sys.argv[1]
        else:
            self.SERVER_IP = 'localhost'
        self.SERVER_PORT = 23456
        self.BUFFER_SIZE = 1024
        self.init_functions()
        self.init_networking()
        self.connect_to_server()


if __name__ == "__main__":
    game = Game()
    game.run()

