import pygame
from .board_state import BoardState, BoardStateType
from .network_manager import TCPClient, UDPClient
import sys

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
    COLORS = {
        "inactive": (150, 150, 150),
        "hover": (180, 180, 180),
        "default": (200, 200, 200),
        "button_active": (0, 100, 0),
        "button_default": (0, 128, 0),
        "error": (255, 0, 0)
    }

    def __init__(self, state_manager, data=None):
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
        self.available_colors = []
        self.assigned_color = None

        self.tcp_client = TCPClient()
        self.udp_client = UDPClient()
        self.tcp_client.add_callback("join", self.handle_join_received)
        self.tcp_client.add_callback("assign_color", self.assign_color_received)

    def entry(self):
        while self.state_manager.get_state() == BoardStateType.JOIN_ROOM:
            self.handle_events()
            self.draw()
            self.tcp_client.process()
            self.clock.tick(self.FPS)
        return {
            "tcp_client": self.tcp_client,
            "udp_client": self.udp_client,
            "color": self.assigned_color,
            "name": self.user_name
        }

    def handle_join_received(self, message):
        if message["result"] == "success":
            self.show_colors = True
            self.available_colors = message.get("colors", [])
            self.error_message = ""
            self.udp_client.send({
                "action": "join",
                "name": message["name"]
            })
        else:
            self.show_colors = False
            self.error_message = message.get("message", "An error occurred.")

    def assign_color_received(self, message):
        if message["result"] == "success":
            self.assigned_color = message["color"]
            self.state_manager.set_state(BoardStateType.GAME)
        else:
            self.error_message = "Someone already got the color :)"
            self.available_colors = message.get("colors", [])
            return False

    def handle_text_input(self, event, text, max_length):
        if event.key == pygame.K_BACKSPACE:
            return text[:-1]
        elif len(text) < max_length and event.unicode.isascii():
            return text + event.unicode
        return text

    def handle_tab(self):
        if self.input_active[0]:
            self.input_active = [False, True]
        else:
            self.input_active = [True, False]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.show_colors:
                    self.handle_color_selection(event.pos)
                elif self.join_button_rect.collidepoint(event.pos):
                    self.find_room()
                else:
                    self.input_active[0] = pygame.Rect((self.screen.get_width() - self.INPUT_W) // 2, self.ROOM_INPUT_Y, self.INPUT_W, self.INPUT_H).collidepoint(event.pos)
                    self.input_active[1] = pygame.Rect((self.screen.get_width() - self.INPUT_W) // 2, self.NAME_INPUT_Y, self.INPUT_W, self.INPUT_H).collidepoint(event.pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.handle_tab()
                elif self.input_active[0]:
                    self.room_code = self.handle_text_input(event, self.room_code, 6)
                elif self.input_active[1]:
                    self.user_name = self.handle_text_input(event, self.user_name, 10)

    def handle_color_selection(self, mouse_pos):
        for i, color in enumerate(self.available_colors):
            box_x = (self.screen.get_width() - self.COLOR_BOX_SIZE * 3 - 10) // 2 + (i % 3) * (self.COLOR_BOX_SIZE + 10)
            box_y = self.COLOR_Y_OFFSET + (i // 3) * (self.COLOR_BOX_SIZE + 10)
            box_rect = pygame.Rect(box_x, box_y, self.COLOR_BOX_SIZE, self.COLOR_BOX_SIZE)
            if box_rect.collidepoint(mouse_pos):
                self.color_chosen(color)

    def color_chosen(self, color):
        self.tcp_client.send({
            "action": "color_chosen",
            "color": color
        })

    def find_room(self):
        self.user_name = self.user_name.lower()

        if len(self.room_code) == 0 or not self.user_name.isalpha():
            return

        self.tcp_client.send({
            "action": "join",
            "room": self.room_code,
            "name": self.user_name
        })

    def draw(self):
        self.screen.fill("#FFFFFF")
        mouse_pos = pygame.mouse.get_pos()

        self.draw_label("Room:", (self.screen.get_width() - self.INPUT_W) // 2 - self.LABEL_OFFSET, self.ROOM_LABEL_Y)
        self.draw_input_box(self.room_code, (self.screen.get_width() - self.INPUT_W) // 2, self.ROOM_INPUT_Y, self.input_active[0], mouse_pos)

        self.draw_label("Name:", (self.screen.get_width() - self.INPUT_W) // 2 - self.LABEL_OFFSET, self.NAME_LABEL_Y)
        self.draw_input_box(self.user_name, (self.screen.get_width() - self.INPUT_W) // 2, self.NAME_INPUT_Y, self.input_active[1], mouse_pos)

        self.draw_button("Find", self.join_button_rect, self.BUTTON_Y, mouse_pos)

        if hasattr(self, 'error_message'):
            self.draw_error_message()

        if self.show_colors:
            self.draw_color_boxes()

        pygame.display.flip()

    def draw_label(self, text, x, y):
        label_surface = self.label_font.render(text, True, (0, 0, 0))
        self.screen.blit(label_surface, (x, y))

    def draw_input_box(self, text, x, y, active, mouse_pos):
        input_rect = pygame.Rect(x, y, self.INPUT_W, self.INPUT_H)
        input_color = self.COLORS["inactive"] if active else self.COLORS["hover"] if input_rect.collidepoint(mouse_pos) else self.COLORS["default"]
        self.draw_rounded_rect(input_rect, input_color, 10)
        input_surface = self.font.render(text, True, (0, 0, 0))
        self.screen.blit(input_surface, input_surface.get_rect(center=input_rect.center))

    def draw_button(self, text, button_rect, y, mouse_pos):
        button_rect.topleft = ((self.screen.get_width() - self.BUTTON_W) // 2, y)
        button_color = self.COLORS["button_active"] if button_rect.collidepoint(mouse_pos) else self.COLORS["button_default"]
        self.draw_rounded_rect(button_rect, button_color, 10)
        button_surface = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(button_surface, button_surface.get_rect(center=button_rect.center))

    def draw_error_message(self):
        error_surface = self.label_font.render(self.error_message, True, self.COLORS["error"])
        error_rect = error_surface.get_rect(center=(self.screen.get_width() // 2, self.BUTTON_Y + 70))
        self.screen.blit(error_surface, error_rect)

    def draw_color_boxes(self):
        color_text_surface = self.color_label_font.render("Choose your color:", True, (0, 0, 0))
        color_text_rect = color_text_surface.get_rect(center=(self.screen.get_width() // 2, self.COLOR_Y_OFFSET - 30))
        self.screen.blit(color_text_surface, color_text_rect)

        for i, color in enumerate(self.available_colors):
            box_x = (self.screen.get_width() - self.COLOR_BOX_SIZE * 3 - 10) // 2 + (i % 3) * (self.COLOR_BOX_SIZE + 10)
            box_y = self.COLOR_Y_OFFSET + (i // 3) * (self.COLOR_BOX_SIZE + 10)
            box_rect = pygame.Rect(box_x, box_y, self.COLOR_BOX_SIZE, self.COLOR_BOX_SIZE)
            pygame.draw.rect(self.screen, color, box_rect)

    def draw_rounded_rect(self, rect, color, radius):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

