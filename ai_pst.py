# ai_pst.py
# Hàm evaluate() dựa trên PST thủ công — fallback khi chưa có chess_model.pt
# Dùng bằng cách sửa ai.py: from ai_pst import evaluate

from constant import PIECE_VALUE, PST_OPENING, PST_ENDGAME
from engine import is_white


def get_phase(board):
    total = 0
    for row in board:
        for p in row:
            if p and p.upper() not in ('K', 'P'):
                total += PIECE_VALUE[p.upper()]
    return max(0.0, min(1.0, total / 7800))


def evaluate(board):
    phase = get_phase(board)
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p:
                continue
            pt    = p.upper()
            white = is_white(p)
            idx   = r * 8 + c if white else (7 - r) * 8 + c
            val   = PIECE_VALUE[pt]
            o = PST_OPENING.get(pt)
            e = PST_ENDGAME.get(pt)
            if o and e:
                val += int(o[idx] * phase + e[idx] * (1 - phase))
            elif o:
                val += o[idx]
            score += val if white else -val
    return score
