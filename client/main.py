import pygame, sys
from random import randint

class Card(pygame.sprite.Sprite):
    """Represents a card in the game."""
    def __init__(self, back_path, front_path, x, y, width, height, group):
        super().__init__(group)
        self.group = group
        self.original_back_image = pygame.image.load(back_path)
        self.original_front_image = pygame.image.load(front_path)
        self.original_width = width
        self.original_height = height
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.is_front = False
        self.border_thickness = 5
        self.white_space = 15
        self.border_radius = 20
        self.zoom_scale = group.zoom_scale
        self.mouse_pos = (0, 0)
        self.set_image()

    def set_image(self):
        if self.is_front:
            self.image = self.create_combined_image(self.original_front_image)
            self.rect = self.image.get_rect(topleft = self.pos)
        else:
            self.image = self.create_combined_image(self.original_back_image)
            self.rect = self.image.get_rect(topleft = self.pos)

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

    def update(self):
        if self.zoom_scale != self.group.zoom_scale:
            self.zoom_scale = self.group.zoom_scale
            self.set_image()

    def flip(self):
        self.is_front = not self.is_front
        self.set_image()

    def is_clicked(self, mouse_pos):
        """Check if the card was clicked based on the mouse position."""
        rect = pygame.Rect(self.pos[0], self.pos[1], self.width, self.height)
        return rect.collidepoint(mouse_pos)

    def to_json(self):
        return {
            "type": "card",
            "x": self.x,
            "y": self.y
            # "path": "assets/
        }

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.zoom_scale = 1

    def custom_draw(self):
        self.display_surface.fill('#71ddee')

        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft
            self.display_surface.blit(sprite.image,offset_pos)

    def zoom(self, new_zoom_scale):
        self.zoom_scale = new_zoom_scale
        scale_factor = new_zoom_scale
        for sprite in self.sprites():
            sprite.width = sprite.original_width * scale_factor
            sprite.height = sprite.original_height * scale_factor
            center_x = self.display_surface.get_size()[0] // 2
            center_y = self.display_surface.get_size()[1] // 2
            pos_x = center_x + (sprite.x - center_x) * scale_factor
            pos_y = center_y + (sprite.y - center_y) * scale_factor
            sprite.pos = (pos_x, pos_y)


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
        self.camera_group = CameraGroup()
        self.font = pygame.font.SysFont(None, 36)
        self.moving_around_board = False

        for i in range(10):
            for j in range(10):
                hero = "tomoe-gozen"
                back_path = f"assets/{hero}/back.webp"
                front_path = f"assets/{hero}/deck/3x-skirmish.png"
                card = Card(back_path, front_path, 230*i, 329*j, 230, 329, self.camera_group)


    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.camera_group.update()
            self.camera_group.custom_draw()
            pygame.display.update()
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
        if event.type == pygame.MOUSEMOTION:
            self.camera_group.mouse_pos = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            self.handle_zoom(event)
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
                    for card in self.camera_group.sprites():
                        if card.is_clicked(mouse_pos):
                            card.flip()
        elif event.type == pygame.MOUSEMOTION and self.moving_around_board:
            pass

    def handle_zoom(self, event):
        new_zoom = self.camera_group.zoom_scale + event.y * 0.03
        if 0.2 < new_zoom < 2.0:
            self.camera_group.zoom(new_zoom)

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()

g = Game()
g.run()

