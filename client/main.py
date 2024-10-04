import os
import pygame, sys
from random import randint
from functools import lru_cache
import random

class Card(pygame.sprite.Sprite):

    """Represents a card in the game."""
    def __init__(self, back_path, front_path, x, y, width, height, group):
        super().__init__(group)
        self.group = group
        self.back_image_path = back_path
        self.front_image_path = front_path

        self.original_width = width
        self.original_height = height
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.is_front = random.choice([False] * 5 + [False])
        self.zoom_scale = group.zoom_scale
        self.mouse_pos = (0, 0)
        self.z_index = 0
        self.set_image()

    def set_image(self):
        if self.is_front:
            self.image = Card.create_combined_image(self.front_image_path, self.width, self.height)
            self.rect = self.image.get_rect(topleft = self.pos)
        else:
            self.image = Card.create_combined_image(self.back_image_path, self.width, self.height)
            self.rect = self.image.get_rect(topleft = self.pos)

    @staticmethod
    @lru_cache(maxsize=256)
    def create_combined_image(image_path, width, height):
        """Create a new image combining the original image and its outline."""
        border_thickness = 5
        white_space = 15
        border_radius = 20
        image = pygame.image.load(image_path).convert_alpha()
        scaled_image = pygame.transform.smoothscale(image, (width, height))
        combined_surface = pygame.Surface((width + 2 * border_thickness, 
                                            height + 2 * white_space + border_thickness), 
                                           pygame.SRCALPHA)
        
        # Draw a filled rectangle with rounded corners
        pygame.draw.rect(combined_surface, (255, 255, 255),  # White fill
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         border_radius=border_radius)
        
        # Draw the border
        pygame.draw.rect(combined_surface, (0, 0, 0),  # Black border
                         (0, 0, combined_surface.get_width(), combined_surface.get_height()), 
                         width=border_thickness, border_radius=border_radius)
        
        combined_surface.blit(scaled_image, (border_thickness, white_space))
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
        self.rel_x = 0
        self.rel_y = 0

    def custom_draw(self):
        self.display_surface.fill('#71ddee')

        screen_rect = self.display_surface.get_rect()
        s = 0
        for sprite in sorted(self.sprites(), key= lambda x : x.z_index):
            if screen_rect.colliderect(sprite.rect):
                s += 1
                offset_pos = sprite.rect.topleft
                self.display_surface.blit(sprite.image,offset_pos)
        print(s)

    def zoom(self, new_zoom_scale):
        self.zoom_scale = new_zoom_scale
        scale_factor = new_zoom_scale
        center_x = self.display_surface.get_size()[0] // 2 - self.rel_x
        center_y = self.display_surface.get_size()[1] // 2 - self.rel_y
        for sprite in self.sprites():
            sprite.width = sprite.original_width * scale_factor
            sprite.height = sprite.original_height * scale_factor
            pos_x = center_x + (sprite.x - center_x) * scale_factor + self.rel_x
            pos_y = center_y + (sprite.y - center_y) * scale_factor + self.rel_y
            sprite.pos = (pos_x, pos_y)

    def move_camera(self, rel):
        rel2 = (rel[0] / self.zoom_scale, rel[1] / self.zoom_scale)
        self.rel_x += rel2[0]
        self.rel_y += rel2[1]
        for sprite in self.sprites():
            sprite.rect.move_ip(rel)
            sprite.pos = sprite.rect.topleft

    def move_sprite(self, sprite, rel):
        sprite.rect.move_ip(rel)
        sprite.x += rel[0]
        sprite.y += rel[1]
        sprite.pos = sprite.rect.topleft

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

        self.is_holding_object = False
        self.moved_holding_object = False
        self.held_object = None
        self.z_index_iota = 0

        v = 2
        with open('assets/all_cards.txt', 'r') as file:
            all_cards_front = [f.strip() for f in file.readlines()][:1]
        with open('assets/all_back.txt', 'r') as file:
            all_cards_back = [f.strip() for f in file.readlines()]
        # hero = "tomoe-gozen"
        # deck = [f for f in os.listdir(f"assets/{hero}/deck/")]
        for i in range(v):
            for j in range(v):
                back_path = f"assets/{random.choice(all_cards_back)}"
                front_path = f"assets/{random.choice(all_cards_front)}"
                card = Card(back_path, front_path, 230*i, 329*j, 230 / 1.4, 329 / 1.4, self.camera_group)
                # index = j + i * v
                # back_path = f"assets/{hero}/back.webp"
                # front_path = f"assets/{hero}/deck/{deck[index % len(deck)]}"


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
            if self.moving_around_board and pygame.key.get_mods() & pygame.KMOD_ALT:
                self.camera_group.move_camera(event.rel)
            if self.is_holding_object and self.held_object is not None:
                self.moved_holding_object = True
                self.camera_group.move_sprite(self.held_object, event.rel)
        elif event.type == pygame.MOUSEWHEEL:
            self.handle_zoom(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and pygame.key.get_mods() & pygame.KMOD_ALT:
                self.moving_around_board = True
            elif event.button == 1:
                self.is_holding_object = True
                mouse_pos = event.pos
                for obj in sorted(self.camera_group.sprites(), key=lambda x: -x.z_index):
                    if obj.is_clicked(mouse_pos):
                        self.assign_z_index(obj)
                        self.held_object = obj
                        break
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.is_holding_object:
                    if not self.moved_holding_object:
                        mouse_pos = event.pos
                        # Check if the card was clicked
                        for obj in sorted(self.camera_group.sprites(), key=lambda x: -x.z_index):
                            if obj.is_clicked(mouse_pos):
                                self.assign_z_index(obj)
                                obj.flip()
                                break
                    self.is_holding_object = False
                    self.held_object = None
                    self.moved_holding_object = False
                elif self.moving_around_board:
                    self.moving_around_board = False
        elif event.type == pygame.MOUSEMOTION and self.moving_around_board:
            pass

    def assign_z_index(self, obj):
        obj.z_index = self.z_index_iota
        self.z_index_iota += 1

    def handle_zoom(self, event):
        new_zoom = self.camera_group.zoom_scale + event.y * 0.05
        if 0.2 < new_zoom < 2.0:
            self.camera_group.zoom(new_zoom)

    def quit(self):
        """Quit the game and clean up resources."""
        pygame.quit()

g = Game()
g.run()

