# main.py — Giao diện desktop bằng Tkinter (built-in Python)
# Chạy: python main.py  →  Cửa sổ bàn cờ mở ra ngay

import tkinter as tk
from tkinter import font as tkfont
import threading
import time

from engine import GameState, all_legal_moves, apply_move, find_king, legal_moves, is_attacked
from ai import minimax
from constant import FILES

# ── CÀI ĐẶT GIAO DIỆN ────────────────────────────────────────────────────────
SQ_SIZE    = 72          # Kích thước mỗi ô (pixel)
BOARD_SIZE = SQ_SIZE * 8
AI_DEPTH   = 3

# Màu sắc
C_LIGHT      = "#f0d9b5"
C_DARK       = "#b58863"
C_SELECT     = "#829769"   # Ô đang chọn
C_LEGAL      = "#cdd16e"   # Ô nước đi hợp lệ
C_LAST_FROM  = "#cdd16e"   # Ô xuất phát nước vừa đi
C_LAST_TO    = "#aaa23a"   # Ô đích nước vừa đi
C_CHECK      = "#e74c3c"   # Ô vua bị chiếu
C_BG         = "#1a1a2e"   # Nền ứng dụng
C_PANEL      = "#16213e"   # Nền panel bên phải
C_TEXT       = "#e8dcc8"
C_GOLD       = "#c9a84c"
C_DIM        = "#8a7f72"

UNICODE_PIECES = {
    'P':'♙','R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔',
    'p':'♟','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚',
    None: ''
}

