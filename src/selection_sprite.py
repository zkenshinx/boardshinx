import pygame

from src.board_object import BoardObject

class Selection(BoardObject):

    PHASE_NONE = 0
    PHASE_SELECTING = 1
    PHASE_SELECTED = 2

    def __init__(self, color, group, game):
        super().__init__(group)
        self.r, self.g, self.b = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        self.game = game
        self.z_index = 0
        self.render = False
        self._type = "selection"
        self.rotation = 0
        self.world_start_pos = (0, 0)
        self.world_end_pos = (0, 0)
        self.selected_objects = []
        self.phase = Selection.PHASE_NONE
        self.world_rect = pygame.rect.Rect(0, 0, 0, 0)
        self.screen_rect = self.world_rect.copy()
        self.clickable = False
        self.update()

    def update(self):
        self.display = self.create_display()

    def create_display(self):
        surface = None
        scale = self.game.camera.zoom_scale
        world_width = abs(self.world_end_pos[0] - self.world_start_pos[0])
        world_height = abs(self.world_end_pos[1] - self.world_start_pos[1])
        if self.phase == Selection.PHASE_SELECTING:

            screen_width = world_width * scale
            screen_height = world_height * scale
            surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

            surface.fill((self.r, self.g, self.b, 50))
            pygame.draw.rect(surface, (self.r, self.g, self.b), (0, 0, screen_width, screen_height), 2)

            x = min(self.world_start_pos[0], self.world_end_pos[0])
            y = min(self.world_start_pos[1], self.world_end_pos[1])
            self.world_rect = pygame.rect.Rect(x, y, world_width, world_height)
            self.screen_rect = pygame.rect.Rect(x, y, screen_width, screen_height)
        elif self.phase == Selection.PHASE_SELECTED:
            min_x = min(sprite.world_rect.topleft[0] for sprite in self)
            min_y = min(sprite.world_rect.topleft[1] for sprite in self)
            max_x = max(sprite.world_rect.bottomright[0] for sprite in self)
            max_y = max(sprite.world_rect.bottomright[1] for sprite in self)
            width = (max_x - min_x)
            height = (max_y - min_y)
            surface = pygame.Surface((width, height), pygame.SRCALPHA)

            for sprite in self:
                rect = sprite.world_rect.copy().move(-min_x, -min_y)
                surface.fill((self.r, self.g, self.b, 125), rect)
            self.world_start_pos = (min_x, min_y)
            self.world_end_pos = (max_x, max_y)
            self.world_rect = pygame.rect.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            scaled_surface = pygame.transform.scale(surface, (width * scale, height * scale))
            self.screen_rect = scaled_surface.get_rect(topleft=(min_x, min_y))
            return scaled_surface
        else:
            return None

        return surface

    def clicked(self):
        for sprite in self:
            sprite.clicked()
            self.game.assign_z_index(sprite)
        self.reset()

    def holding(self):
        self.game.moved_holding_object = True
        p = self.game.camera.mouse_pos()

        scale = self.game.camera.zoom_scale
        min_x = min(sprite.screen_rect.topleft[0] for sprite in self)
        min_y = min(sprite.screen_rect.topleft[1] for sprite in self)
        max_x = max(sprite.screen_rect.bottomright[0] for sprite in self)
        max_y = max(sprite.screen_rect.bottomright[1] for sprite in self)
        width = (max_x - min_x) / scale
        height = (max_y - min_y) / scale

        rect = pygame.rect.Rect(min_x, min_y, width, height)
        center = rect.center

        for sprite in self:
            to_x = p[0] - center[0] + sprite.screen_rect.center[0]
            to_y = p[1] - center[1] + sprite.screen_rect.center[1]
            self.game.transform_manager.move_sprite_to_centered(sprite, to_x, to_y)
            self.game.assign_z_index(sprite)
        return self

    def mark_focused(self, is_focused):
        pass

    def start_selection(self):
        self.world_start_pos = self.game.camera.mouse_pos()
        self.world_end_pos = self.world_start_pos
        self.render = True
        self.phase = Selection.PHASE_SELECTING

    def finish_selection(self):
        self.phase = Selection.PHASE_SELECTED
        self.selected_objects.clear()
        for sprite in self.game.GIP.get_rendered_objects():
            if sprite == self or not sprite.draggable:
                continue
            elif self.game.collision_manager.colliderect(self.world_rect, sprite.world_rect):
                self.selected_objects.append(sprite)
        if len(self) == 0:
            self.reset()

    def reset(self):
        self.selected_objects.clear()
        self.render = False
        self.phase = Selection.PHASE_NONE

    def __len__(self):
        return len(self.selected_objects)

    def __contains__(self, item):
        return item in self.selected_objects

    def __iter__(self):
        return iter(self.selected_objects)

