# ai.py
import time
from src.engine.constant import PIECE_VALUE
from src.engine.rules import all_legal_moves, apply_move, is_white, find_king, is_attacked, legal_moves
from src.utils.opening_book import get_opening_move

class SearchTimeout(Exception):
    """Raised when AI search exceeds its time budget."""
    pass

# ─── HÀM ĐÁNH GIÁ ────────────────────────────────────────────────────────────
# Hybrid (mặc định): neural + PST + heuristic, tự fallback nếu thiếu model
# Chỉ PST:           from src.ai.ai_pst import evaluate
# Chỉ neural:        from src.ai.ai_neural import evaluate
from src.ai.ai_hybrid import evaluate

# ─── BẢNG CHUYỂN VỊ (TRANSPOSITION TABLE) ───────────────────────────────────
# Lưu các vị trí đã tính toán để tránh tính lại
# Key: (board_hash, depth, is_max)  →  Value: (score, best_move, flag)
# flag: 'exact' | 'lower' | 'upper'  (để kết hợp với Alpha-Beta đúng cách)
_tt = {}
TT_MAX_SIZE = 500_000   # Giới hạn bộ nhớ (~50MB)

_eval_cache = {}
EVAL_CACHE_MAX = 200_000

def _hash_board(board):
    """Hash nhanh bàn cờ thành một chuỗi bất biến để làm key."""
    return tuple(p for row in board for p in row)

def _cached_evaluate(board):
    """Cache kết quả evaluate — tránh gọi CNN/PST lặp lại cùng một thế cờ."""
    key = _hash_board(board)
    if key not in _eval_cache:
        if len(_eval_cache) >= EVAL_CACHE_MAX:
            _eval_cache.clear()
        _eval_cache[key] = evaluate(board)
    return _eval_cache[key]


# ─── SẮP XẾP NƯỚC ĐI (MOVE ORDERING) ────────────────────────────────────────
# Thử nước ăn quân và chiếu trước → Alpha-Beta cắt tỉa hiệu quả hơn nhiều
def _move_score(board, fr, fc, tr, tc, flag):
    """Chấm điểm ưu tiên cho một nước đi (càng cao càng thử trước)."""
    score = 0
    target = board[tr][tc]
    mover  = board[fr][fc]
    if target:  # Ăn quân: ưu tiên ăn quân to bằng quân nhỏ (MVV-LVA)
        score += 10 * PIECE_VALUE.get(target.upper(), 0) - PIECE_VALUE.get(mover.upper(), 0)
    if flag == 'castle':
        score += 60   # Nhập thành tốt
    if flag == 'ep':
        score += 105  # Bắt tốt qua đường ~ ăn tốt bằng tốt
    if mover and mover.upper() == 'P' and (tr == 0 or tr == 7):
        score += 800  # Phong cấp
    return score

def order_moves(board, moves):
    """Sắp xếp danh sách nước đi theo điểm ưu tiên giảm dần."""
    return sorted(moves,
                  key=lambda m: _move_score(board, m[0], m[1], m[2], m[3], m[4]),
                  reverse=True)


# ─── MINIMAX + ALPHA-BETA + TRANSPOSITION TABLE ───────────────────────────────
def minimax(board, depth, alpha, beta, is_max, t, en_passant, castling, deadline=None):
    """
    Minimax với Alpha-Beta và Transposition Table.
    Nếu vị trí đã tính ở độ sâu >= depth hiện tại → dùng lại kết quả.
    """
    if deadline and time.time() >= deadline:
        raise SearchTimeout()

    board_key = (_hash_board(board), depth, is_max)

    # ── Tra bảng chuyển vị ──
    if board_key in _tt:
        tt_score, tt_move, tt_flag = _tt[board_key]
        if tt_flag == 'exact':
            return tt_score, tt_move
        if tt_flag == 'lower':
            alpha = max(alpha, tt_score)
        elif tt_flag == 'upper':
            beta = min(beta, tt_score)
        if alpha >= beta:
            return tt_score, tt_move

    if depth == 0:
        return _cached_evaluate(board), None

    moves = all_legal_moves(board, t, en_passant, castling)

    if not moves:
        kr = find_king(board, t)
        if kr and is_attacked(board, kr[0], kr[1], t):
            return (-99999 if is_max else 99999), None
        return 0, None

    moves = order_moves(board, moves)   # Sắp xếp trước khi duyệt
    opp = 'b' if t == 'w' else 'w'
    best_move = moves[0]
    original_alpha = alpha

    if is_max:
        best = float('-inf')
        for fr, fc, tr, tc, flag in moves:
            nb = apply_move(board, fr, fc, tr, tc, flag, t)
            new_ep = (fr+(tr-fr)//2, fc) if board[fr][fc] and board[fr][fc].upper()=='P' and abs(tr-fr)==2 else None
            score, _ = minimax(nb, depth-1, alpha, beta, False, opp, new_ep, castling, deadline)
            if score > best:
                best = score
                best_move = (fr, fc, tr, tc, flag)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
    else:
        best = float('inf')
        for fr, fc, tr, tc, flag in moves:
            nb = apply_move(board, fr, fc, tr, tc, flag, t)
            new_ep = (fr+(tr-fr)//2, fc) if board[fr][fc] and board[fr][fc].upper()=='P' and abs(tr-fr)==2 else None
            score, _ = minimax(nb, depth-1, alpha, beta, True, opp, new_ep, castling, deadline)
            if score < best:
                best = score
                best_move = (fr, fc, tr, tc, flag)
            beta = min(beta, best)
            if beta <= alpha:
                break

    # ── Lưu vào bảng chuyển vị ──
    if len(_tt) < TT_MAX_SIZE:
        if best <= original_alpha:
            flag = 'upper'
        elif best >= beta:
            flag = 'lower'
        else:
            flag = 'exact'
        _tt[board_key] = (best, best_move, flag)

    return best, best_move

def clear_tt():
    """Xóa bảng chuyển vị và cache đánh giá khi bắt đầu ván mới."""
    _tt.clear()
    _eval_cache.clear()


# ─── HÀM GỌI CHÍNH — TÍCH HỢP OPENING BOOK ──────────────────────────────────
def get_best_move(board, depth, t, en_passant, castling, move_history, time_limit=None):
    """
    Hàm duy nhất main.py cần gọi. Ưu tiên theo thứ tự:
      1. Opening book (nếu còn trong sách khai cuộc)
      2. Iterative deepening Minimax (dừng khi hết time_limit nếu có)
    """
    # ── Bước 1: Tra opening book ──
    book_move = get_opening_move(move_history)
    if book_move:
        fr, fc, tr, tc = book_move
        # Kiểm tra nước sách có hợp lệ không (đề phòng)
        valid = legal_moves(board, fr, fc, t, en_passant, castling)
        match = next((m for m in valid if m[0] == tr and m[1] == tc), None)
        if match:
            return (fr, fc, tr, tc, match[2])   # Có trong sách → dùng ngay

    # ── Bước 2: Iterative deepening — dùng kết quả depth trước nếu hết giờ ──
    deadline = time.time() + time_limit if time_limit else None
    best = None
    for d in range(1, depth + 1):
        if deadline and time.time() >= deadline:
            break
        try:
            _, move = minimax(board, d, float('-inf'), float('inf'),
                              t == 'w', t, en_passant, castling, deadline)
            if move:
                best = move
        except SearchTimeout:
            break
    return best