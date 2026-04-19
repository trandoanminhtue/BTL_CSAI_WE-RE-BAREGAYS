# ai.py
import math
from constant import PIECE_VALUE, PST
from engine import all_legal_moves, apply_move, is_white, is_black, is_own, is_opp, in_bounds, find_king, is_attacked

# ─── 📊 THÀNH PHẦN 3: HÀM ĐÁNH GIÁ (CHI TIẾT) ──────────────────────────────────
def evaluate(board):
    """Tính toán điểm số bàn cờ: Dương có lợi cho Trắng, Âm có lợi cho Đen."""
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p: continue
            pt = p.upper()
            white = is_white(p)
            # Tính chỉ số index trong mảng PST 64 ô
            idx = r * 8 + c if white else (7 - r) * 8 + c
            val = PIECE_VALUE[pt]
            # Cộng điểm vật chất + điểm vị trí
            if pt in PST:
                val += PST[pt][idx]
            score += val if white else -val
    return score

# ─── 🔍 THÀNH PHẦN 4: THUẬT TOÁN TÌM KIẾM (MINIMAX + ALPHA-BETA) ───────────────
def minimax(board, depth, alpha, beta, is_max, t, en_passant, castling):
    """Thuật toán tìm kiếm nước đi tối ưu bằng cách duyệt cây quyết định."""
    if depth == 0:
        return evaluate(board), None

    moves = all_legal_moves(board, t, en_passant, castling)

    # Kiểm tra trạng thái kết thúc (Chiếu hết hoặc Hòa)
    if not moves:
        kr = find_king(board, t)
        if kr and is_attacked(board, kr[0], kr[1], t):
            return (-99999 if is_max else 99999), None # Thua
        return 0, None  # Hòa

    opp = 'b' if t == 'w' else 'w'
    best_move = moves[0]

    if is_max: # Nhánh của người chơi muốn tối đa hóa điểm (Trắng)
        best = float('-inf')
        for fr, fc, tr, tc, flag in moves:
            nb = apply_move(board, fr, fc, tr, tc, flag, t)
            # Logic cập nhật trạng thái en_passant cho lượt sau
            new_ep = (fr + (tr - fr) // 2, fc) if board[fr][fc] and board[fr][fc].upper() == 'P' and abs(tr - fr) == 2 else None
            score, _ = minimax(nb, depth-1, alpha, beta, False, opp, new_ep, castling)
            if score > best:
                best = score
                best_move = (fr, fc, tr, tc, flag)
            alpha = max(alpha, best)
            if beta <= alpha: break # Cắt tỉa Alpha-Beta
        return best, best_move
    else: # Nhánh của người chơi muốn tối thiểu hóa điểm (Đen/AI)
        best = float('inf')
        for fr, fc, tr, tc, flag in moves:
            nb = apply_move(board, fr, fc, tr, tc, flag, t)
            new_ep = (fr + (tr - fr) // 2, fc) if board[fr][fc] and board[fr][fc].upper() == 'P' and abs(tr - fr) == 2 else None
            score, _ = minimax(nb, depth-1, alpha, beta, True, opp, new_ep, castling)
            if score < best:
                best = score
                best_move = (fr, fc, tr, tc, flag)
            beta = min(beta, best)
            if beta <= alpha: break # Cắt tỉa Alpha-Beta
        return best, best_move