from pygame.sprite import Sprite

class BoardObject(Sprite):

    def __init__(self, group):
        super().__init__(group)
        self.static_rendering = False
        self.is_focused = False
        self.draggable = False
        self.clickable = True
        self.rotatable = False
        self.z_index = 0
        self.rotation = 0

    def update(self):
        pass

    def clicked(self):
        pass

    def holding(self):
        return self

    # TODO: remove this
    def hovering(self):
        self.mark_focused(True)

    def not_hovering(self):
        self.mark_focused(False)

    def mark_focused(self, is_focused):
        if self.is_focused != is_focused:
            self.is_focused = is_focused
            self.create_display()

    def release(self):
        pass

