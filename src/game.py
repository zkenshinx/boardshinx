import math
import json
import os
import pygame, sys
import random

from random import randint
from functools import lru_cache

from src.board_state import BoardState, BoardStateType
from src.state_manager import GameStateManager
from src.network_manager import NetworkManager
from src.button_sprite import ShuffleButton, SitButton, RetrieveButton
from src.board_object import BoardObject
from src.ongoing import OngoingMove, OngoingShuffle, OngoingRoll

ROTATION_STEP = 90
ROTATION_STEP_MOD = 360
PIXEL_PERFECT = 5

class Image(BoardObject):

    image_cache = dict()

    """Represents an image in the game."""
    def __init__(self, front_path, x, y, width, height, group, game, flipable=False, draggable=True, rotatable=True, back_path=None):
        super().__init__(group)
        self.game  = game
        self.world_rect = pygame.rect.Rect(x, y, width, height)
        self.screen_rect = pygame.rect.Rect(x, y, width, height)
        self.group = group
        self.flipable = flipable
        self.front_image_path = front_path
        if self.flipable:
            self.back_image_path = back_path
        else:
            # In case of some bug
            self.image_image_path = front_path 
        self.rotatable = rotatable
        self.is_front = not self.flipable
        self.z_index = 0
        self.render = True
        self._type = "image"
        self.draggable = draggable
        self.rotation = 0

        self.update()

    def update(self):
        image_path = self.front_image_path if self.is_front else self.back_image_path
        self.display = Image.create_display(image_path, self.screen_rect.width, self.screen_rect.height, self.rotation)

    @staticmethod
    @lru_cache(maxsize=4096)
    def create_display(image_path, width, height, rotation):
        image = pygame.image.load(image_path).convert_alpha()
        scaled_image = pygame.transform.smoothscale(image, (width, height))
        return scaled_image

    def assign_front(self, is_front):
        if self.flipable and self.is_front != is_front:
            self.is_front = is_front
            self.update()

    def clicked(self):
        self.flip()

    def holding(self):
        for hand in self.game.GIP.get_hands():
            if self in hand:
                hand.remove_image(self)
                return

        for holder in self.game.GIP.get_holders():
            holder.mark_focused(self.game.collision_manager.colliderect(self.world_rect, holder.world_rect))

        for hand in self.game.GIP.get_hands():
            hand.mark_focused(self.game.collision_manager.colliderect(self.world_rect, hand.world_rect))
        return self

    def release(self):
        if self._try_add_image_to_deck():
            return
        self._try_add_image_to_hand()

    def _try_add_image_to_deck(self):
        for holder in self.game.GIP.get_holders():
            if self.game.collision_manager.colliderect(self.world_rect, holder.world_rect):
                holder.add_image(self)
                return True
        return False

    def _try_add_image_to_hand(self):
        for hand in self.game.GIP.get_hands():
            if self.game.collision_manager.colliderect(self.world_rect, hand.world_rect):
                hand.add_image(self)

    def flip(self, send_message=True):
        if not self.flipable:
            return
        self.is_front = not self.is_front
        if send_message:
            self.game.network_mg.flip_image_send(self)
        self.update()

    def mark_focused(self, is_focused):
        pass

    def __repr__(self):
        return f"Image: {self.front_image_path}"

class Dice(BoardObject):

    """Represents a dice in the game."""
    def __init__(self, paths, x, y, width, height, group, game, draggable=True, rotatable=True):
        super().__init__(group)
        self.game = game
        self.world_rect = pygame.rect.Rect(x, y, width, height)
        self.screen_rect = pygame.rect.Rect(x, y, width, height)
        self.group = group
        self.rotatable = rotatable
        self.z_index = 0
        self.render = True
        self._type = "dice"
        self.draggable = draggable
        self.rotation = 0

        self.paths = paths
        self.current_image_path = paths[0]

        self.update()

    def update(self):
        self.display = Image.create_display(self.current_image_path, self.screen_rect.width, self.screen_rect.height, self.rotation)

    @staticmethod
    @lru_cache(maxsize=4096)
    def create_display(image_path, width, height, rotation):
        image = pygame.image.load(image_path).convert_alpha()
        scaled_image = pygame.transform.smoothscale(image, (width, height))
        return scaled_image

    def clicked(self):
        self.roll()

    def roll(self, result=None, send_message=True):
        if result is None:
            result = random.randint(0, len(self.paths) - 1)
        ongoing_event = OngoingRoll(self, result, self.game)
        self.game.add_ongoing(ongoing_event)
        if send_message:
            self.game.network_mg.dice_rolled_send(self, result)

    def set_specific(self, ind):
        self.current_image_path = self.paths[ind]
        self.update()

    def set_random(self):
        self.current_image_path = random.choice(self.paths)
        self.update()

    def mark_focused(self, is_focused):
        pass

        
