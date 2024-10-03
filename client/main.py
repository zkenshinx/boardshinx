import pygame

class Picture:
    """Represents a picture in the game."""
    def __init__(self, path, x, y, width, height):
        self.image = pygame.image.load(path)
        self.image = pygame.transform.scale(self.image, (width, height))
        self.x = x
        self.y = y

    def update(self):
        """Update logic for the picture (if needed)."""
        pass

    def render(self, screen, dx, dy):
        """Draw the picture on the screen."""
        screen.blit(self.image, (self.x + dx, self.y + dy))

class Rectangle:
    """Represents a rectangle in the game."""
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def update(self):
        """Update logic for the rectangle (if needed)."""
        pass

    def render(self, screen, dx, dy):
        """Draw the rectangle on the screen."""
        pygame.draw.rect(screen, self.color, (self.x + dx, self.y + dy, self.width, self.height))

class Game:
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60  # Adjust FPS for smoother gameplay

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
        rect_width = 1337 / 1.5
        rect_height = 866 / 1.5
        rect_x = (self.WINDOW_WIDTH - rect_width) // 2
        rect_y = (self.WINDOW_HEIGHT - rect_height) // 2
        rectangle = Picture("assets/sarpedon.webp", rect_x, rect_y, rect_width, rect_height)
        self.game_objects.append(rectangle)

        # Initialize font for displaying mouse coordinates
        self.font = pygame.font.SysFont(None, 36)  # Default font and size

        # Initialize mouse position variables
        self.prev_mouse_x, self.prev_mouse_y = pygame.mouse.get_pos()
        self.sum_dx = 0
        self.sum_dy = 0
        self.mouse_held = False  # Track whether the mouse button is held down

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
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.mouse_held = True
                self.prev_mouse_x, self.prev_mouse_y = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_held = False

    def update(self):
        if self.state == "playing":
            for obj in self.game_objects:
                obj.update()

            if self.mouse_held:
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

            coord_text = f"({mouse_x - self.sum_dx}, {mouse_y - self.sum_dy})"
            coord_surface = self.font.render(coord_text, True, (0, 0, 0))
            self.screen.blit(coord_surface, (10, 10))

        pygame.display.flip()  # Update the display

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()

g = Game()
g.run()
