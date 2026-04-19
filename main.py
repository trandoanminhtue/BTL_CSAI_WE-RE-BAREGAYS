# main.py
from re import UNICODE
import time
from engine import GameState, all_legal_moves, apply_move, find_king, legal_moves, is_attacked
from ai import minimax
from constant import UNICODE_PIECES, FILES

def print_board(board, last_move=None):
    """In bàn cờ ra màn hình Console với màu sắc làm nổi bật nước đi cuối."""
    print("\n    a  b  c  d  e  f  g  h")
    print("  ┌" + "──┬" * 7 + "──┐")
    for r in range(8):
        row = f"{8-r} │"
        for c in range(8):
            p = board[r][c]
            sym = UNICODE_PIECES.get(p, '?')
            # Tô màu vàng (\033[43m) cho ô vừa mới di chuyển
            if last_move and ((r, c) == last_move[0] or (r, c) == last_move[1]):
                row += f"\033[43m {sym} \033[0m│"
            else:
                row += f" {sym} │"
        row += f" {8-r}"
        print(row)
        if r < 7: print("  ├" + "──┼" * 7 + "──┤")
    print("  └" + "──┴" * 7 + "──┘")
    print("    a  b  c  d  e  f  g  h\n")

def parse_move(text):
    """Chuyển đổi chuỗi nhập liệu (VD: 'e2e4') thành tọa độ mảng (row, col)."""
    text = text.strip().replace(' ', '').lower()
    if len(text) != 4: return None
    fc = FILES.find(text[0])
    fr = 8 - int(text[1])
    tc = FILES.find(text[2])
    tr = 8 - int(text[3])
    if any(x < 0 for x in [fr, fc, tr, tc]): return None
    return fr, fc, tr, tc

def update_castling(castling, board, fr, fc, t):
    """Cập nhật quyền nhập thành nếu Vua hoặc Xe đã di chuyển hoặc bị ăn mất."""
    p = board[fr][fc]
    if not p: return
    if p == 'K': castling['wK'] = castling['wQ'] = False
    if p == 'k': castling['bK'] = castling['bQ'] = False
    if p == 'R' and fr == 7 and fc == 7: castling['wK'] = False
    if p == 'R' and fr == 7 and fc == 0: castling['wQ'] = False
    if p == 'r' and fr == 0 and fc == 7: castling['bK'] = False
    if p == 'r' and fr == 0 and fc == 0: castling['bQ'] = False

# ─── 🔄 VÒNG LẶP CHÍNH CỦA TRÒ CHƠI ───────────────────────────────────────────
def main():
    gs = GameState()
    last_move = None
    AI_DEPTH = 3 # Độ sâu tính toán của AI

    while True:
        print_board(gs.board, last_move)
        moves = all_legal_moves(gs.board, gs.turn, gs.en_passant, gs.castling)
        kr = find_king(gs.board, gs.turn)
        in_check = kr and is_attacked(gs.board, kr[0], kr[1], gs.turn)

        # Kiểm tra điều kiện kết thúc ván đấu
        if not moves:
            if in_check:
                print(f"♛ CHIẾU HẾT! {'Trắng' if gs.turn == 'b' else 'Đen'} thắng!")
            else:
                print("½ HÒA! Bế tắc (Stalemate).")
            break

        if in_check: print("⚠ CHIẾU!")

        # LƯỢT NGƯỜI CHƠI (TRẮNG)
        if gs.turn == 'w':
            inp = input("Nước đi của bạn (VD: e2e4): ").strip().lower()
            if inp == 'quit': break
            parsed = parse_move(inp)
            if not parsed: continue
            
            fr, fc, tr, tc = parsed
            valid = legal_moves(gs.board, fr, fc, 'w', gs.en_passant, gs.castling)
            match = next((m for m in valid if m[0] == tr and m[1] == tc), None)
            
            if match:
                # Cập nhật trạng thái sau nước đi hợp lệ
                update_castling(gs.castling, gs.board, fr, fc, 'w')
                gs.board = apply_move(gs.board, fr, fc, tr, tc, match[2], 'w')
                gs.turn = 'b' # Đổi lượt
                last_move = ((fr, fc), (tr, tc))
            else:
                print("❌ Nước đi không hợp lệ!")

        # LƯỢT AI (ĐEN)
        else:
            print("⏳ AI đang suy nghĩ...", end='', flush=True)
            t0 = time.time()
            # Gọi thuật toán Minimax để tìm nước đi tốt nhất cho phe Đen (False)
            _, best = minimax(gs.board, AI_DEPTH, float('-inf'), float('inf'), False, 'b', gs.en_passant, gs.castling)
            
            if best:
                fr, fc, tr, tc, flag = best
                update_castling(gs.castling, gs.board, fr, fc, 'b')
                gs.board = apply_move(gs.board, fr, fc, tr, tc, flag, 'b')
                gs.turn = 'w'
                last_move = ((fr, fc), (tr, tc))
                print(f" Done! ({time.time()-t0:.1f}s)")

if __name__ == '__main__':
    main()