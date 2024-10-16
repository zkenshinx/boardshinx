import math
import json
import socket
import os
import pygame, sys
import random

from uuid import uuid4
from random import randint
from functools import lru_cache

from src.state_manager import GameStateManager

ROTATION_STEP = 90
ROTATION_STEP_MOD = 360
PIXEL_PERFECT = 5

class BoardObject:

    def __init__(self):
        self.static_rendering = False
        self.is_focused = False
        self.draggable = False
        self.clickable = True
        self.rotatable = False
        self.z_index = 0
        self.rotation = 0

    def update(self):
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

class Image(pygame.sprite.Sprite, BoardObject):

    image_cache = dict()

    """Represents an image in the game."""
    def __init__(self, front_path, x, y, width, height, group, game, flipable=False, draggable=True, rotatable=True, back_path=None):
        super().__init__(group)
        BoardObject.__init__(self)
        self.game  = game
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        self.rect = pygame.rect.Rect(x, y, width, height)
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
        self.display = Image.create_display(image_path, self.rect.width, self.rect.height, self.rotation)

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
            holder.mark_focused(self.game.collision_manager.colliderect(self.original_rect, holder.original_rect))

        for hand in self.game.GIP.get_hands():
            hand.mark_focused(self.game.collision_manager.colliderect(self.original_rect, hand.original_rect))
        return self

    def release(self):
        if self._try_add_image_to_deck():
            return
        self._try_add_image_to_hand()

    def _try_add_image_to_deck(self):
        for holder in self.game.GIP.get_holders():
            if self.game.collision_manager.colliderect(self.original_rect, holder.original_rect):
                holder.add_image(self)
                return True
        return False

    def _try_add_image_to_hand(self):
        for hand in self.game.GIP.get_hands():
            if self.game.collision_manager.colliderect(self.original_rect, hand.original_rect):
                hand.add_image(self)

    def flip(self):
        if not self.flipable:
            return
        self.is_front = not self.is_front
        self.game.network_mg.flip_image_send(self)
        self.update()

    def mark_focused(self, is_focused):
        pass

    def __repr__(self):
        return f"Image: {self.front_image_path}"

class Dice(pygame.sprite.Sprite, BoardObject):

    """Represents a dice in the game."""
    def __init__(self, paths, x, y, width, height, group, game, draggable=True, rotatable=True):
        super().__init__(group)
        BoardObject.__init__(self)
        self.game = game
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        self.rect = pygame.rect.Rect(x, y, width, height)
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
        self.display = Image.create_display(self.current_image_path, self.rect.width, self.rect.height, self.rotation)

    @staticmethod
    @lru_cache(maxsize=4096)
    def create_display(image_path, width, height, rotation):
        image = pygame.image.load(image_path).convert_alpha()
        scaled_image = pygame.transform.smoothscale(image, (width, height))
        return scaled_image

    def clicked(self):
        self.roll()

    def roll(self):
        ongoing_event = OngoingRoll(self, self.game)
        self.game.add_ongoing(ongoing_event)

    def set_random(self):
        self.current_image_path = random.choice(self.paths)
        self.update()

    def mark_focused(self, is_focused):
        pass

