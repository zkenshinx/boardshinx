import pygame
from .board_state import BoardState, BoardStateType

class MainMenu(BoardState):
    FPS = 30
    BUTTON_W = 270
    BUTTON_H = 125

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 52)

        self.join_button_rect = pygame.Rect(0, 0, 0, 0)
        self.create_button_rect = pygame.Rect(0, 0, 0, 0)
        self.exit_button_rect = pygame.Rect(0, 0, 0, 0)

        self.init_assets()

    def init_assets(self):
        self.background = pygame.image.load("background.jpg")
        button = pygame.image.load("wood_button.png")
        self.button = pygame.transform.smoothscale(button, (self.BUTTON_W, self.BUTTON_H))
        self.hover_button = self.button.copy()
        self.hover_button.fill((170, 170, 170), special_flags=pygame.BLEND_MULT)

    def entry(self, data=None):
        while True:
            if self.handle_events():
                break
            self.draw()
            self.clock.tick(self.FPS)
        return data
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.check_button_clicked(event):
                    return True
        return False

    def check_button_clicked(self, event):
        if self.join_button_rect.collidepoint(event.pos):
            self.state_manager.set_state(BoardStateType.JOIN_ROOM)
            return True
        elif self.create_button_rect.collidepoint(event.pos):
            return True
        elif self.exit_button_rect.collidepoint(event.pos):
            pygame.quit()
            exit()
        return False

    def draw(self):
        self.screen.fill("#FFFFFF")
        pygame.draw.circle(self.screen, (255, 0, 0), (self.screen.get_width() // 2, self.screen.get_height() // 2), 50)
        screen_w, screen_h = self.screen.get_size()

        # Draw background
        background = pygame.transform.smoothscale(self.background, self.screen.get_size())
        self.screen.blit(background, (0, 0))

        mouse_pos = pygame.mouse.get_pos()

        # Draw Join Room button
        x = (screen_w - self.BUTTON_W) / 2
        y = 270
        if self.join_button_rect.collidepoint(mouse_pos):
            self.screen.blit(self.hover_button, (x, y))
        else:
            self.screen.blit(self.button, (x, y))
        self.join_button_rect = self.button.get_rect(topleft=(x, y))
        text_surface = self.font.render("Join Room", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(x + self.BUTTON_W / 2, y + self.BUTTON_H / 2))
        self.screen.blit(text_surface, text_rect)

        # Draw Create Room button
        y = 450
        if self.create_button_rect.collidepoint(mouse_pos):
            self.screen.blit(self.hover_button, (x, y))
        else:
            self.screen.blit(self.button, (x, y))
        self.create_button_rect = self.button.get_rect(topleft=(x, y))
        text_surface = self.font.render("Create Room", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(x + self.BUTTON_W / 2, y + self.BUTTON_H / 2))
        self.screen.blit(text_surface, text_rect)

        # Draw Exit button
        y = 630
        if self.exit_button_rect.collidepoint(mouse_pos):
            self.screen.blit(self.hover_button, (x, y))
        else:
            self.screen.blit(self.button, (x, y))
        self.exit_button_rect = self.button.get_rect(topleft=(x, y))
        text_surface = self.font.render("Exit", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(x + self.BUTTON_W / 2, y + self.BUTTON_H / 2))
        self.screen.blit(text_surface, text_rect)

        pygame.display.flip()

