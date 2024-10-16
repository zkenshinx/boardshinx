import pygame
from .board_state import BoardState

class JoinRoom(BoardState):
    FPS = 30
    BUTTON_W = 200
    BUTTON_H = 50
    INPUT_W = 300
    INPUT_H = 50
    LABEL_OFFSET = 75
    ROOM_LABEL_Y = 215
    NAME_LABEL_Y = 315
    ROOM_INPUT_Y = 200
    NAME_INPUT_Y = 300
    BUTTON_Y = 400
    COLOR_BOX_SIZE = 80
    COLOR_Y_OFFSET = 520
    COLORS = [(0, 255, 0), (0, 255, 255), (255, 0, 0), 
              (255, 165, 0), (127, 0, 255), (139, 69, 19)]  # Green, Blue, Red, Orange, Violet, Brown

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.label_font = pygame.font.Font(None, 28)
        self.color_label_font = pygame.font.Font(None, 36)

        self.room_code = ""
        self.user_name = ""
        self.input_active = [False, False]
        self.join_button_rect = pygame.Rect(0, 0, self.BUTTON_W, self.BUTTON_H)
        self.show_colors = False

    def entry(self, data=None):
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(self.FPS)
        return data

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.show_colors:
                    # Check if a color box was clicked
                    # TODO: improve
                    for i in range(6):
                        box_rect = pygame.Rect((self.screen.get_width() - self.COLOR_BOX_SIZE) // 2 + (i % 3) * (self.COLOR_BOX_SIZE + 10), 
                                               self.COLOR_Y_OFFSET + (i // 3) * (self.COLOR_BOX_SIZE + 10), 
                                               self.COLOR_BOX_SIZE, self.COLOR_BOX_SIZE)
                        if box_rect.collidepoint(event.pos):
                            print(f"Selected color: {self.COLORS[i]}")
                elif self.join_button_rect.collidepoint(event.pos):
                    self.find_room()
                else:
                    self.input_active[0] = pygame.Rect((self.screen.get_width() - self.INPUT_W) // 2, self.ROOM_INPUT_Y, self.INPUT_W, self.INPUT_H).collidepoint(event.pos)
                    self.input_active[1] = pygame.Rect((self.screen.get_width() - self.INPUT_W) // 2, self.NAME_INPUT_Y, self.INPUT_W, self.INPUT_H).collidepoint(event.pos)
            if event.type == pygame.KEYDOWN:
                if self.input_active[0]:
                    if event.key == pygame.K_BACKSPACE:
                        self.room_code = self.room_code[:-1]
                    elif len(self.room_code) < 6:
                        self.room_code += event.unicode
                elif self.input_active[1]:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_name = self.user_name[:-1]
                    else:
                        self.user_name += event.unicode

    def find_room(self):
        self.user_name = self.user_name.lower()

        if not self.user_name.isalpha() or len(self.user_name) == 0:
            return

        print(f"Finding room {self.room_code} for user {self.user_name}")
        self.show_colors = True

    def draw(self):
        self.screen.fill("#FFFFFF")

        mouse_pos = pygame.mouse.get_pos()

        # Draw Room Label
        room_label_surface = self.label_font.render("Room:", True, (0, 0, 0))
        self.screen.blit(room_label_surface, ((self.screen.get_width() - self.INPUT_W) // 2 - self.LABEL_OFFSET, self.ROOM_LABEL_Y))

        # Draw Room Code Input Box
        room_code_rect = pygame.Rect((self.screen.get_width() - self.INPUT_W) // 2, self.ROOM_INPUT_Y, self.INPUT_W, self.INPUT_H)
        room_code_color = (180, 180, 180) if room_code_rect.collidepoint(mouse_pos) else (200, 200, 200)
        self.draw_rounded_rect(room_code_rect, room_code_color, 10)
        room_code_surface = self.font.render(self.room_code, True, (0, 0, 0))
        text_rect = room_code_surface.get_rect(center=room_code_rect.center)
        self.screen.blit(room_code_surface, text_rect)

        # Draw Name Label
        name_label_surface = self.label_font.render("Name:", True, (0, 0, 0))
        self.screen.blit(name_label_surface, ((self.screen.get_width() - self.INPUT_W) // 2 - self.LABEL_OFFSET, self.NAME_LABEL_Y))

        # Draw User Name Input Box
        user_name_rect = pygame.Rect((self.screen.get_width() - self.INPUT_W) // 2, self.NAME_INPUT_Y, self.INPUT_W, self.INPUT_H)
        user_name_color = (180, 180, 180) if user_name_rect.collidepoint(mouse_pos) else (200, 200, 200)
        self.draw_rounded_rect(user_name_rect, user_name_color, 10)
        user_name_surface = self.font.render(self.user_name, True, (0, 0, 0))
        text_rect = user_name_surface.get_rect(center=user_name_rect.center)
        self.screen.blit(user_name_surface, text_rect)

        # Draw Find Button
        self.join_button_rect.topleft = ((self.screen.get_width() - self.BUTTON_W) // 2, self.BUTTON_Y)
        button_color = (0, 100, 0) if self.join_button_rect.collidepoint(mouse_pos) else (0, 128, 0)
        self.draw_rounded_rect(self.join_button_rect, button_color, 10)
        button_text_surface = self.font.render("Find", True, (255, 255, 255))
        text_rect = button_text_surface.get_rect(center=self.join_button_rect.center)
        self.screen.blit(button_text_surface, text_rect)

        if self.show_colors:
            # Draw color selection text
            color_text_surface = self.color_label_font.render("Choose your color:", True, (0, 0, 0))
            color_text_rect = color_text_surface.get_rect(center=(self.screen.get_width() // 2, self.COLOR_Y_OFFSET - 30))
            self.screen.blit(color_text_surface, color_text_rect)

            # Draw Color Boxes
            for i in range(6):
                box_x = (self.screen.get_width() - self.COLOR_BOX_SIZE * 3 - 10) // 2 + (i % 3) * (self.COLOR_BOX_SIZE + 10)
                box_y = self.COLOR_Y_OFFSET + (i // 3) * (self.COLOR_BOX_SIZE + 10)
                box_rect = pygame.Rect(box_x, box_y, self.COLOR_BOX_SIZE, self.COLOR_BOX_SIZE)
                pygame.draw.rect(self.screen, self.COLORS[i], box_rect)

        pygame.display.flip()

    def draw_rounded_rect(self, rect, color, radius):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