class Cursor(BoardObject):
    """Represents a cursor in the game."""
    def __init__(self, name, color, group, game):
        super().__init__(group)
        self.name = name
        self.color = self.hex_to_rgb(color)
        self.game = game
        self.group = group
        self.z_index = float('inf')
        self.render = True
        self._type = "cursor"
        self.rotation = 0
        
        self.cursor_image = pygame.image.load("cursor.svg").convert_alpha()
        
        self.size = (15, 20)
        self.world_rect = pygame.Rect(0, 0, *self.size)
        self.screen_rect = pygame.Rect(0, 0, *self.size)
        
        self.update()

    def update(self):
        self.display = pygame.Surface(self.size, pygame.SRCALPHA)
        scaled_cursor = pygame.transform.smoothscale(self.cursor_image, self.size)
        self.display.blit(scaled_cursor, (0, 0))
        self.apply_color_to_surface(self.display, self.color)

    def apply_color_to_surface(self, surface, color):
        w, h = surface.get_size()
        r, g, b = color
        for x in range(w):
            for y in range(h):
                a = surface.get_at((x, y))[3]
                surface.set_at((x, y), (r, g, b, a))

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def mark_focused(self, is_focused):
        pass

class Selection(BoardObject):

    PHASE_NONE = 0
    PHASE_SELECTING = 1
    PHASE_SELECTED = 2

    def __init__(self, color, group, game):
        super().__init__(group)
        self.r, self.g, self.b = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        self.game = game
        self.z_index = 0
        self.render = False
        self._type = "selection"
        self.rotation = 0
        self.world_start_pos = (0, 0)
        self.world_end_pos = (0, 0)
        self.selected_objects = []
        self.phase = Selection.PHASE_NONE
        self.world_rect = pygame.rect.Rect(0, 0, 0, 0)
        self.screen_rect = self.world_rect.copy()
        self.clickable = False
        self.update()

    def update(self):
        self.display = self.create_display()

    def create_display(self):
        surface = None
        scale = self.game.camera.zoom_scale
        world_width = abs(self.world_end_pos[0] - self.world_start_pos[0])
        world_height = abs(self.world_end_pos[1] - self.world_start_pos[1])
        if self.phase == Selection.PHASE_SELECTING:

            screen_width = world_width * scale
            screen_height = world_height * scale
            surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

            surface.fill((self.r, self.g, self.b, 50))
            pygame.draw.rect(surface, (self.r, self.g, self.b), (0, 0, screen_width, screen_height), 2)

            x = min(self.world_start_pos[0], self.world_end_pos[0])
            y = min(self.world_start_pos[1], self.world_end_pos[1])
            self.world_rect = pygame.rect.Rect(x, y, world_width, world_height)
            self.screen_rect = pygame.rect.Rect(x, y, screen_width, screen_height)
        elif self.phase == Selection.PHASE_SELECTED:
            min_x = min(sprite.world_rect.topleft[0] for sprite in self)
            min_y = min(sprite.world_rect.topleft[1] for sprite in self)
            max_x = max(sprite.world_rect.bottomright[0] for sprite in self)
            max_y = max(sprite.world_rect.bottomright[1] for sprite in self)
            width = (max_x - min_x)
            height = (max_y - min_y)
            surface = pygame.Surface((width, height), pygame.SRCALPHA)

            for sprite in self:
                rect = sprite.world_rect.copy().move(-min_x, -min_y)
                surface.fill((self.r, self.g, self.b, 125), rect)
            self.world_start_pos = (min_x, min_y)
            self.world_end_pos = (max_x, max_y)
            self.world_rect = pygame.rect.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            scaled_surface = pygame.transform.scale(surface, (width * scale, height * scale))
            self.screen_rect = scaled_surface.get_rect(topleft=(min_x, min_y))
            return scaled_surface
        else:
            return None

        return surface

    def clicked(self):
        for sprite in self:
            sprite.clicked()
            self.game.assign_z_index(sprite)
        self.reset()

    def holding(self):
        self.game.moved_holding_object = True
        p = self.game.camera.mouse_pos()

        scale = self.game.camera.zoom_scale
        min_x = min(sprite.screen_rect.topleft[0] for sprite in self)
        min_y = min(sprite.screen_rect.topleft[1] for sprite in self)
        max_x = max(sprite.screen_rect.bottomright[0] for sprite in self)
        max_y = max(sprite.screen_rect.bottomright[1] for sprite in self)
        width = (max_x - min_x) / scale
        height = (max_y - min_y) / scale

        rect = pygame.rect.Rect(min_x, min_y, width, height)
        center = rect.center

        for sprite in self:
            to_x = p[0] - center[0] + sprite.screen_rect.center[0]
            to_y = p[1] - center[1] + sprite.screen_rect.center[1]
            self.game.transform_manager.move_sprite_to_centered(sprite, to_x, to_y)
            self.game.assign_z_index(sprite)
        return self

    def mark_focused(self, is_focused):
        pass

    def start_selection(self):
        self.world_start_pos = self.game.camera.mouse_pos()
        self.world_end_pos = self.world_start_pos
        self.render = True
        self.phase = Selection.PHASE_SELECTING

    def finish_selection(self):
        self.phase = Selection.PHASE_SELECTED
        self.selected_objects.clear()
        for sprite in self.game.GIP.get_rendered_objects():
            if sprite == self or not sprite.draggable:
                continue
            elif self.game.collision_manager.colliderect(self.world_rect, sprite.world_rect):
                self.selected_objects.append(sprite)
        if len(self) == 0:
            self.reset()

    def reset(self):
        self.selected_objects.clear()
        self.render = False
        self.phase = Selection.PHASE_NONE

    def __len__(self):
        return len(self.selected_objects)

    def __contains__(self, item):
        return item in self.selected_objects

    def __iter__(self):
        return iter(self.selected_objects)

