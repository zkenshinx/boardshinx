import pygame
import random

from src.board_object import BoardObject

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

