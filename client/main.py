import pygame

class Picture:
    """Represents a picture in the game."""
    def __init__(self, path, x, y, width, height):
        self.original_image = pygame.image.load(path)
        self.image = pygame.transform.scale(self.original_image, (width, height))
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def update(self):
        """Update logic for the picture (if needed)."""
        pass

    def render(self, screen, dx, dy):
        """Draw the picture on the screen."""
        screen.blit(self.image, (self.x + dx, self.y + dy))

    def set_scale(self, scale_factor):
        """Scale the image based on the zoom level."""
        new_size = (int(self.width * scale_factor), int(self.height * scale_factor))
        self.image = pygame.transform.scale(self.original_image, new_size)

    def to_json():
        return {
            "type": "picture",
            "x": self.x,
            "y": self.y,
            # "path": self.path
        }

class Card:
    """Represents a card in the game."""
    def __init__(self, back_path, front_path, x, y, width, height):
        self.original_back_image = pygame.image.load(back_path)
        self.original_front_image = pygame.image.load(front_path)
        self.back_image = pygame.transform.scale(self.original_back_image, (width, height))
        self.front_image = pygame.transform.scale(self.original_front_image, (width, height))
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_front = False
        self.border_thickness = 5  # Thickness of the border
        self.white_space = 15  # Space between the card and the border

    def update(self):
        """Update logic for the card (if needed)."""
        pass

    def render(self, screen, dx, dy):
        """Draw the card on the screen with a rounded black border and white spacing."""
        # Draw the card
        if self.is_front:
            screen.blit(self.front_image, (self.x + dx, self.y + dy))
        else:
            screen.blit(self.back_image, (self.x + dx, self.y + dy))

        # Draw outline
        border_x = self.x + dx - self.border_thickness
        border_y = self.y + dy - self.white_space - self.border_thickness
        rounded_rect_surface = pygame.Surface((self.width + 2 * self.border_thickness, 
                                                self.height + 2 * self.white_space + self.border_thickness), 
                                               pygame.SRCALPHA)
        pygame.draw.rect(rounded_rect_surface, (0, 0, 0), 
                         (0, 0, rounded_rect_surface.get_width(), rounded_rect_surface.get_height()), 
                         width=self.border_thickness, border_radius=20)
        screen.blit(rounded_rect_surface, (border_x, border_y))


    def set_scale(self, scale_factor):
        """Scale the image based on the zoom level."""
        new_size = (int(self.width * scale_factor), int(self.height * scale_factor))
        self.back_image = pygame.transform.scale(self.original_back_image, new_size)
        self.front_image = pygame.transform.scale(self.original_front_image, new_size)

    def is_clicked(self, mouse_pos, dx, dy):
        """Check if the card was clicked based on the mouse position."""
        rect = pygame.Rect(self.x + dx, self.y + dy, self.width, self.height)
        return rect.collidepoint(mouse_pos)

    def to_json(self):
        return {
            "type": "card",
            "x": self.x,
            "y": self.y
            # "path": "assets/
        }

class Game:
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60  # Adjust FPS for smoother gameplay
    CLICKED_OBJECT_SCALE = 1.1

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Boardshinx")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "playing"  # Simple state system to handle menus, etc.

        # Initialize game objects
        self.game_objects = []

        # Create and add the centered rectangle to game_objects
        # rect_width = 1337
        # rect_height = 866
        # rect_x = (self.WINDOW_WIDTH - rect_width) // 2
        # rect_y = (self.WINDOW_HEIGHT - rect_height) // 2
        # rectangle = Picture("assets/sarpedon.webp", rect_x, rect_y, rect_width, rect_height)
        # self.game_objects.append(rectangle)
        card = Card("assets/medusa/back.webp", "assets/medusa/deck/3x-dash.png", 0, 0, 250, 349)
        self.game_objects.append(card)

        # Initialize font for displaying mouse coordinates
        self.font = pygame.font.SysFont(None, 36)  # Default font and size

        # Initialize mouse position variables
        self.prev_mouse_x, self.prev_mouse_y = pygame.mouse.get_pos()
        self.sum_dx = 0
        self.sum_dy = 0
        self.moving_around_board = False  # Track whether the mouse button is held down
        self.zoom_scale = 1.0  # Initialize zoom scale

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.WINDOW_WIDTH, self.WINDOW_HEIGHT = event.w, event.h
            self.handle_input(event)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.MOUSEWHEEL:
            # Zoom in and out
            if event.y > 0 and self.zoom_scale < 2.0:  # Scroll up
                self.zoom_scale *= 1.1  # Zoom in
            elif event.y < 0 and self.zoom_scale > 0.2:  # Scroll down
                self.zoom_scale /= 1.1  # Zoom out
            # Scale all game objects based on the zoom level
            for obj in self.game_objects:
                obj.set_scale(self.zoom_scale)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and pygame.key.get_mods() & pygame.KMOD_ALT:
                self.moving_around_board = True
                self.prev_mouse_x, self.prev_mouse_y = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.moving_around_board:
                    self.moving_around_board = False
                else:
                    mouse_pos = event.pos
                    # Check if the card was clicked
                    card = self.game_objects[0]
                    if card.is_clicked(mouse_pos, self.sum_dx, self.sum_dy):
                        card.is_front = not card.is_front  # Flip the card on click
                        print("Card clicked!")

    def update(self):
        if self.state == "playing":
            for obj in self.game_objects:
                obj.update()

            if self.moving_around_board:
                current_mouse_x, current_mouse_y = pygame.mouse.get_pos()

                self.sum_dx += (current_mouse_x - self.prev_mouse_x) / 1.3
                self.sum_dy += (current_mouse_y - self.prev_mouse_y) / 1.3

                self.prev_mouse_x = current_mouse_x
                self.prev_mouse_y = current_mouse_y

    def render(self):
        self.screen.fill((255, 255, 255))

        if self.state == "playing":
            for obj in self.game_objects:
                obj.render(self.screen, self.sum_dx, self.sum_dy)

            mouse_x, mouse_y = pygame.mouse.get_pos()

            coord_text = f"({mouse_x - self.sum_dx}, {mouse_y - self.sum_dy}), Zoom: {self.zoom_scale}"
            coord_surface = self.font.render(coord_text, True, (0, 0, 0))
            self.screen.blit(coord_surface, (10, 10))

        pygame.display.flip()  # Update the display

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()

g = Game()
g.run()