class Holder(BoardObject):
    """Represents an image deck in the game."""
    def __init__(self, x, y, width, height, group, game):
        super().__init__(group)
        self.game = game
        self.group = group
        self.world_rect = pygame.rect.Rect(x, y, width, height)
        self.screen_rect = pygame.rect.Rect(x, y, width, height)
        self.z_index = 0
        self._type = "holder"
        self.deck = []
        self.render = True
        self.last_focused = True
        self.counter = 0
        self.create_display()


    def create_display(self):
        border_thickness = int((self.screen_rect.height + 99) / 100)
        surface = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()))
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()),
                         width=border_thickness)

        if len(self.deck) > 0:
            top_image = self.deck[-1]
            top_image_x = (self.screen_rect.width - top_image.screen_rect.width) // 2
            top_image_y = (self.screen_rect.height - top_image.screen_rect.height) // 2
            surface.blit(top_image.display, (top_image_x, top_image_y))

        if self.is_focused:
            gray_overlay = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
            gray_overlay.fill((80, 80, 80, 99))
            surface.blit(gray_overlay, (0, 0))
        self.display = surface

    def add_image(self, image, send_message=True):
        if image not in self.deck:
            if send_message:
                self.game.network_mg.add_image_to_holder_send(self, image)
            self.mark_focused(False)
            image.render = False
            self.deck.append(image)
            self.create_display()

    def pop_image(self, image=None, send_message=True):
        if len(self.deck) == 0:
            return None
        if image is None:
            last = self.deck[-1]
            if send_message:
                self.game.network_mg.remove_image_from_holder_send(self, last)
            self.deck = self.deck[:-1]
            self.create_display()
            last.render = True
            return last
        else:
            # In case of networking race condition
            if image in self.deck:
                self.deck.remove(image)
                self.create_display()
                image.render = True
                self.game.assign_z_index(image)
                return image
        return None

    def hovering(self):
        pass

    def clicked(self):
        self.flip_top()

    def holding(self):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            return self
        return self.pop_image()

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
        for image in self.deck:
            if image.is_front:
                image.flip()
        self.create_display()

    def update(self):
        self.create_display()

