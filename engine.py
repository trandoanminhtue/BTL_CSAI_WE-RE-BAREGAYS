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
        self.move_history = []   # Lịch sử các nước đi


# ─── ♟️ TIỆN ÍCH KIỂM TRA QUÂN CỜ ──────────────────────────────────────────────
#hàm is_white và is_black để kiểm tra quân trên bàn cờ là đen hay trắng
def is_white(p): return p and p.isupper()
# nếu p là None hoặc p là ký tự thường (quân Đen) thì trả về False, ngược lại nếu p là ký tự hoa (quân Trắng) thì trả về True.
def is_black(p): return p and p.islower()
# ngược lại với hàm white

# xác định quân cờ là của AI hay người chơi
def is_own(p, t): return is_white(p) if t == 'w' else is_black(p)
# nếu t là 'w' (Trắng), hàm sẽ trả về True nếu p là ký tự hoa (quân Trắng), 
# ngược lại nếu t là 'b' (Đen), hàm sẽ trả về True nếu p là ký tự thường (quân Đen).
def is_opp(p, t): return is_white(p) if t == 'b' else is_black(p)
# ngược lại
#logic của hàm: nếu đến lượt đi của Trắng (t == 'w'), 
# hàm sẽ trả về is_white, 
# ngược lại nếu đến lượt đi của Đen (t == 'b'), 
# hàm sẽ trả về is_black.

def in_bounds(r, c): return 0 <= r < 8 and 0 <= c < 8 # Kiểm tra tọa độ nằm trong bàn cờ

def find_king(board, t):
    """Tìm tọa độ quân Vua của phe t trên bàn cờ."""
    k = 'K' if t == 'w' else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c] == k:
                return (r, c)
    return None

# ─── ♟️ THÀNH PHẦN 2: BỘ SINH NƯỚC ĐI (MOVE GENERATOR) ─────────────────────────
def pseudo_moves(board, r, c, t, en_passant, castling):
    """Sinh tất cả nước đi lý thuyết (có thể vẫn đang bị chiếu)."""
    p = board[r][c]
    if not p or not is_own(p, t):
        return []
    pt = p.upper()
    moves = []

    def add(nr, nc, flag=None):
        """Hàm phụ hỗ trợ thêm nước đi vào danh sách nếu hợp lệ tọa độ."""
        if in_bounds(nr, nc) and not is_own(board[nr][nc], t):
            moves.append((nr, nc, flag))

    if pt == 'P': # Logic cho quân TỐT
        d = -1 if is_white(p) else 1 # Trắng đi lên (-1), Đen đi xuống (+1)
        start = 6 if is_white(p) else 1
        # Đi thẳng 1 hoặc 2 ô
        if in_bounds(r+d, c) and not board[r+d][c]:
            moves.append((r+d, c, None))
            if r == start and not board[r+d*2][c]:
                moves.append((r+d*2, c, None))
        # Ăn chéo & Bắt tốt qua đường
        for dc in (-1, 1):
            nr, nc = r+d, c+dc
            if in_bounds(nr, nc):
                if is_opp(board[nr][nc], t):
                    moves.append((nr, nc, None))
                elif en_passant and (nr, nc) == en_passant:
                    moves.append((nr, nc, 'ep'))

    elif pt == 'N': # Logic quân MÃ (Nhảy chữ L)
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            add(r+dr, c+dc)

    elif pt in ('B', 'Q'): # Logic quân TƯỢNG và HẬU (Đi chéo)
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            while in_bounds(nr, nc):
                if is_own(board[nr][nc], t): break
                moves.append((nr, nc, None))
                if board[nr][nc]: break # Dừng nếu gặp quân địch (đã ăn xong)
                nr += dr; nc += dc

    if pt in ('R', 'Q'): # Logic quân XE và HẬU (Đi thẳng)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            while in_bounds(nr, nc):
                if is_own(board[nr][nc], t): break
                moves.append((nr, nc, None))
                if board[nr][nc]: break
                nr += dr; nc += dc

    if pt == 'K': # Logic quân VUA (1 ô xung quanh)
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            add(r+dr, c+dc)
        # Kiểm tra điều kiện NHẬP THÀNH
        if t == 'w' and r == 7 and c == 4:
            if castling.get('wK') and not board[7][5] and not board[7][6]: # Cánh Vua
                if not is_attacked(board, 7, 4, 'w') and not is_attacked(board, 7, 5, 'w') and not is_attacked(board, 7, 6, 'w'):
                    moves.append((7, 6, 'castle'))
            if castling.get('wQ') and not board[7][3] and not board[7][2] and not board[7][1]: # Cánh Hậu
                if not is_attacked(board, 7, 4, 'w') and not is_attacked(board, 7, 3, 'w') and not is_attacked(board, 7, 2, 'w'):
                    moves.append((7, 2, 'castle'))
        # Tương tự cho quân Đen...
        if t == 'b' and r == 0 and c == 4:
            if castling.get('bK') and not board[0][5] and not board[0][6]:
                if not is_attacked(board, 0, 4, 'b') and not is_attacked(board, 0, 5, 'b') and not is_attacked(board, 0, 6, 'b'):
                    moves.append((0, 6, 'castle'))
            if castling.get('bQ') and not board[0][3] and not board[0][2] and not board[0][1]:
                if not is_attacked(board, 0, 4, 'b') and not is_attacked(board, 0, 3, 'b') and not is_attacked(board, 0, 2, 'b'):
                    moves.append((0, 2, 'castle'))

    return moves

