# engine.py
import constant

class GameState:
    def __init__(self):
        self.board = [
            ['r','n','b','q','k','b','n','r'],
            ['p','p','p','p','p','p','p','p'],
            [None]*8, [None]*8, [None]*8, [None]*8,
            ['P','P','P','P','P','P','P','P'],
            ['R','N','B','Q','K','B','N','R'],
        ]
        self.turn = 'w'
        self.castling = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant = None

def get_pseudo_moves(board, r, c, t, en_passant, castling):
    # Chép logic hàm pseudo_moves của bạn vào đây
    pass

def apply_move(board, fr, fc, tr, tc, flag, t):
    # Chép logic hàm apply_move của bạn vào đây
    pass

# Thêm các hàm is_attacked, legal_moves, find_king...