class PlayerHand(BoardObject):
    def __init__(self, x, y, width, height, group, game, owner=""):
        super().__init__(group)
        self.world_rect = pygame.rect.Rect(x, y, width, height)
        self.screen_rect = pygame.rect.Rect(x, y, width, height)
        self.game = game
        self.group = group
        self._type = "player_hand"
        self.deck = []
        self.render = True
        self.insert_image_index = 0
        self.margin = 10
        self.owner = owner
        self.create_display()

    def create_display(self):
        border_thickness = int((self.screen_rect.height + 99) / 100)
        surface = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, (255, 255, 255),
                         (0, 0, surface.get_width(), surface.get_height()))
        pygame.draw.rect(surface, (0, 0, 0),
                         (0, 0, surface.get_width(), surface.get_height()),
                         width=border_thickness)

        self.insert_image_index = 0
        deck_len = len(self.deck)
        if deck_len == 0:
            return surface

        image = self.deck[0]
        image_width = image.screen_rect.width
        image_height = image.screen_rect.height
        image_original_width = image.world_rect.width
        image_original_height = image.world_rect.height
        # Needed to determine where hovering image goes
        if self.is_focused:
            closest_dist = float('inf')

            start_x = (self.world_rect.width - (self.margin * deck_len + image_original_width * (deck_len + 1)) ) / 2
            start_y = (self.world_rect.height - image_original_height) / 2
            for i in range(deck_len + 1):
                x = start_x + i * self.margin + i * image_original_width
                y = start_y
                center_x = self.world_rect.x + (x + image_original_width / 2)
                center_y = self.world_rect.y + (y + image_original_height / 2)

                mouse_x, mouse_y = self.game.camera.mouse_pos()
                dist = math.hypot(center_x - mouse_x, center_y - mouse_y)
                if dist < closest_dist:
                    closest_dist = dist
                    self.insert_image_index = i

            start_x = (self.screen_rect.width - (self.margin * deck_len + image.screen_rect.width * (deck_len + 1)) ) / 2
            start_y = (self.screen_rect.height - image.screen_rect.height) / 2
            for i in range(deck_len + 1):
                x = start_x + i * self.margin + i * image_width
                y = start_y
                if i == self.insert_image_index:
                    gray_overlay = pygame.Surface((image_width, image_height), pygame.SRCALPHA)
                    gray_overlay.fill((80, 80, 80, 99))
                    surface.blit(gray_overlay, (x, y))
                    continue
                j = i if i < self.insert_image_index else i - 1
                image = self.deck[j]
                surface.blit(image.display, (x, y))
            return surface

        start_x = (self.screen_rect.width - (self.margin * (deck_len - 1) + image.screen_rect.width * deck_len) ) / 2
        start_y = (self.screen_rect.height - image.screen_rect.height) / 2
        for i in range(deck_len):
            image = self.deck[i]
            x = start_x + i * self.margin + i * image_width
            y = start_y
            surface.blit(image.display, (x, y))
        
        return surface

    @property
    def display(self):
        return self.create_display()

    def add_image(self, image, index=None, send_message=True):
        if image not in self.deck:
            image.render = False
            self.mark_focused(False)

            if self.owner == self.game.name and not image.is_front:
                image.flip(False)
            elif self.owner != self.game.name and image.is_front:
                image.flip(True)

            if index is None:
                index = self.insert_image_index
            self.deck.insert(index, image)

            if send_message:
                self.game.network_mg.add_image_to_hand_send(self, image, index)

    def remove_image(self, image, send_message=True):
        if image in self.deck:
            image.render = True
            if image.is_front:
                image.flip()
            self.deck.remove(image)

            if send_message:
                self.game.network_mg.remove_image_from_hand_send(self, image)

    def holding(self):
        deck_len = len(self.deck)
        if deck_len > 0:
            image = self.deck[0]
            image_original_width = image.world_rect.width
            image_original_height = image.world_rect.height
            start_x = (self.world_rect.width - (self.margin * (deck_len - 1) + image_original_width * deck_len) ) / 2
            start_y = (self.world_rect.height - image_original_height) / 2
            for i in range(deck_len):
                x = self.world_rect.x + start_x + i * self.margin + i * image_original_width
                y = self.world_rect.y + start_y
                rect = pygame.rect.Rect(x, y, image_original_width, image_original_height)
                if rect.collidepoint(self.game.camera.mouse_pos()):
                    image = self.deck[i]
                    self.remove_image(self.deck[i])
                    return image
        return self

    def hovering(self):
        pass

    def not_hovering(self):
        self.mark_focused(False)

    def mark_focused(self, is_focused):
        if self.is_focused != is_focused:
            self.is_focused = is_focused

    def __contains__(self, item):
        return item in self.deck