class Selection(pygame.sprite.Sprite, BoardObject):

    PHASE_NONE = 0
    PHASE_SELECTING = 1
    PHASE_SELECTED = 2

    """Represents a dice in the game."""
    def __init__(self, group, game):
        super().__init__(group)
        BoardObject.__init__(self)
        self.game = game
        self.z_index = 0
        self.render = False
        self._type = "selection"
        self.rotation = 0
        self.start_pos = (0, 0)
        self.end_pos = (0, 0)
        self.selected_objects = []
        self.phase = Selection.PHASE_NONE
        self.original_rect = pygame.rect.Rect(0, 0, 0, 0)
        self.rect = self.original_rect.copy()
        self.clickable = False
        self.update()

    def update(self):
        self.display = self.create_display()

    def create_display(self):
        surface = None
        # TODO: why dice knows about zoom_scale?!?!?!
        scale = self.game.camera.zoom_scale
        if self.phase == Selection.PHASE_SELECTING:
            width = abs(self.end_pos[0] - self.start_pos[0]) * scale
            height = abs(self.end_pos[1] - self.start_pos[1]) * scale

            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            surface.fill((173, 216, 230, 128))
            pygame.draw.rect(surface, (0, 0, 255), (0, 0, width, height), 2)

        elif self.phase == Selection.PHASE_SELECTED:
            min_x = min(sprite.rect.topleft[0] for sprite in self)
            min_y = min(sprite.rect.topleft[1] for sprite in self)
            max_x = max(sprite.rect.bottomright[0] for sprite in self)
            max_y = max(sprite.rect.bottomright[1] for sprite in self)
            width = (max_x - min_x) * max(scale, 1 / scale)
            height = (max_y - min_y) * max(scale, 1 / scale)
            surface = pygame.Surface((width, height), pygame.SRCALPHA)

            for sprite in self:
                rect = sprite.rect.copy().move(-min_x, -min_y)
                rect.x *= scale
                rect.y *= scale
                surface.fill((0, 0, 255, 100), rect)
            self.start_pos = (min_x, min_y)
            self.end_pos = (max_x, max_y)
        else:
            return None

        self.original_rect = surface.get_rect(topleft=(min(self.start_pos[0], self.end_pos[0]),
                                                        min(self.start_pos[1], self.end_pos[1])))
        self.rect = self.original_rect.copy()
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
        min_x = min(sprite.rect.topleft[0] for sprite in self)
        min_y = min(sprite.rect.topleft[1] for sprite in self)
        max_x = max(sprite.rect.bottomright[0] for sprite in self)
        max_y = max(sprite.rect.bottomright[1] for sprite in self)
        width = (max_x - min_x) / scale
        height = (max_y - min_y) / scale

        rect = pygame.rect.Rect(min_x, min_y, width, height)
        center = rect.center

        for sprite in self:
            to_x = p[0] - center[0] + sprite.rect.center[0]
            to_y = p[1] - center[1] + sprite.rect.center[1]
            self.game.transform_manager.move_sprite_to_centered(sprite, to_x, to_y)
            self.game.assign_z_index(sprite)
        return self

    def mark_focused(self, is_focused):
        pass

    def start_selection(self):
        self.start_pos = self.game.camera.mouse_pos()
        self.end_pos = self.start_pos
        self.render = True
        self.phase = Selection.PHASE_SELECTING

    def finish_selection(self):
        self.phase = Selection.PHASE_SELECTED
        self.selected_objects.clear()
        for sprite in self.game.GIP.get_rendered_objects():
            if sprite == self or not sprite.draggable:
                continue
            elif self.game.collision_manager.colliderect(self.rect, sprite.rect):
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

class OngoingMove:
    def __init__(self, start_pos, end_pos, count, move_obj, game, callback_fn=None):
        self.game = game
        self.start_pos = pygame.Vector2(*start_pos)
        self.end_pos = pygame.Vector2(*end_pos)
        self.count = count
        self.current_count = 0
        self.move_obj = move_obj
        self.callback_fn = callback_fn

    def lerp(self, t):
        return self.start_pos + (self.end_pos - self.start_pos) * t

    def update(self):
        self.current_count += 1
        if self.is_finished():
            pos = self.end_pos
        else:
            t = self.current_count / self.count 
            pos = self.lerp(t)
        self.game.transform_manager.move_sprite_to(self.move_obj, pos.x, pos.y)

    def is_finished(self):
        if self.current_count >= self.count:
            if self.callback_fn is not None:
                self.callback_fn(self.move_obj)
            return True
        return False

class OngoingShuffle:
    def __init__(self, holder, game):
        self.game = game
        self.holder = holder
        self.step = 0
        self.step_counter = 0

        # Initial step
        images_for_animation = 10
        self.top_images = []
        for i in range(images_for_animation):
            top_image = self.holder.pop_image(send_message=False)
            if top_image is None:
                break
            next = self.generate_random_next_coordinate()
            self.game.transform_manager.move_sprite_to(top_image, *next)
            self.top_images.append(top_image)
            self.game.assign_z_index(top_image)

    def generate_random_next_coordinate(self):
        diff_left = int(-self.holder.original_rect.width * 0.9)
        diff_right = int(self.holder.original_rect.width * 0.2)
        center = self.holder.original_rect.center
        next_x = center[0] + randint(diff_left, diff_right)
        next_y = center[1] + randint(diff_left, diff_right)
        return next_x, next_y

    def update(self):
        limit = 10
        if self.step_counter % limit == 0:
            self.step += 1
            if self.step == 6:
                return
            for image in self.top_images:
                if self.step == 5:
                    dest = self.holder.original_rect.topleft
                else:
                    dest = self.generate_random_next_coordinate()
                ongoing_event = OngoingMove(image.original_rect.topleft, dest, limit, image, self.game, None)
                self.game.add_ongoing(ongoing_event)
        self.step_counter += 1

    def is_finished(self):
        if self.step >= 6:
            for image in self.top_images:
                self.holder.add_image(image, False)
            return True

