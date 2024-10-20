import pygame
from .main_menu import MainMenu
from .join_room import JoinRoom
from .board_state import BoardState, BoardStateType
from .game import Game

class BoardShinx:
    WINDOW_WIDTH = 740
    WINDOW_HEIGHT = 983

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Boardshinx")
        self.state = BoardStateType.MAIN_MENU
        self.states = {
            BoardStateType.MAIN_MENU: MainMenu,
            BoardStateType.JOIN_ROOM: JoinRoom,
            BoardStateType.GAME: Game
        }

    def set_state(self, new_state):
        self.state = new_state

    def get_state(self):
        return self.state

    def run(self):
        data = None
        while True:
            state_obj = self.states[self.state](self, data)
            data = state_obj.entry()

