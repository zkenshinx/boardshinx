import pygame

from random import randint

class OngoingMove:
    def __init__(self, start_pos, end_pos, count, move_obj, game, callback_fn=None):
        self.game = game
        self.start_pos = pygame.Vector2(*start_pos)
        self.end_pos = pygame.Vector2(*end_pos)
        self.count = count
        self.current_count = 0
        self.move_obj = move_obj
        self.callback_fn = callback_fn

    def lerp(self, t):
        return self.start_pos + (self.end_pos - self.start_pos) * t

    def update(self):
        self.current_count += 1
        if self.is_finished():
            pos = self.end_pos
        else:
            t = self.current_count / self.count 
            pos = self.lerp(t)
        self.game.transform_manager.move_sprite_to(self.move_obj, pos.x, pos.y)

    def is_finished(self):
        if self.current_count >= self.count:
            if self.callback_fn is not None:
                self.callback_fn(self.move_obj)
            return True
        return False

class OngoingShuffle:
    def __init__(self, holder, game):
        self.game = game
        self.holder = holder
        self.step = 0
        self.step_counter = 0

        # Initial step
        images_for_animation = 10
        self.top_images = []
        for i in range(images_for_animation):
            top_image = self.holder.pop_image(send_message=False)
            if top_image is None:
                break
            next = self.generate_random_next_coordinate()
            self.game.transform_manager.move_sprite_to(top_image, *next)
            self.top_images.append(top_image)
            self.game.assign_z_index(top_image)

    def generate_random_next_coordinate(self):
        diff_left = int(-self.holder.world_rect.width * 0.9)
        diff_right = int(self.holder.world_rect.width * 0.2)
        center = self.holder.world_rect.center
        next_x = center[0] + randint(diff_left, diff_right)
        next_y = center[1] + randint(diff_left, diff_right)
        return next_x, next_y

    def update(self):
        limit = 10
        if self.step_counter % limit == 0:
            self.step += 1
            if self.step == 6:
                return
            for image in self.top_images:
                if self.step == 5:
                    dest = self.holder.world_rect.topleft
                else:
                    dest = self.generate_random_next_coordinate()
                ongoing_event = OngoingMove(image.world_rect.topleft, dest, limit, image, self.game, None)
                self.game.add_ongoing(ongoing_event)
        self.step_counter += 1

    def is_finished(self):
        if self.step >= 6:
            for image in self.top_images:
                self.holder.add_image(image, False)
            return True

class OngoingRoll:
    def __init__(self, dice, result, game):
        self.game = game
        self.dice = dice
        self.result = result
        self.step = 0
        self.start_rect = self.dice.world_rect.copy()

    def generate_random_next_coordinate(self):
        diff_left = int(-self.start_rect.width * 0.1)
        diff_right = int(self.start_rect.width * 0.1)
        topleft = self.start_rect.topleft
        next_x = topleft[0] + randint(diff_left, diff_right)
        next_y = topleft[1] + randint(diff_left, diff_right)
        return next_x, next_y

    def update(self):
        self.step += 1
        if self.step % 3 == 0:
            dest = self.generate_random_next_coordinate()
            self.game.transform_manager.move_sprite_to(self.dice, *dest)
            self.dice.set_random()

    def is_finished(self):
        if self.step >= 50:
            self.game.transform_manager.move_sprite_to(self.dice, self.start_rect.x, self.start_rect.y)
            self.dice.set_specific(self.result)
            return True
        return False