class OngoingRoll:
    def __init__(self, dice, game):
        self.game = game
        self.dice = dice
        self.step = 0
        self.start_rect = self.dice.original_rect.copy()

    def generate_random_next_coordinate(self):
        diff_left = int(-self.start_rect.width * 0.1)
        diff_right = int(self.start_rect.width * 0.1)
        topleft = self.start_rect.topleft
        next_x = topleft[0] + randint(diff_left, diff_right)
        next_y = topleft[1] + randint(diff_left, diff_right)
        return next_x, next_y

    def update(self):
        self.step += 1
        if self.step % 3 == 0:
            dest = self.generate_random_next_coordinate()
            self.game.transform_manager.move_sprite_to(self.dice, *dest)
            self.dice.set_random()

    def is_finished(self):
        if self.step >= 50:
            self.game.transform_manager.move_sprite_to(self.dice, self.start_rect.x, self.start_rect.y)
            return True
        return False

class Holder(pygame.sprite.Sprite, BoardObject):
    """Represents an image deck in the game."""
    def __init__(self, x, y, width, height, group, game):
        super().__init__(group)
        BoardObject.__init__(self)
        self.game = game
        self.group = group
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.z_index = 0
        self._type = "holder"
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
            top_image = self.deck[-1]
            top_image_x = (self.rect.width - top_image.rect.width) // 2
            top_image_y = (self.rect.height - top_image.rect.height) // 2
            surface.blit(top_image.display, (top_image_x, top_image_y))

        if self.is_focused:
            gray_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
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

class PlayerHand(pygame.sprite.Sprite, BoardObject):
    def __init__(self, x, y, width, height, group, game):
        super().__init__(group)
        BoardObject.__init__(self)
        self.original_rect = pygame.rect.Rect(x, y, width, height)
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.game = game
        self.group = group
        self._type = "player_hand"
        self.deck = []
        self.render = True
        self.insert_image_index = 0
        self.margin = 10
        self.create_display()

    def create_display(self):
        border_thickness = int((self.rect.height + 99) / 100)
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
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
        image_width = image.rect.width
        image_height = image.rect.height
        image_original_width = image.original_rect.width
        image_original_height = image.original_rect.height
        # Needed to determine where hovering image goes
        if self.is_focused:
            closest_dist = float('inf')

            start_x = (self.original_rect.width - (self.margin * deck_len + image_original_width * (deck_len + 1)) ) / 2
            start_y = (self.original_rect.height - image_original_height) / 2
            for i in range(deck_len + 1):
                x = start_x + i * self.margin + i * image_original_width
                y = start_y
                center_x = self.original_rect.x + (x + image_original_width / 2)
                center_y = self.original_rect.y + (y + image_original_height / 2)

                mouse_x, mouse_y = self.camera.mouse_pos()
                dist = math.hypot(center_x - mouse_x, center_y - mouse_y)
                if dist < closest_dist:
                    closest_dist = dist
                    self.insert_image_index = i

            start_x = (self.rect.width - (self.margin * deck_len + image.rect.width * (deck_len + 1)) ) / 2
            start_y = (self.rect.height - image.rect.height) / 2
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

        start_x = (self.rect.width - (self.margin * (deck_len - 1) + image.rect.width * deck_len) ) / 2
        start_y = (self.rect.height - image.rect.height) / 2
        for i in range(deck_len):
            image = self.deck[i]
            x = start_x + i * self.margin + i * image_width
            y = start_y
            surface.blit(image.display, (x, y))
        
        return surface

    @property
    def display(self):
        return self.create_display()

    def add_image(self, image):
        if image not in self.deck:
            self.game.network_mg.add_image_to_hand_send(image)
            image.render = False
            self.mark_focused(False)
            #if not image.is_front:
            #    image.flip()
            self.deck.insert(self.insert_image_index, image)

    def remove_image(self, image):
        if image in self.deck:
            self.game.network_mg.remove_image_from_hand_send(image)
            image.render = True
            if image.is_front:
                image.flip()
            self.deck.remove(image)

    def holding(self):
        deck_len = len(self.deck)
        if deck_len > 0:
            image = self.deck[0]
            image_original_width = image.original_rect.width
            image_original_height = image.original_rect.height
            start_x = (self.original_rect.width - (self.margin * (deck_len - 1) + image_original_width * deck_len) ) / 2
            start_y = (self.original_rect.height - image_original_height) / 2
            for i in range(deck_len):
                x = self.original_rect.x + start_x + i * self.margin + i * image_original_width
                y = self.original_rect.y + start_y
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