def is_attacked(board, r, c, t):
    """Kiểm tra ô (r,c) có đang bị quân đối phương tấn công hay không."""
    opp = 'b' if t == 'w' else 'w'
    for rr in range(8):
        for cc in range(8):
            if is_own(board[rr][cc], opp):
                # Nếu bất kỳ nước đi giả định nào của địch chạm tới ô này -> Có bị tấn công
                for mr, mc, _ in pseudo_moves(board, rr, cc, opp, None, {}):
                    if mr == r and mc == c:
                        return True
    return False

def apply_move(board, fr, fc, tr, tc, flag, t):
    """Thực thi nước đi lên một bản sao của bàn cờ (để tính toán trước)."""
    b = [row[:] for row in board] # Copy bàn cờ
    p = b[fr][fc]
    b[tr][tc] = p
    b[fr][fc] = None
    # Xử lý nhập thành (di chuyển thêm quân Xe)
    if flag == 'castle':
        if tc == 6: # Nhập thành gần
            b[fr][5] = b[fr][7]; b[fr][7] = None
        else: # Nhập thành xa
            b[fr][3] = b[fr][0]; b[fr][0] = None
    # Xử lý bắt tốt qua đường (xóa quân tốt bị ăn)
    if flag == 'ep':
        d = -1 if is_white(p) else 1
        b[tr - d][tc] = None
    # Xử lý phong cấp (mặc định lên Hậu)
    if p.upper() == 'P' and (tr == 0 or tr == 7):
        b[tr][tc] = 'Q' if is_white(p) else 'q'
    return b

def legal_moves(board, r, c, t, en_passant, castling):
    """Lọc các nước đi hợp lệ: Đi thử -> Nếu vua không bị chiếu mới chấp nhận."""
    result = []
    for tr, tc, flag in pseudo_moves(board, r, c, t, en_passant, castling):
        nb = apply_move(board, r, c, tr, tc, flag, t)
        kr = find_king(nb, t)
        if kr and not is_attacked(nb, kr[0], kr[1], t):
            result.append((tr, tc, flag))
    return result

def all_legal_moves(board, t, en_passant, castling):
    """Tổng hợp tất cả nước đi hợp lệ của tất cả quân phe t."""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_own(board[r][c], t):
                for m in legal_moves(board, r, c, t, en_passant, castling):
                    moves.append((r, c) + m)
    return moves