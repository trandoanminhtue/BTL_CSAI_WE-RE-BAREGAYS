# game_controller.py — Điều phối ván đấu: thực thi nước đi, gọi AI, kiểm tra kết thúc

import threading
import time

from src.engine.game_state import GameState
from src.engine.rules import all_legal_moves, apply_move, legal_moves, find_king, is_attacked
from src.ai.ai import get_best_move, clear_tt

AI_DEPTH = 3


class GameController:
    def __init__(self):
        self.gs          = GameState()
        self.move_number = 0

        # Callbacks — app.py gán vào sau khi khởi tạo
        self.on_move_done   = None   # fn(fr, fc, tr, tc, who)        — sau mỗi nước đi
        self.on_ai_done     = None   # fn(fr, fc, tr, tc, elapsed)    — sau khi AI xong
        self.on_game_over   = None   # fn(result: str)                — 'checkmate' | 'stalemate'

    # ─── TRUY VẤN TRẠNG THÁI ─────────────────────────────────────────────────

    def get_legal_squares(self, r, c, turn):
        """Trả về list (row, col) các ô hợp lệ của quân tại (r,c)."""
        moves = legal_moves(self.gs.board, r, c, turn, self.gs.en_passant, self.gs.castling)
        return [(m[0], m[1]) for m in moves]

    def is_in_check(self):
        """Trả về (row, col) của vua đang bị chiếu, hoặc None."""
        kr = find_king(self.gs.board, self.gs.turn)
        if kr and is_attacked(self.gs.board, kr[0], kr[1], self.gs.turn):
            return kr
        return None

    # ─── THỰC THI NƯỚC ĐI NGƯỜI CHƠI ─────────────────────────────────────────

    def do_player_move(self, fr, fc, tr, tc):
        """Thực thi nước đi của người chơi (Trắng). Trả về False nếu không hợp lệ."""
        valid = legal_moves(self.gs.board, fr, fc, 'w', self.gs.en_passant, self.gs.castling)
        match = next((m for m in valid if m[0] == tr and m[1] == tc), None)
        if not match:
            return False

        self._update_ep(fr, fc, tr)
        self._update_castling(fr, fc)
        self.gs.board = apply_move(self.gs.board, fr, fc, tr, tc, match[2], 'w')
        self.gs.turn  = 'b'
        self.move_number += 1
        self.gs.move_history.append((fr, fc, tr, tc))

        if self.on_move_done:
            self.on_move_done(fr, fc, tr, tc, 'w')

        if self._check_game_over():
            return True

        threading.Thread(target=self._run_ai, daemon=True).start()
        return True

    # ─── AI ───────────────────────────────────────────────────────────────────

    def _run_ai(self):
        """Chạy trên thread riêng — tính nước đi AI rồi callback về main thread."""
        t0   = time.time()
        best = get_best_move(self.gs.board, AI_DEPTH, 'b',
                             self.gs.en_passant, self.gs.castling,
                             self.gs.move_history)
        elapsed = time.time() - t0

        if not best:
            return

        fr, fc, tr, tc, flag = best
        self._update_ep(fr, fc, tr)
        self._update_castling(fr, fc)
        self.gs.board = apply_move(self.gs.board, fr, fc, tr, tc, flag, 'b')
        self.gs.turn  = 'w'
        self.move_number += 1
        self.gs.move_history.append((fr, fc, tr, tc))

        if self.on_ai_done:
            self.on_ai_done(fr, fc, tr, tc, elapsed)

        self._check_game_over()

    # ─── KIỂM TRA KẾT THÚC ───────────────────────────────────────────────────

    def _check_game_over(self):
        """Trả về True và gọi on_game_over nếu ván kết thúc."""
        moves = all_legal_moves(self.gs.board, self.gs.turn,
                                self.gs.en_passant, self.gs.castling)
        if moves:
            return False

        kr       = find_king(self.gs.board, self.gs.turn)
        in_check = kr and is_attacked(self.gs.board, kr[0], kr[1], self.gs.turn)
        result   = 'checkmate' if in_check else 'stalemate'

        if self.on_game_over:
            self.on_game_over(result)
        return True

    # ─── RESET ────────────────────────────────────────────────────────────────

    def restart(self):
        """Reset về ván mới."""
        self.gs          = GameState()
        self.move_number = 0
        clear_tt()

    # ─── CẬP NHẬT TRẠNG THÁI NỘI BỘ ─────────────────────────────────────────

    def _update_ep(self, fr, fc, tr):
        """Cập nhật ô bắt tốt qua đường sau mỗi nước đi."""
        p = self.gs.board[fr][fc]
        if p and p.upper() == 'P' and abs(tr - fr) == 2:
            self.gs.en_passant = (fr + (tr - fr) // 2, fc)
        else:
            self.gs.en_passant = None

    def _update_castling(self, fr, fc):
        """Hủy quyền nhập thành khi vua hoặc xe di chuyển."""
        p = self.gs.board[fr][fc]
        if not p:
            return
        c = self.gs.castling
        if p == 'K':                      c['wK'] = c['wQ'] = False
        if p == 'k':                      c['bK'] = c['bQ'] = False
        if p == 'R' and fr==7 and fc==7:  c['wK'] = False
        if p == 'R' and fr==7 and fc==0:  c['wQ'] = False
        if p == 'r' and fr==0 and fc==7:  c['bK'] = False
        if p == 'r' and fr==0 and fc==0:  c['bQ'] = False