class Camera:
    def __init__(self, sprite_group):
        self.sprite_group = sprite_group
        self.zoom_scale = 1
        self.offset_x = 0
        self.offset_y = 0
        self.global_rotation = 0
        self.center()

    def zoom(self, new_zoom_scale):
        self.zoom_scale = new_zoom_scale
        order_priority = {
            "image": 1,
            "holder": 2,
            "shuffle_button": 2,
            "retrieve_button": 2,
            "sit_button": 2,
            "dice": 2,
            "cursor": 2,
            "selection": 101,
            "player_hand": 100,
        }
        for sprite in sorted(self.sprite_group.sprites(), key=lambda x : order_priority[x._type]):
            sprite.screen_rect.width = sprite.world_rect.width * self.zoom_scale
            sprite.screen_rect.height = sprite.world_rect.height * self.zoom_scale
            sprite.update()

    def move_camera(self, rel):
        rel2 = (rel[0] / self.zoom_scale, rel[1] / self.zoom_scale)
        self.offset_x += rel2[0]
        self.offset_y += rel2[1]

    def apply_zoom(self, x, y):
        zoomed_x = (x + self.offset_x) * self.zoom_scale
        zoomed_y = (y + self.offset_y) * self.zoom_scale
        return zoomed_x, zoomed_y

    def reverse_zoom(self, x, y):
        reversed_x = (x / self.zoom_scale) - self.offset_x
        reversed_y = (y / self.zoom_scale) - self.offset_y
        return reversed_x, reversed_y

    def apply_rotation(self, x, y):
        radians = math.radians(-self.global_rotation)
        rotated_x = x * math.cos(radians) - y * math.sin(radians)
        rotated_y = x * math.sin(radians) + y * math.cos(radians)
        return rotated_x, rotated_y

    def reverse_rotation(self, x, y):
        radians = math.radians(self.global_rotation)
        reversed_x = x * math.cos(radians) - y * math.sin(radians)
        reversed_y = x * math.sin(radians) + y * math.cos(radians)
        return reversed_x, reversed_y

    def center(self):
        display_surface = pygame.display.get_surface()
        self.offset_x = display_surface.get_rect().width / 2
        self.offset_y = display_surface.get_rect().height / 2

    def mouse_pos(self):
        return self.reverse_rotation(*self.reverse_zoom(*pygame.mouse.get_pos()))

