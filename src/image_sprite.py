import pygame

from functools import lru_cache
from src.board_object import BoardObject

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