class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("♟ Chess vs AI")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)

        # Font
        self.piece_font  = tkfont.Font(family="Segoe UI Emoji", size=int(SQ_SIZE * 0.55))
        self.coord_font  = tkfont.Font(family="Georgia", size=9, weight="bold")
        self.label_font  = tkfont.Font(family="Georgia", size=11, weight="bold")
        self.small_font  = tkfont.Font(family="Georgia", size=9)
        self.status_font = tkfont.Font(family="Georgia", size=10, weight="bold")

        # Trạng thái game
        self.gs         = GameState()
        self.selected   = None   # (r, c) ô đang chọn
        self.legal_sqrs = []     # [(r, c)] nước đi hợp lệ
        self.last_move  = None   # ((fr,fc),(tr,tc))
        self.ai_thinking = False
        self.move_number = 0

        self._build_ui()
        self.draw_board()
        self.update_status("Lượt của bạn (Trắng). Click chọn quân.")

    # ── XÂY DỰNG UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # Frame chứa toàn bộ
        main_frame = tk.Frame(self.root, bg=C_BG)
        main_frame.pack(padx=16, pady=16)

        # ── Bàn cờ + tọa độ ──
        board_frame = tk.Frame(main_frame, bg=C_BG)
        board_frame.grid(row=0, column=0, padx=(0, 16))

        # Nhãn cột (a-h) phía trên
        col_top = tk.Frame(board_frame, bg=C_BG)
        col_top.grid(row=0, column=1)
        for i, ch in enumerate("abcdefgh"):
            tk.Label(col_top, text=ch, font=self.coord_font,
                     bg=C_BG, fg=C_DIM, width=4).grid(row=0, column=i)

        # Nhãn hàng (8-1) bên trái
        rank_frame = tk.Frame(board_frame, bg=C_BG)
        rank_frame.grid(row=1, column=0)
        for i in range(8):
            tk.Label(rank_frame, text=str(8-i), font=self.coord_font,
                     bg=C_BG, fg=C_DIM, width=2, anchor='e').grid(row=i, column=0)

        # Canvas bàn cờ
        self.canvas = tk.Canvas(board_frame,
                                width=BOARD_SIZE, height=BOARD_SIZE,
                                highlightthickness=3, highlightbackground=C_GOLD)
        self.canvas.grid(row=1, column=1)
        self.canvas.bind("<Button-1>", self.on_click)

        # Nhãn hàng bên phải
        rank_right = tk.Frame(board_frame, bg=C_BG)
        rank_right.grid(row=1, column=2)
        for i in range(8):
            tk.Label(rank_right, text=str(8-i), font=self.coord_font,
                     bg=C_BG, fg=C_DIM, width=2).grid(row=i, column=0)

        # Nhãn cột phía dưới
        col_bot = tk.Frame(board_frame, bg=C_BG)
        col_bot.grid(row=2, column=1)
        for i, ch in enumerate("abcdefgh"):
            tk.Label(col_bot, text=ch, font=self.coord_font,
                     bg=C_BG, fg=C_DIM, width=4).grid(row=0, column=i)

        # ── Panel bên phải ──
        panel = tk.Frame(main_frame, bg=C_PANEL, bd=0,
                         width=200, relief="flat")
        panel.grid(row=0, column=1, sticky="ns")
        panel.grid_propagate(False)

        # Card AI (Đen) ở trên
        self.card_b = self._player_card(panel, "♟", "AI (Đen)", f"Minimax depth {AI_DEPTH}", active=False)
        self.card_b.pack(fill="x", padx=12, pady=(14, 4))

        # Status
        self.status_var = tk.StringVar(value="")
        status_box = tk.Frame(panel, bg="#0d1426", bd=0)
        status_box.pack(fill="x", padx=12, pady=4)
        self.status_lbl = tk.Label(status_box, textvariable=self.status_var,
                                   font=self.small_font, bg="#0d1426", fg=C_TEXT,
                                   wraplength=170, justify="left", anchor="nw",
                                   padx=8, pady=8)
        self.status_lbl.pack(fill="x")

        # Log nước đi
        tk.Label(panel, text="Lịch sử nước đi", font=self.small_font,
                 bg=C_PANEL, fg=C_DIM).pack(anchor="w", padx=14, pady=(6,0))

        log_frame = tk.Frame(panel, bg="#0d1426")
        log_frame.pack(fill="x", padx=12, pady=4)
        self.log_text = tk.Text(log_frame, height=10, width=22,
                                font=tkfont.Font(family="Courier New", size=8),
                                bg="#0d1426", fg=C_DIM, relief="flat",
                                state="disabled", wrap="word",
                                padx=6, pady=6, cursor="arrow")
        self.log_text.pack()

        # Card Người chơi (Trắng) ở dưới
        self.card_w = self._player_card(panel, "♙", "Bạn (Trắng)", "Đi trước", active=True)
        self.card_w.pack(fill="x", padx=12, pady=4)

        # Nút Ván mới
        restart_btn = tk.Button(panel, text="↺  Ván mới",
                                font=self.label_font,
                                bg=C_PANEL, fg=C_GOLD,
                                activebackground=C_GOLD, activeforeground=C_BG,
                                relief="flat", bd=0, cursor="hand2",
                                command=self.restart_game)
        restart_btn.pack(fill="x", padx=12, pady=(4, 14))

    def _player_card(self, parent, icon, name, role, active):
        bg = "#1e2d4a" if active else C_PANEL
        frame = tk.Frame(parent, bg=bg, relief="flat", bd=0)
        tk.Label(frame, text=icon, font=tkfont.Font(size=22),
                 bg=bg, fg=C_TEXT).grid(row=0, column=0, rowspan=2, padx=(10,6), pady=8)
        tk.Label(frame, text=name, font=self.label_font,
                 bg=bg, fg=C_GOLD if active else C_TEXT, anchor="w").grid(row=0, column=1, sticky="w")
        tk.Label(frame, text=role, font=self.small_font,
                 bg=bg, fg=C_DIM, anchor="w").grid(row=1, column=1, sticky="w")
        return frame

    def _set_card_active(self, turn):
        """Highlight card theo lượt."""
        for widget in self.card_w.winfo_children():
            widget.configure(bg="#1e2d4a" if turn == 'w' else C_PANEL)
        self.card_w.configure(bg="#1e2d4a" if turn == 'w' else C_PANEL)
        for widget in self.card_b.winfo_children():
            widget.configure(bg="#1e2d4a" if turn == 'b' else C_PANEL)
        self.card_b.configure(bg="#1e2d4a" if turn == 'b' else C_PANEL)

    # ── VẼ BÀN CỜ ────────────────────────────────────────────────────────────
    def draw_board(self):
        self.canvas.delete("all")
        board = self.gs.board
        lm    = self.last_move
        kr    = find_king(board, self.gs.turn)
        in_check = kr and is_attacked(board, kr[0], kr[1], self.gs.turn)

        for r in range(8):
            for c in range(8):
                x1, y1 = c*SQ_SIZE, r*SQ_SIZE
                x2, y2 = x1+SQ_SIZE, y1+SQ_SIZE

                # Màu nền ô
                color = C_LIGHT if (r+c) % 2 == 0 else C_DARK

                # Nước đi cuối
                if lm:
                    if (r, c) == lm[0]: color = C_LAST_FROM
                    if (r, c) == lm[1]: color = C_LAST_TO

                # Chiếu
                if in_check and kr and (r, c) == kr:
                    color = C_CHECK

                # Ô đang chọn
                if self.selected and (r, c) == self.selected:
                    color = C_SELECT

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # Nước đi hợp lệ
                if (r, c) in self.legal_sqrs:
                    cx, cy = x1 + SQ_SIZE//2, y1 + SQ_SIZE//2
                    if board[r][c]:  # Có quân địch → vẽ viền tròn
                        self.canvas.create_oval(x1+3, y1+3, x2-3, y2-3,
                                                outline=C_LEGAL, width=4, fill="")
                    else:            # Ô trống → chấm tròn nhỏ
                        r2 = SQ_SIZE // 5
                        self.canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                                                fill=C_LEGAL, outline="")

                # Vẽ quân cờ
                p = board[r][c]
                if p:
                    sym = UNICODE_PIECES.get(p, '')
                    self.canvas.create_text(
                        x1 + SQ_SIZE//2, y1 + SQ_SIZE//2,
                        text=sym, font=self.piece_font,
                        fill="#1a1a1a" if p.isupper() else "#ffffff",
                        tags="piece"
                    )

    # ── XỬ LÝ CLICK ──────────────────────────────────────────────────────────
    def on_click(self, event):
        if self.ai_thinking or self.gs.turn != 'w':
            return
        c = event.x // SQ_SIZE
        r = event.y // SQ_SIZE
        if not (0 <= r < 8 and 0 <= c < 8):
            return

        board = self.gs.board

        # Đang có ô được chọn
        if self.selected:
            # Click vào nước đi hợp lệ → đi
            if (r, c) in self.legal_sqrs:
                self._do_move(self.selected[0], self.selected[1], r, c)
                return
            # Click quân Trắng khác → chọn lại
            if board[r][c] and board[r][c].isupper():
                self._select(r, c)
                return
            # Click vào nơi khác → bỏ chọn
            self.selected = None
            self.legal_sqrs = []
            self.draw_board()
            return

        # Chưa chọn: chỉ chọn quân Trắng
        p = board[r][c]
        if p and p.isupper():
            self._select(r, c)

    def _select(self, r, c):
        moves = legal_moves(self.gs.board, r, c, 'w', self.gs.en_passant, self.gs.castling)
        self.selected   = (r, c)
        self.legal_sqrs = [(m[0], m[1]) for m in moves]
        self.draw_board()

    # ── THỰC THI NƯỚC ĐI ─────────────────────────────────────────────────────
    def _do_move(self, fr, fc, tr, tc):
        valid = legal_moves(self.gs.board, fr, fc, 'w', self.gs.en_passant, self.gs.castling)
        match = next((m for m in valid if m[0] == tr and m[1] == tc), None)
        if not match:
            return

        self._update_ep(fr, fc, tr)
        self._update_castling(fr, fc)
        self.gs.board = apply_move(self.gs.board, fr, fc, tr, tc, match[2], 'w')
        self.gs.turn  = 'b'
        self.last_move = ((fr, fc), (tr, tc))
        self.selected   = None
        self.legal_sqrs = []
        self.move_number += 1
        self._log_move(fr, fc, tr, tc, 'w')
        self.draw_board()

        state = self._check_game_over()
        if state: return
        self._set_card_active('b')
        self.update_status("⏳ AI đang suy nghĩ…")
        # Chạy AI trên luồng riêng để không đóng băng cửa sổ
        threading.Thread(target=self._ai_move, daemon=True).start()

    def _ai_move(self):
        t0 = time.time()
        _, best = minimax(self.gs.board, AI_DEPTH, float('-inf'), float('inf'),
                          False, 'b', self.gs.en_passant, self.gs.castling)
        elapsed = time.time() - t0

        if best:
            fr, fc, tr, tc, flag = best
            self._update_ep(fr, fc, tr)
            self._update_castling(fr, fc)
            self.gs.board  = apply_move(self.gs.board, fr, fc, tr, tc, flag, 'b')
            self.gs.turn   = 'w'
            self.last_move = ((fr, fc), (tr, tc))
            self.move_number += 1
            # Cập nhật UI từ main thread
            self.root.after(0, lambda: self._after_ai(fr, fc, tr, tc, elapsed))

    def _after_ai(self, fr, fc, tr, tc, elapsed):
        self._log_move(fr, fc, tr, tc, 'b', elapsed)
        self.draw_board()
        state = self._check_game_over()
        if not state:
            self._set_card_active('w')
            self.update_status("Lượt của bạn. Click chọn quân.")

    # ── KIỂM TRA KẾT THÚC ────────────────────────────────────────────────────
    def _check_game_over(self):
        moves = all_legal_moves(self.gs.board, self.gs.turn, self.gs.en_passant, self.gs.castling)
        if moves: return False

        kr = find_king(self.gs.board, self.gs.turn)
        in_check = kr and is_attacked(self.gs.board, kr[0], kr[1], self.gs.turn)
        if in_check:
            winner = "Trắng" if self.gs.turn == 'b' else "Đen"
            self._show_popup(f"♛ Chiếu hết!\n{winner} thắng!")
        else:
            self._show_popup("½ Hòa!\nBế tắc (Stalemate).")
        return True

    def _show_popup(self, msg):
        """Hiện cửa sổ thông báo kết thúc ván."""
        top = tk.Toplevel(self.root)
        top.title("Kết thúc ván")
        top.resizable(False, False)
        top.configure(bg=C_PANEL)
        top.grab_set()

        # Căn giữa màn hình
        top.update_idletasks()
        pw, ph = 300, 160
        sx = self.root.winfo_rootx() + (BOARD_SIZE//2) - (pw//2)
        sy = self.root.winfo_rooty() + (BOARD_SIZE//2) - (ph//2)
        top.geometry(f"{pw}x{ph}+{sx}+{sy}")

        tk.Label(top, text=msg, font=self.label_font,
                 bg=C_PANEL, fg=C_GOLD, pady=20).pack()
        tk.Button(top, text="↺  Ván mới",
                  font=self.label_font, bg=C_PANEL, fg=C_GOLD,
                  activebackground=C_GOLD, activeforeground=C_BG,
                  relief="flat", bd=0, cursor="hand2",
                  command=lambda: [top.destroy(), self.restart_game()]
                  ).pack(pady=(0, 16))

    # ── TIỆN ÍCH ─────────────────────────────────────────────────────────────
    def _update_ep(self, fr, fc, tr):
        p = self.gs.board[fr][fc]
        if p and p.upper() == 'P' and abs(tr - fr) == 2:
            self.gs.en_passant = (fr + (tr-fr)//2, fc)
        else:
            self.gs.en_passant = None

    def _update_castling(self, fr, fc):
        p = self.gs.board[fr][fc]
        if not p: return
        c = self.gs.castling
        if p == 'K': c['wK'] = c['wQ'] = False
        if p == 'k': c['bK'] = c['bQ'] = False
        if p == 'R' and fr==7 and fc==7: c['wK'] = False
        if p == 'R' and fr==7 and fc==0: c['wQ'] = False
        if p == 'r' and fr==0 and fc==7: c['bK'] = False
        if p == 'r' and fr==0 and fc==0: c['bQ'] = False

    def _log_move(self, fr, fc, tr, tc, who, elapsed=None):
        from_sq = FILES[fc] + str(8-fr)
        to_sq   = FILES[tc] + str(8-tr)
        n = (self.move_number + 1) // 2
        if who == 'w':
            entry = f"{n}. {from_sq}→{to_sq}"
        else:
            t = f" ({elapsed:.1f}s)" if elapsed else ""
            entry = f"   {from_sq}→{to_sq}{t}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", entry + (" " if who=='w' else ""))
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_status(self, msg):
        self.status_var.set(msg)

    def restart_game(self):
        self.gs          = GameState()
        self.selected    = None
        self.legal_sqrs  = []
        self.last_move   = None
        self.ai_thinking = False
        self.move_number = 0
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._set_card_active('w')
        self.draw_board()
        self.update_status("Ván mới bắt đầu! Lượt của bạn.")


# ── CHẠY ỨNG DỤNG ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    app  = ChessApp(root)
    root.mainloop()