class Renderer:
    BACKGROUND_COLOR = "#E1E1E1"

    def __init__(self, group):
        self.display_surface = pygame.display.get_surface()
        self.group = group

    def render(self):
        self.display_surface.fill(Renderer.BACKGROUND_COLOR)

        for sprite in sorted([s for s in self.group.sprites() if s.render], key= lambda x : x.z_index):
            if sprite.static_rendering:
                self.display_surface.blit(sprite.display, sprite.screen_rect.topleft)
                continue
            # Sprite might be inner rotated
            pos_x, pos_y = self.camera.apply_zoom(*self.camera.apply_rotation(*sprite.screen_rect.topleft))
            global_rotation = self.camera.global_rotation
            rotation = 0 if sprite._type == "cursor" else global_rotation + sprite.rotation
            rotated_sprite = pygame.transform.rotate(sprite.display, rotation)
            if global_rotation == 90:
                pos_y -= sprite.screen_rect.width
            elif global_rotation == 180:
                pos_x -= sprite.screen_rect.width
                pos_y -= sprite.screen_rect.height
            elif global_rotation == 270:
                pos_x -= sprite.screen_rect.height
            self.display_surface.blit(rotated_sprite, (pos_x, pos_y))

        # Debugging
        #center = self.camera.apply_zoom(0, 0)
        #pygame.draw.circle(self.display_surface, 'red', center, 10)
        #mouse_pos = self.camera.reverse_zoom(*pygame.mouse.get_pos())
        #font = pygame.font.SysFont(None, 24)
        #text_surface = font.render(f'{mouse_pos}', True, 'black')
        #self.display_surface.blit(text_surface, (10, 10))

class TransformManager:

    def __init__(self, camera):
        self.camera = camera

    def move_sprite_abs(self, sprite, abs):
        sprite.world_rect.move_ip(abs)
        sprite.screen_rect.move_ip(abs)

    def move_sprite_to(self, sprite, x, y):
        x = round(x / PIXEL_PERFECT) * PIXEL_PERFECT
        y = round(y / PIXEL_PERFECT) * PIXEL_PERFECT
        sprite.world_rect.topleft = (x, y)
        sprite.screen_rect.topleft = (x, y)

    def move_sprite_to_centered(self, sprite, x, y):
        sprite.world_rect.center = (x, y)
        sprite.screen_rect.center = (x, y)
        # Experimental feature
        x = round(sprite.screen_rect.topleft[0] / PIXEL_PERFECT) * PIXEL_PERFECT
        y = round(sprite.screen_rect.topleft[1] / PIXEL_PERFECT) * PIXEL_PERFECT
        sprite.world_rect.topleft = (x, y)
        sprite.screen_rect.topleft = (x, y)

    def move_sprite_to_centered_zoomed(self, sprite, x, y):
        x, y = self.camera.reverse_rotation(*self.camera.reverse_zoom(x, y))
        # Experimental feature
        x = round(x / PIXEL_PERFECT) * PIXEL_PERFECT
        y = round(y / PIXEL_PERFECT) * PIXEL_PERFECT
        sprite.world_rect.topleft = (x - sprite.world_rect.width / 2, y - sprite.world_rect.height / 2)
        sprite.screen_rect.topleft = (x - sprite.screen_rect.width / (2 * self.camera.zoom_scale), y - sprite.screen_rect.height / (2 * self.camera.zoom_scale))

class CollisionManager:

    def __init__(self, camera):
        self.camera = camera

    def colliderect(self, rect1, rect2):
        return rect1.colliderect(rect2)

    def collidepoint(self, rect, point_pos):
        return rect.collidepoint(self.camera.reverse_rotation(*self.camera.reverse_zoom(*point_pos)))


class SpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

