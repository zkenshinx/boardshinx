import pygame
from src.board_object import BoardObject
from src.ongoing import OngoingShuffle, OngoingMove

class Button(BoardObject):
    def __init__(self, group, game, text, x, y, width, height, font_size=25):
        super().__init__(group)
        self.game = game
        self.group = group
        self._type = "button"
        self.render = True
        self.text = text
        self.screen_rect = pygame.rect.Rect(x, y, width, height)
        self.world_rect = self.screen_rect.copy()
        self.font_size = font_size
        self.create_display()

    def create_display(self):
        text_color = (0, 0, 0)
        button_color = (255, 255, 255)
        border_color = (0, 0, 0)
        
        border_thickness = max(1, int(self.screen_rect.height / 50))
        surface = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, button_color, (0, 0, self.screen_rect.width, self.screen_rect.height), border_radius=7)
        
        pygame.draw.rect(surface, border_color, (0, 0, self.screen_rect.width, self.screen_rect.height), 
                         width=border_thickness, border_radius=7)

        font = pygame.font.Font(None, self.font_size)
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=(self.screen_rect.width / 2, self.screen_rect.height / 2))
        surface.blit(text_surface, text_rect)

        if self.is_focused:
            gray_overlay = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
            gray_overlay.fill((0, 0, 0, 0))
            pygame.draw.rect(gray_overlay, (128, 128, 128, 80), (0, 0, self.screen_rect.width, self.screen_rect.height), border_radius=10)
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

class SitButton(Button):

    def __init__(self, group, game, x, y, width, height, hand, font_size=25):
        super().__init__(group, game, "Sit", x, y, width, height, font_size)
        self.game = game
        self.hand = hand
        self._type = "sit_button"

    def clicked(self):
        self.game.network_mg.sit_button_clicked_send(self, self.game.name)
        self.sit(self.game.name)

    def sit(self, owner):
        self.hand.owner = owner
        self.render = False

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
                ongoing_event = OngoingMove(image.screen_rect.topleft, self.deck.screen_rect.topleft, 45, image, self.game, callback)
                self.game.add_ongoing(ongoing_event)
