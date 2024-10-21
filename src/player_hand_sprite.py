import pygame

from src.board_object import BoardObject

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