class Game(BoardState):
    FPS = 60
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720

    def __init__(self, state_manager, data):
        super().__init__(state_manager)
        self.network_mg = NetworkManager(self, data["tcp_client"], data["udp_client"])
        self.color = data["color"]
        self.name = data["name"]

        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "playing"

        self.sprite_group = SpriteGroup()
        self.renderer = Renderer(self.sprite_group)
        self.camera = Camera(self.sprite_group)
        self.collision_manager = CollisionManager(self.camera)
        self.transform_manager = TransformManager(self.camera)
        self.renderer.camera = self.camera
        self.sprite_group.camera = self.camera

        self.font = pygame.font.SysFont(None, 36)
        self.moving_around_board = False

        self.is_holding_object = False
        self.moved_holding_object = False
        self.held_object = None
        self.last_held_object = None
        self.held_down_counter = 0
        self.z_index_iota = 0
        self.zoom_index = 3
        self.zooms = [0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
        self.ongoing = []
        self.selection_present = False

        self.other_cursors = dict()

        self.mp = {}
        self.GIP = GameInfoProvider(self, self.sprite_group)
        self.GOM = GameObjectManipulator(self, self.sprite_group, self.GIP)


        def assign_id(obj):
            if len(self.mp) == 0:
                iota = 0
            else:
                iota = max(self.mp.keys()) + 1
            obj._id = iota
            self.mp[obj._id] = obj
        #GameStateManager.load_game_state(self, "dice_throne.zip")
        #self.network_mg.set_networking(True)

        self.selection = Selection(self.color, self.sprite_group, self)
        assign_id(self.selection)
        self.assign_inf_z_index(self.selection)

    def entry(self):
        """Main game loop."""
        self.network_mg.get_game_state()
        while self.running:
            self.handle_events()
            self.handle_ongoing()
            self.sprite_group.update()
            self.renderer.render()
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
        if event.type == pygame.KEYUP:
            self.key_up(event)
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
        else:
            self.move_last_held_object()

    def key_up(self, event):
        self.held_down_counter = 0
        if self.selection_present:
            self.process_end_selection()

    def key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self.running = True
        elif event.key in [pygame.K_q, pygame.K_e]:
            self.process_rotation_clicked(event)
        elif event.key in [pygame.K_z, pygame.K_x]:
            self.process_board_rotation(event)
        elif event.key in [pygame.K_c]:
            self.camera.center()
        elif event.key in [pygame.K_j, pygame.K_i, pygame.K_k, pygame.K_l]:
            self.move_last_held_object(False)
        elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            GameStateManager.save_game_state(self, output_zip_path="game_state.zip")
        elif event.key == pygame.K_LSHIFT:
            self.process_start_selection()

    def process_start_selection(self):
        self.selection_present = True
        self.selection.start_selection()

    def process_end_selection(self):
        self.selection.finish_selection()
        self.selection_present = False

    def move_selection(self):
        self.selection.world_end_pos = self.camera.mouse_pos()

    def move_last_held_object(self, count=True):
        if self.last_held_object is None:
            return
        if count:
            self.held_down_counter += 1
            if self.held_down_counter <= 7:
                return
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_j]:
            dx = -1
        elif keys[pygame.K_l]:
            dx = 1
        elif keys[pygame.K_i]:
            dy = -1
        elif keys[pygame.K_k]:
            dy = 1
        else:
            return
        self.transform_manager.move_sprite_abs(self.last_held_object, (dx, dy))

    def process_board_rotation(self, event):
        direction = 1 if event.key == pygame.K_z else -1
        self.camera.global_rotation = (self.camera.global_rotation + direction * ROTATION_STEP) % ROTATION_STEP_MOD

    def process_rotation_clicked(self, event):
        direction = 1 if event.key == pygame.K_q else -1
        if self.held_object is not None:
            self.GOM.try_rotate_obj(direction, self.held_object)
            return
        mouse_pos = pygame.mouse.get_pos()
        for obj in sorted(self.GIP.get_rendered_objects(), key= lambda x : -x.z_index):
            if self.collision_manager.collidepoint(obj.world_rect, mouse_pos):
                self.GOM.try_rotate_obj(direction, obj)
                break

    def mouse_motion(self, event):
        x, y = self.camera.mouse_pos()
        self.network_mg.cursor_moved_send(x, y, self.name, self.color)
        if self.moving_around_board and (pygame.mouse.get_pressed()[1] or pygame.key.get_mods() & pygame.KMOD_ALT):
            self.process_moving_around_board(event)
        elif self.is_holding_object and self.held_object is not None:
            self.move_held_object(event)
        elif self.selection_present:
            self.move_selection()
        elif not self.is_holding_object:
            self.process_mouse_hovering(event.pos)

    def process_moving_around_board(self, event):
        self.camera.move_camera(event.rel)

    def process_mouse_hovering(self, mouse_pos):
        for sprite in self.GIP.get_rendered_objects():
            if self.collision_manager.collidepoint(sprite.world_rect, mouse_pos):
                sprite.hovering()
            else:
                sprite.not_hovering()

    def mouse_button_down(self, event):
        if event.button == 2 or pygame.key.get_mods() & pygame.KMOD_ALT:
            self.moving_around_board = True
            return 
        elif event.button != 1:
            return

        for obj in sorted(self.GIP.get_rendered_objects(), key= lambda x : -x.z_index):
            if self.collision_manager.collidepoint(obj.world_rect, event.pos):
                self.is_holding_object = True

                if obj in self.selection:
                    self.held_object = self.selection
                    return

                self.held_object = obj
                if self.GIP.can_drag(obj):
                    self.assign_z_index(obj)
                return
        self.selection.reset()

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
        self.last_held_object = self.held_object
        self.held_object = None
        self.moved_holding_object = False

    def move_held_object(self, event):
        self.held_object = self.held_object.holding()
        if self.held_object is not None and self.GIP.can_drag(self.held_object):
            self.moved_holding_object = True
            self.transform_manager.move_sprite_to_centered_zoomed(self.held_object, event.pos[0], event.pos[1])
            self.assign_z_index(self.held_object)
            self.network_mg.move_object_send(self.held_object)

    def process_release(self):
        self.held_object.release()

    def process_click(self, mouse_pos):
        for obj in sorted([s for s in self.sprite_group.sprites() if s.render and s.clickable], key= lambda x : -x.z_index):
            if self.collision_manager.collidepoint(obj.world_rect, mouse_pos):
                if obj in self.selection:
                    self.selection.clicked()
                    return True
                self.selection.reset()
                obj.clicked()
                if obj.draggable:
                    self.assign_z_index(obj)
                return True
        return False

    def handle_ongoing(self):
        for event in self.ongoing[:]:
            event.update()
            if event.is_finished():
                self.ongoing.remove(event)

    def add_ongoing(self, ongoing_event):
        self.ongoing.append(ongoing_event)

    def cursor_moved(self, x, y, name, color):
        if name not in self.other_cursors:
            self.other_cursors[name] = Cursor(name, color, self.sprite_group, self)
        self.transform_manager.move_sprite_to(self.other_cursors[name], x, y)

    def initialize_z_index(self):
        for obj in self.mp.keys():
            self.z_index_iota = max(self.z_index_iota, self.mp[obj].z_index + 1)

    def assign_z_index(self, obj):
        if obj is not None:
            obj.z_index = self.z_index_iota
            self.z_index_iota += 1

    def assign_inf_z_index(self, obj):
        if obj is not None:
            obj.z_index = float('inf')

    def handle_zoom(self, event):
        next_zoom_index = self.zoom_index + event.y
        if 0 <= next_zoom_index < len(self.zooms):
            self.zoom_index = next_zoom_index
            self.camera.zoom(self.zooms[self.zoom_index])

    def quit(self):
        pygame.quit()

