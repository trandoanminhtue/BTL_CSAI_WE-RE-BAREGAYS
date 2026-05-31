# rules.py — Luật cờ: sinh nước đi, kiểm tra hợp lệ, thực thi nước đi

from src.engine.constant import PIECE_VALUE


# ─── TIỆN ÍCH ────────────────────────────────────────────────────────────────

def is_white(p):    return p and p.isupper()
def is_black(p):    return p and p.islower()
def is_own(p, t):   return is_white(p) if t == 'w' else is_black(p)
def is_opp(p, t):   return is_white(p) if t == 'b' else is_black(p)
def in_bounds(r, c): return 0 <= r < 8 and 0 <= c < 8

def find_king(board, t):
    """Trả về (row, col) của vua phe t, hoặc None nếu không tìm thấy."""
    k = 'K' if t == 'w' else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c] == k:
                return (r, c)
    return None


# ─── SINH NƯỚC ĐI ────────────────────────────────────────────────────────────

def pseudo_moves(board, r, c, t, en_passant, castling):
    """Sinh tất cả nước đi lý thuyết — chưa lọc trường hợp vua bị chiếu."""
    p = board[r][c]
    if not p or not is_own(p, t):
        return []

    pt    = p.upper()
    moves = []

    def add(nr, nc, flag=None):
        if in_bounds(nr, nc) and not is_own(board[nr][nc], t):
            moves.append((nr, nc, flag))

    if pt == 'P': #quân tốt
        d     = -1 if is_white(p) else 1
        start =  6 if is_white(p) else 1

        if in_bounds(r+d, c) and not board[r+d][c]:
            moves.append((r+d, c, None))
            if r == start and not board[r+d*2][c]:
                moves.append((r+d*2, c, None))
        #ăn chéo
        for dc in (-1, 1):
            nr, nc = r+d, c+dc
            if in_bounds(nr, nc):
                if is_opp(board[nr][nc], t):
                    moves.append((nr, nc, None))
                elif en_passant and (nr, nc) == en_passant:
                    moves.append((nr, nc, 'ep'))

    elif pt == 'N':#quân mã
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            add(r+dr, c+dc)

    if pt in ('B', 'Q'):#tượng + hậu (đi chéo)
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            while in_bounds(nr, nc):
                if is_own(board[nr][nc], t): break
                moves.append((nr, nc, None))
                if board[nr][nc]: break
                nr += dr; nc += dc

    if pt in ('R', 'Q'):#xe + hậu (đi ngang ngược)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            while in_bounds(nr, nc):
                if is_own(board[nr][nc], t): break
                moves.append((nr, nc, None))
                if board[nr][nc]: break
                nr += dr; nc += dc

    if pt == 'K':#vua
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            add(r+dr, c+dc)
        _castle_moves(board, r, c, t, castling, moves)

    return moves

#nhập thành
def _castle_moves(board, r, c, t, castling, moves):
    """Kiểm tra và thêm nước nhập thành hợp lệ vào danh sách."""
    if t == 'w' and r == 7 and c == 4:
        if castling.get('wK') and not board[7][5] and not board[7][6]:
            if not any(is_attacked(board, 7, col, 'w') for col in (4, 5, 6)):
                moves.append((7, 6, 'castle'))
        if castling.get('wQ') and not board[7][3] and not board[7][2] and not board[7][1]:
            if not any(is_attacked(board, 7, col, 'w') for col in (4, 3, 2)):
                moves.append((7, 2, 'castle'))

    if t == 'b' and r == 0 and c == 4:
        if castling.get('bK') and not board[0][5] and not board[0][6]:
            if not any(is_attacked(board, 0, col, 'b') for col in (4, 5, 6)):
                moves.append((0, 6, 'castle'))
        if castling.get('bQ') and not board[0][3] and not board[0][2] and not board[0][1]:
            if not any(is_attacked(board, 0, col, 'b') for col in (4, 3, 2)):
                moves.append((0, 2, 'castle'))


# ─── KIỂM TRA TẤN CÔNG ───────────────────────────────────────────────────────

def is_attacked(board, r, c, t):
    """Trả về True nếu ô (r,c) đang bị bất kỳ quân nào của đối phương tấn công."""
    opp = 'b' if t == 'w' else 'w'
    for rr in range(8):
        for cc in range(8):
            if is_own(board[rr][cc], opp):
                for mr, mc, _ in pseudo_moves(board, rr, cc, opp, None, {}):
                    if mr == r and mc == c:
                        return True
    return False


# ─── THỰC THI NƯỚC ĐI ────────────────────────────────────────────────────────

def apply_move(board, fr, fc, tr, tc, flag, t):
    """Trả về bản sao bàn cờ sau khi thực thi nước đi (không sửa board gốc)."""
    b = [row[:] for row in board]
    p = b[fr][fc]
    b[tr][tc] = p
    b[fr][fc] = None

    if flag == 'castle':
        if tc == 6: b[fr][5], b[fr][7] = b[fr][7], None   # nhập thành gần
        else:       b[fr][3], b[fr][0] = b[fr][0], None   # nhập thành xa

    if flag == 'ep':
        d = -1 if is_white(p) else 1
        b[tr - d][tc] = None                               # xóa tốt bị bắt qua đường

    if p.upper() == 'P' and (tr == 0 or tr == 7):
        b[tr][tc] = 'Q' if is_white(p) else 'q'           # phong cấp mặc định lên Hậu

    return b


# ─── LỌC NƯỚC ĐI HỢP LỆ ─────────────────────────────────────────────────────

def legal_moves(board, r, c, t, en_passant, castling):
    """Lọc từ pseudo_moves: chỉ giữ nước đi mà sau đó vua không bị chiếu."""
    result = []
    for tr, tc, flag in pseudo_moves(board, r, c, t, en_passant, castling):
        nb = apply_move(board, r, c, tr, tc, flag, t)
        kr = find_king(nb, t)
        if kr and not is_attacked(nb, kr[0], kr[1], t):
            result.append((tr, tc, flag))
    return result


def all_legal_moves(board, t, en_passant, castling):
    """Tổng hợp tất cả nước đi hợp lệ của toàn bộ quân phe t."""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_own(board[r][c], t):
                for m in legal_moves(board, r, c, t, en_passant, castling):
                    moves.append((r, c) + m)
    return moves