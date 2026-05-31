# game_state.py — Trạng thái ván đấu (dữ liệu thuần, không chứa logic)

class GameState:
    def __init__(self):
        self.board = [
            ['r','n','b','q','k','b','n','r'],
            ['p','p','p','p','p','p','p','p'],
            [None]*8, [None]*8, [None]*8, [None]*8,
            ['P','P','P','P','P','P','P','P'],
            ['R','N','B','Q','K','B','N','R'],
        ]
        self.turn        = 'w'
        self.castling    = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant  = None
        self.move_history = []