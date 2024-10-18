from enum import Enum

class BoardStateType(Enum):
    MAIN_MENU = 1
    JOIN_ROOM = 2
    CREATE_ROOM = 3
    GAME = 4

class BoardState:
    def __init__(self, state_manager):
        self.state_manager = state_manager

    def entry(self, data=None):
        pass

