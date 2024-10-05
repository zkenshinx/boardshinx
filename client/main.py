import os
import pygame, sys
from random import randint
from functools import lru_cache
import random

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

        self.original_width = width
        self.original_height = height
        self.is_front = random.choice([False] * 2 + [True])
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
        self.original_width = width
        self.original_height = height
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

    def mark_focused(self, is_focused):
        self.is_focused = is_focused
        self.create_deck_display()

    def update_zoom(self):
        self.create_deck_display()

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
        for sprite in sorted([s for s in self.sprites() if s.render], key= lambda x : x.z_index):
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
        sprite.original_rect.move_ip(rel)
        sprite.rect.move_ip(rel)

    def move_sprite_to(self, sprite, x, y):
        sprite.original_rect.x = x
        sprite.original_rect.y = y
        sprite.rect.x = x
        sprite.rect.y = y

    def update_sprite_pos(self, sprite):
        scale_factor = self.zoom_scale
        center_x = self.display_surface.get_size()[0] // 2 - self.rel_x
        center_y = self.display_surface.get_size()[1] // 2 - self.rel_y
        sprite.rect.width = sprite.original_width * scale_factor
        sprite.rect.height = sprite.original_height * scale_factor
        pos_x = center_x + (sprite.original_rect.x - center_x) * scale_factor + self.rel_x
        pos_y = center_y + (sprite.original_rect.y - center_y) * scale_factor + self.rel_y

    def collidepoint(self, rect, mouse_pos):
        scaled_mouse_pos = (
            (mouse_pos[0] / self.zoom_scale) - self.rel_x,
            (mouse_pos[1] / self.zoom_scale) - self.rel_y
        )
        return rect.collidepoint(scaled_mouse_pos)

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

        card_deck = CardDeck(250, 250, 230 / 1.3, 330 / 1.3, self.camera_group)

        v = 44
        with open('assets/all_cards.txt', 'r') as file:
            all_cards_front = [f.strip() for f in file.readlines()]
        with open('assets/all_back.txt', 'r') as file:
            all_cards_back = [f.strip() for f in file.readlines()]
        # hero = "tomoe-gozen"
        # deck = [f for f in os.listdir(f"assets/{hero}/deck/")]
        for i in range(v):
            for j in range(v):
                back_path = f"assets/{random.choice(all_cards_back)}"
                front_path = f"assets/{random.choice(all_cards_front)}"
                card = Card(back_path, front_path, 230*i/1.39, 329*j/1.39, 230 / 1.4, 329 / 1.4, self.camera_group)
                # index = j + i * v
                # back_path = f"assets/{hero}/back.webp"
                # front_path = f"assets/{hero}/deck/{deck[index % len(deck)]}"

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.camera_group.update()
            self.camera_group.custom_draw()
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
        elif event.type == pygame.MOUSEMOTION and self.moving_around_board:
            pass

    def key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self.running = False

    def mouse_motion(self, event):
        self.camera_group.mouse_pos = event.pos
        if self.moving_around_board and pygame.key.get_mods() & pygame.KMOD_ALT:
            self.camera_group.move_camera(event.rel)
        elif self.is_holding_object and self.held_object is not None:
            if self.held_object._type == 'card_deck':
                card_deck = self.held_object
                self.held_object = card_deck.pop_card()
                if self.held_object is not None:
                    self.camera_group.move_sprite_to(self.held_object, card_deck.original_rect.x, card_deck.rect.y)
                    self.assign_z_index(self.held_object)
                    self.move_held_object(event)
            else:
                self.move_held_object(event)
        else: # Just moving
            # Check collision with card_deck
            mouse_pos = event.pos
            for card_deck in self.get_card_decks():
                if self.camera_group.collidepoint(card_deck.original_rect, mouse_pos):
                    card_deck.mark_focused(True)
                else:
                    card_deck.mark_focused(False)

    def mouse_button_down(self, event):
        if event.button == 1 and pygame.key.get_mods() & pygame.KMOD_ALT:
            self.moving_around_board = True
        elif event.button == 1:
            self.is_holding_object = True
            mouse_pos = event.pos
            for obj in sorted([s for s in self.camera_group.sprites() if s.render], key= lambda x : -x.z_index):
                # Check if card deck was clicked
                if self.camera_group.collidepoint(obj.original_rect, mouse_pos):
                    print(obj.original_rect, mouse_pos)
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
                    mouse_pos = event.pos
                    # Check if the card was clicked
                    for obj in sorted([s for s in self.camera_group.sprites() if s.render], key= lambda x : -x.z_index):
                        if self.camera_group.collidepoint(obj.original_rect, mouse_pos):
                            if obj._type == "card_deck":
                                obj.flip_top()
                            elif obj._type == "card":
                                self.assign_z_index(obj)
                                obj.flip()
                                break
                else:
                    if self.held_object._type == "card":
                        # Check collission with all card decks
                        # TODO: optimize this
                        card_decks = [item for item in self.camera_group.sprites() if item._type == "card_deck"]
                        for card_deck in card_decks:
                            if pygame.sprite.collide_rect(self.held_object, card_deck):
                                card_deck.mark_focused(False)
                                card_deck.add_card(self.held_object)
                                # self.camera_group.remove(self.held_object)

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
                    card_deck.mark_focused(True)
                else:
                    card_deck.mark_focused(False)

    def assign_z_index(self, obj):
        obj.z_index = self.z_index_iota
        self.z_index_iota += 1

    def handle_zoom(self, event):
        next_zoom_index = self.zoom_index + event.y
        if 0 <= next_zoom_index < len(self.zooms):
            self.zoom_index = next_zoom_index
            self.camera_group.zoom(self.zooms[self.zoom_index])

    def get_card_decks(self):
        # TODO: optimize this
        return [item for item in self.camera_group.sprites() if item._type == "card_deck"]

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()

g = Game()
g.run()