class GameObjectManipulator:

    def __init__(self, game, group, game_info_provider):
        self.game = game
        self.GIP = game_info_provider

    def try_rotate_obj(self, direction, obj, send_message=True):
        if self.GIP.can_rotate(obj):
            obj.rotation = (obj.rotation + ROTATION_STEP * direction) % ROTATION_STEP_MOD
            obj.world_rect.width, obj.world_rect.height = obj.world_rect.height, obj.world_rect.width
            if send_message:
                self.game.network_mg.rotate_object_send(obj, direction)

class GameInfoProvider:
    def __init__(self, game, group):
        self.game = game
        self.sprite_group = group

    def can_rotate(self, obj):
        return (pygame.key.get_mods() & pygame.KMOD_CTRL) or (obj is not None and obj.rotatable)

    def can_drag(self, obj):
        return (pygame.key.get_mods() & pygame.KMOD_CTRL) or (obj is not None and obj.draggable)

    def get_sprites_of_type(self, _type):
        return [item for item in self.sprite_group.sprites() if item._type == _type]

    def get_hands(self):
        return self.get_sprites_of_type("player_hand")

    def get_holders(self):
        return self.get_sprites_of_type("holder")

    def get_rendered_objects(self):
        return [s for s in self.sprite_group.sprites() if s.render]
