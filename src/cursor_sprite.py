import pygame

from src.board_object import BoardObject

class Cursor(BoardObject):
    """Represents a cursor in the game."""
    def __init__(self, name, color, group, game):
        super().__init__(group)
        self.name = name
        self.color = self.hex_to_rgb(color)
        self.game = game
        self.group = group
        self.z_index = float('inf')
        self.render = True
        self._type = "cursor"
        self.rotation = 0

        self.cursor_image = pygame.image.load("cursor.svg").convert_alpha()

        self.size = (15, 20)
        self.world_rect = pygame.Rect(0, 0, *self.size)
        self.screen_rect = pygame.Rect(0, 0, *self.size)

        self.update()

    def update(self):
        self.display = pygame.Surface(self.size, pygame.SRCALPHA)
        scaled_cursor = pygame.transform.smoothscale(self.cursor_image, self.size)
        self.display.blit(scaled_cursor, (0, 0))
        self.apply_color_to_surface(self.display, self.color)

    def apply_color_to_surface(self, surface, color):
        w, h = surface.get_size()
        r, g, b = color
        for x in range(w):
            for y in range(h):
                a = surface.get_at((x, y))[3]
                surface.set_at((x, y), (r, g, b, a))

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def mark_focused(self, is_focused):
        pass
