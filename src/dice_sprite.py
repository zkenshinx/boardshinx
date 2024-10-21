import pygame
import random

from functools import lru_cache
from src.ongoing import OngoingRoll
from src.board_object import BoardObject

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
        self.display = Dice.create_display(self.current_image_path, self.screen_rect.width, self.screen_rect.height, self.rotation)

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