class Button(pygame.sprite.Sprite, BoardObject):
    def __init__(self, group, game, text, x, y, width, height, font_size=25):
        super().__init__(group)
        BoardObject.__init__(self)
        self.game = game
        self.group = group
        self._type = "button"
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

    def clicked(self):
        pass

    def update(self):
        self.create_display()

class ShuffleButton(Button):

    def __init__(self, group, game, x, y, width, height, holder, font_size=25):
        super().__init__(group, game, "Shuffle", x, y, width, height, font_size)
        self.game = game
        self.holder = holder
        self._type = "shuffle_button"

    def clicked(self):
        self.game.network_mg.shuffle_button_clicked_send(self)
        self.shuffle()

    def shuffle(self):
        self.holder.shuffle()
        # Animation
        ongoing_shuffle = OngoingShuffle(self.holder, self.game)
        self.game.add_ongoing(ongoing_shuffle)
        

class RetrieveButton(Button):

    def __init__(self, group, game, x, y, width, height, deck, images_to_retrieve, font_size=25):
        super().__init__(group, game, "Retrieve", x, y, width, height, font_size)
        self.game = game
        self.deck = deck
        self.images_to_retrieve = images_to_retrieve
        self._type = "retrieve_button"

    def clicked(self):
        self.game.network_mg.retrieve_button_clicked_send(self)
        self.retrieve()

    def retrieve(self):
        for image in self.images_to_retrieve:
            if hasattr(self.game, "player_hand") and image in self.game.player_hand.deck:
                self.game.player_hand.remove_image(image)
            if image not in self.deck.deck:
                def callback(image):
                    image.assign_front(False)
                    self.deck.add_image(image, send_message=False)
                ongoing_event = OngoingMove(image.rect.topleft, self.deck.rect.topleft, 45, image, self.game, callback)
                game.add_ongoing(ongoing_event)

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
            "dice": 2,
            "selection": 101,
            "player_hand": 100,
        }
        for sprite in sorted(self.sprite_group.sprites(), key=lambda x : order_priority[x._type]):
            # TODO: refactor
            sprite.rect.width = sprite.original_rect.width * self.zoom_scale
            sprite.rect.height = sprite.original_rect.height * self.zoom_scale
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
                self.display_surface.blit(sprite.display, sprite.rect.topleft)
                continue
            # Sprite might be inner rotated
            pos_x, pos_y = self.camera.apply_zoom(*self.camera.apply_rotation(*sprite.rect.topleft))
            global_rotation = self.camera.global_rotation
            rotation = global_rotation + sprite.rotation
            rotated_sprite = pygame.transform.rotate(sprite.display, global_rotation + sprite.rotation)
            if global_rotation == 90:
                pos_y -= sprite.rect.width
            elif global_rotation == 180:
                pos_x -= sprite.rect.width
                pos_y -= sprite.rect.height
            elif global_rotation == 270:
                pos_x -= sprite.rect.height
            self.display_surface.blit(rotated_sprite, (pos_x, pos_y))

        # Debugging
        center = self.camera.apply_zoom(0, 0)
        pygame.draw.circle(self.display_surface, 'red', center, 10)
        mouse_pos = self.camera.reverse_zoom(*pygame.mouse.get_pos())
        font = pygame.font.SysFont(None, 24)
        text_surface = font.render(f'{mouse_pos}', True, 'black')
        self.display_surface.blit(text_surface, (10, 10))

class TransformManager:

    def __init__(self, camera):
        self.camera = camera

    def move_sprite_abs(self, sprite, abs):
        sprite.original_rect.move_ip(abs)
        sprite.rect.move_ip(abs)

    def move_sprite_to(self, sprite, x, y):
        x = round(x / PIXEL_PERFECT) * PIXEL_PERFECT
        y = round(y / PIXEL_PERFECT) * PIXEL_PERFECT
        sprite.original_rect.topleft = (x, y)
        sprite.rect.topleft = (x, y)

    def move_sprite_to_centered(self, sprite, x, y):
        sprite.original_rect.center = (x, y)
        sprite.rect.center = (x, y)
        # Experimental feature
        x = round(sprite.rect.topleft[0] / PIXEL_PERFECT) * PIXEL_PERFECT
        y = round(sprite.rect.topleft[1] / PIXEL_PERFECT) * PIXEL_PERFECT
        sprite.original_rect.topleft = (x, y)
        sprite.rect.topleft = (x, y)

    def move_sprite_to_centered_zoomed(self, sprite, x, y):
        x, y = self.camera.reverse_rotation(*self.camera.reverse_zoom(x, y))
        # Experimental feature
        x = round(x / PIXEL_PERFECT) * PIXEL_PERFECT
        y = round(y / PIXEL_PERFECT) * PIXEL_PERFECT
        sprite.original_rect.topleft = (x - sprite.original_rect.width / 2, y - sprite.original_rect.height / 2)
        sprite.rect.topleft = (x - sprite.rect.width / (2 * self.camera.zoom_scale), y - sprite.rect.height / (2 * self.camera.zoom_scale))

