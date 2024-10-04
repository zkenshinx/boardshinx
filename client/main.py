import pygame, sys
from random import randint

# class Picture:
#     """Represents a picture in the game."""
#     def __init__(self, path, x, y, width, height):
#         self.original_image = pygame.image.load(path)
#         self.image = pygame.transform.scale(self.original_image, (width, height))
#         self.x = x
#         self.y = y
#         self.width = width
#         self.height = height
# 
#     def update(self):
#         """Update logic for the picture (if needed)."""
#         pass
# 
#     def render(self, screen, dx, dy):
#         """Draw the picture on the screen."""
#         screen.blit(self.image, (self.x + dx, self.y + dy))
# 
#     def set_scale(self, scale_factor):
#         """Scale the image based on the zoom level."""
#         new_size = (int(self.width * scale_factor), int(self.height * scale_factor))
#         self.image = pygame.transform.scale(self.original_image, new_size)
# 
#     def to_json():
#         return {
#             "type": "picture",
#             "x": self.x,
#             "y": self.y,
#             # "path": self.path
#         }


class Card:
    """Represents a card in the game."""
    def __init__(self, back_path, front_path, x, y, width, height):
        self.original_back_image = pygame.image.load(back_path)
        self.original_front_image = pygame.image.load(front_path)
        self.original_width = width
        self.original_height = height
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.is_front = False
        self.border_thickness = 5
        self.white_space = 15
        self.border_radius = 20
        self.create_images()

    def create_images(self):
        self.back_image = self.create_combined_image(self.original_back_image)
        self.front_image = self.create_combined_image(self.original_front_image)

    def create_combined_image(self, original_image):
        """Create a new image combining the original image and its outline."""
        scaled_image = pygame.transform.smoothscale(original_image, (self.width, self.height))
        combined_surface = pygame.Surface((self.width + 2 * self.border_thickness, 
                                            self.height + 2 * self.white_space + self.border_thickness), 
                                           pygame.SRCALPHA)
        
        # Draw a filled rectangle with rounded corners
        pygame.draw.rect(combined_surface, (255, 255, 255),  # White fill
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         border_radius=self.border_radius)
        
        # Draw the border
        pygame.draw.rect(combined_surface, (0, 0, 0),  # Black border
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         width=self.border_thickness, border_radius=self.border_radius)
        
        combined_surface.blit(scaled_image, (self.border_thickness, self.white_space))
        return combined_surface

    # ... (rest of the methods remain unchanged)
    def update(self):
        """Update logic for the card (if needed)."""
        pass

    def render(self, screen, dx, dy):
        """Draw the card on the screen."""
        if self.is_front:
            screen.blit(self.front_image, (self.x + dx, self.y + dy))
        else:
            screen.blit(self.back_image, (self.x + dx, self.y + dy))

    def set_scale(self, scale_factor):
        """Scale the image based on the zoom level."""
        self.width = self.original_width * scale_factor
        self.height = self.original_height * scale_factor
        self.create_images()

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
    FPS = 60
    CLICKED_OBJECT_SCALE = 1.1

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Boardshinx")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "playing"

        # Initialize game objects
        self.game_objects = []

        # Create and add the centered rectangle to game_objects
        # rect_width = 1337
        # rect_height = 866
        # rect_x = (self.WINDOW_WIDTH - rect_width) // 2
        # rect_y = (self.WINDOW_HEIGHT - rect_height) // 2
        # rectangle = Picture("assets/sarpedon.webp", rect_x, rect_y, rect_width, rect_height)
        # self.game_objects.append(rectangle)
        for i in range(1):
            for j in range(1):
                hero = "tomoe-gozen"
                card = Card(f"assets/{hero}/back.webp", f"assets/{hero}/deck/3x-skirmish.png", 230*i, 329*j, 230, 329)
                self.game_objects.append(card)

        # Initialize font for displaying mouse coordinates
        self.font = pygame.font.SysFont(None, 36)  # Default font and size

        # Initialize mouse position variables
        self.sum_dx = 0
        self.sum_dy = 0
        self.moving_around_board = False
        self.zoom_scale = 1.0

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
                    for card in self.game_objects:
                        if card.is_clicked(mouse_pos, self.sum_dx, self.sum_dy):
                            card.is_front = not card.is_front  # Flip the card on click
        elif event.type == pygame.MOUSEMOTION and self.moving_around_board:
            self.sum_dx += event.rel[0]
            self.sum_dy += event.rel[1]

    def update(self):
        if self.state == "playing":
            for obj in self.game_objects:
                obj.update()

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