class CollisionManager:
    
    def __init__(self, camera):
        self.camera = camera

    def colliderect(self, rect1, rect2):
        def normalize(rect):
            rect_copy = rect.copy()
            rect_copy.width /= self.camera.zoom_scale
            rect_copy.height /= self.camera.zoom_scale
            return rect_copy
        return normalize(rect1).colliderect(normalize(rect2))

    def collidepoint(self, rect, point_pos):
        return rect.collidepoint(self.camera.reverse_rotation(*self.camera.reverse_zoom(*point_pos)))


class SpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

class Game:
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60

    def __init__(self):
        self.network_mg = NetworkManager(self)
        pygame.init()
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Boardshinx")
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

        GameStateManager.load_game_state(self)

        self.selection = Selection(self.sprite_group, self)
        assign_id(self.selection)
        self.assign_inf_z_index(self.selection)
        self.network_mg.set_networking(True)

    def run(self):
        """Main game loop."""
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
            self.running = False
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
        self.selection.end_pos = self.camera.mouse_pos()

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
            if self.collision_manager.collidepoint(obj.original_rect, mouse_pos):
                self.GOM.try_rotate_obj(direction, obj)
                break

    def mouse_motion(self, event):
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
            if self.collision_manager.collidepoint(sprite.original_rect, mouse_pos):
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
            if self.collision_manager.collidepoint(obj.original_rect, event.pos):
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
        """
        Processes a mouse click by checking if any rendered object is clicked.
        It triggers the clicked object's 'clicked' method. 

        Args:
            mouse_pos (tuple): The (x, y) position of the mouse click.

        Returns:
            bool: True if an object was clicked, False otherwise.
        """
        for obj in sorted([s for s in self.sprite_group.sprites() if s.render and s.clickable], key= lambda x : -x.z_index):
            if self.collision_manager.collidepoint(obj.original_rect, mouse_pos):
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

    def initialize_z_index(self):
        for obj in self.mp.keys():
            self.z_index_iota = max(self.z_index_iota, self.mp[obj].z_index + 1)

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
            self.camera.zoom(self.zooms[self.zoom_index])

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()

class GameObjectManipulator:

    def __init__(self, game, group, game_info_provider):
        self.game = game
        self.GIP = game_info_provider

    def try_rotate_obj(self, direction, obj):
        if self.GIP.can_rotate(obj):
            obj.rotation = (obj.rotation + ROTATION_STEP * direction) % ROTATION_STEP_MOD
            obj.original_rect.width, obj.original_rect.height = obj.original_rect.height, obj.original_rect.width

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
        self.game.transform_manager.move_sprite_to(self.game.mp[message["object_id"]], x, y)

    def flip_image_send(self, image):
        if not self.networking_status:
            return
        message = {
            "action": "flip_image",
            "image_id": image._id,
            "is_front": image.is_front
        }
        self.send_to_server(message)

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
        self.send_to_server(message)

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
        self.send_to_server(message)

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
        self.send_to_server(message)

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
        self.send_to_server(message)

    def rotate_object_received(self, message):
        self.game.mp[message["object_id"]].rotate(message["direction"], False)

    def retrieve_button_clicked_send(self, button):
        if not self.networking_status:
            return
        message = {
            "action": "retrieve_button_clicked",
            "button_id": button._id
        }
        self.send_to_server(message)

    def retrieve_button_clicked_received(self, message):
        self.game.mp[message["button_id"]].retrieve()

    def shuffle_button_clicked_send(self, button):
        if not self.networking_status:
            return
        message = {
            "action": "shuffle_button_clicked",
            "button_id": button._id
        }
        self.send_to_server(message)

    def shuffle_button_clicked_received(self, message):
        self.game.mp[message["button_id"]].shuffle()

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

