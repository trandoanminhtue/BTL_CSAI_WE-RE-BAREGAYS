# app.py — Giao diện Tkinter: vẽ bàn cờ, xử lý click, cập nhật panel

import tkinter as tk
from tkinter import font as tkfont

from src.engine.rules import find_king, is_attacked
from src.engine.constant import FILES
from src.controller.game_controller import GameController, AI_DEPTH

# ─── HẰNG SỐ GIAO DIỆN ───────────────────────────────────────────────────────

SQ_SIZE    = 72
BOARD_SIZE = SQ_SIZE * 8

C_LIGHT     = "#f0d9b5"
C_DARK      = "#b58863"
C_SELECT    = "#829769"
C_LEGAL     = "#cdd16e"
C_LAST_FROM = "#cdd16e"
C_LAST_TO   = "#aaa23a"
C_CHECK     = "#e74c3c"
C_BG        = "#1a1a2e"
C_PANEL     = "#16213e"
C_TEXT      = "#e8dcc8"
C_GOLD      = "#c9a84c"
C_DIM       = "#8a7f72"

UNICODE_PIECES = {
    'P':'♙','R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔',
    'p':'♟','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚',
    None: ''
}


# ─── APP ─────────────────────────────────────────────────────────────────────

class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("♟ Chess vs AI")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)

        self._init_fonts()

        # UI state
        self.selected   = None   # (r, c) ô đang chọn
        self.legal_sqrs = []     # [(r, c)] nước đi hợp lệ hiển thị
        self.last_move  = None   # ((fr,fc), (tr,tc))
        self.move_number = 0

        # Controller + gán callbacks
        self.ctrl = GameController()
        self.ctrl.on_move_done = self._on_move_done
        self.ctrl.on_ai_done   = self._on_ai_done
        self.ctrl.on_game_over = self._on_game_over

        self._build_ui()
        self.draw_board()
        self.update_status("Lượt của bạn (Trắng). Click chọn quân.")

    def _init_fonts(self):
        self.piece_font  = tkfont.Font(family="Segoe UI Emoji", size=int(SQ_SIZE * 0.55))
        self.coord_font  = tkfont.Font(family="Georgia", size=9, weight="bold")
        self.label_font  = tkfont.Font(family="Georgia", size=11, weight="bold")
        self.small_font  = tkfont.Font(family="Georgia", size=9)

    # ─── XÂY DỰNG UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        main_frame = tk.Frame(self.root, bg=C_BG)
        main_frame.pack(padx=16, pady=16)

        self._build_board_area(main_frame)
        self._build_panel(main_frame)

    def _build_board_area(self, parent):
        board_frame = tk.Frame(parent, bg=C_BG)
        board_frame.grid(row=0, column=0, padx=(0, 16))

        # Nhãn cột trên / dưới
        for row_idx, row in enumerate([0, 2]):
            f = tk.Frame(board_frame, bg=C_BG)
            f.grid(row=row, column=1)
            for i, ch in enumerate("abcdefgh"):
                tk.Label(f, text=ch, font=self.coord_font,
                         bg=C_BG, fg=C_DIM, width=4).grid(row=0, column=i)

        # Nhãn hàng trái / phải
        for col_idx, col in enumerate([0, 2]):
            f = tk.Frame(board_frame, bg=C_BG)
            f.grid(row=1, column=col)
            for i in range(8):
                tk.Label(f, text=str(8-i), font=self.coord_font,
                         bg=C_BG, fg=C_DIM, width=2,
                         anchor='e' if col == 0 else 'w').grid(row=i, column=0)

        # Canvas bàn cờ
        self.canvas = tk.Canvas(board_frame,
                                width=BOARD_SIZE, height=BOARD_SIZE,
                                highlightthickness=3, highlightbackground=C_GOLD)
        self.canvas.grid(row=1, column=1)
        self.canvas.bind("<Button-1>", self.on_click)

    def _build_panel(self, parent):
        panel = tk.Frame(parent, bg=C_PANEL, bd=0, width=200, relief="flat")
        panel.grid(row=0, column=1, sticky="ns")
        panel.grid_propagate(False)

        self.card_b = self._player_card(panel, "♟", "AI (Đen)", f"Minimax depth {AI_DEPTH}", active=False)
        self.card_b.pack(fill="x", padx=12, pady=(14, 4))

        # Status
        self.status_var = tk.StringVar(value="")
        status_box = tk.Frame(panel, bg="#0d1426", bd=0)
        status_box.pack(fill="x", padx=12, pady=4)
        tk.Label(status_box, textvariable=self.status_var,
                 font=self.small_font, bg="#0d1426", fg=C_TEXT,
                 wraplength=170, justify="left", anchor="nw",
                 padx=8, pady=8).pack(fill="x")

        # Log nước đi
        tk.Label(panel, text="Lịch sử nước đi", font=self.small_font,
                 bg=C_PANEL, fg=C_DIM).pack(anchor="w", padx=14, pady=(6, 0))
        log_frame = tk.Frame(panel, bg="#0d1426")
        log_frame.pack(fill="x", padx=12, pady=4)
        self.log_text = tk.Text(log_frame, height=10, width=22,
                                font=tkfont.Font(family="Courier New", size=8),
                                bg="#0d1426", fg=C_DIM, relief="flat",
                                state="disabled", wrap="word",
                                padx=6, pady=6, cursor="arrow")
        self.log_text.pack()

        self.card_w = self._player_card(panel, "♙", "Bạn (Trắng)", "Đi trước", active=True)
        self.card_w.pack(fill="x", padx=12, pady=4)

        tk.Button(panel, text="↺  Ván mới",
                  font=self.label_font, bg=C_PANEL, fg=C_GOLD,
                  activebackground=C_GOLD, activeforeground=C_BG,
                  relief="flat", bd=0, cursor="hand2",
                  command=self.restart_game).pack(fill="x", padx=12, pady=(4, 14))

    def _player_card(self, parent, icon, name, role, active):
        bg    = "#1e2d4a" if active else C_PANEL
        frame = tk.Frame(parent, bg=bg, relief="flat", bd=0)
        tk.Label(frame, text=icon, font=tkfont.Font(size=22),
                 bg=bg, fg=C_TEXT).grid(row=0, column=0, rowspan=2, padx=(10, 6), pady=8)
        tk.Label(frame, text=name, font=self.label_font,
                 bg=bg, fg=C_GOLD if active else C_TEXT, anchor="w").grid(row=0, column=1, sticky="w")
        tk.Label(frame, text=role, font=self.small_font,
                 bg=bg, fg=C_DIM, anchor="w").grid(row=1, column=1, sticky="w")
        return frame

    def _set_card_active(self, turn):
        for card, active_turn in [(self.card_w, 'w'), (self.card_b, 'b')]:
            bg = "#1e2d4a" if turn == active_turn else C_PANEL
            card.configure(bg=bg)
            for w in card.winfo_children():
                w.configure(bg=bg)

    # ─── VẼ BÀN CỜ ───────────────────────────────────────────────────────────

    def draw_board(self):
        self.canvas.delete("all")
        board    = self.ctrl.gs.board
        lm       = self.last_move
        check_sq = self.ctrl.is_in_check()

        for r in range(8):
            for c in range(8):
                x1, y1 = c * SQ_SIZE, r * SQ_SIZE
                x2, y2 = x1 + SQ_SIZE, y1 + SQ_SIZE

                color = C_LIGHT if (r + c) % 2 == 0 else C_DARK
                if lm:
                    if (r, c) == lm[0]: color = C_LAST_FROM
                    if (r, c) == lm[1]: color = C_LAST_TO
                if check_sq and (r, c) == check_sq:
                    color = C_CHECK
                if self.selected and (r, c) == self.selected:
                    color = C_SELECT

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # Chấm / viền nước đi hợp lệ
                if (r, c) in self.legal_sqrs:
                    cx, cy = x1 + SQ_SIZE // 2, y1 + SQ_SIZE // 2
                    if board[r][c]:
                        self.canvas.create_oval(x1+3, y1+3, x2-3, y2-3,
                                                outline=C_LEGAL, width=4, fill="")
                    else:
                        r2 = SQ_SIZE // 5
                        self.canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                                                fill=C_LEGAL, outline="")

                # Vẽ quân cờ
                p = board[r][c]
                if p:
                    self.canvas.create_text(
                        x1 + SQ_SIZE // 2, y1 + SQ_SIZE // 2,
                        text=UNICODE_PIECES.get(p, ''),
                        font=self.piece_font,
                        fill="#1a1a1a" if p.isupper() else "#ffffff",
                        tags="piece"
                    )

    # ─── XỬ LÝ CLICK ─────────────────────────────────────────────────────────

    def on_click(self, event):
        if self.ctrl.gs.turn != 'w':
            return
        c = event.x // SQ_SIZE
        r = event.y // SQ_SIZE
        if not (0 <= r < 8 and 0 <= c < 8):
            return

        board = self.ctrl.gs.board

        if self.selected:
            if (r, c) in self.legal_sqrs:
                self.ctrl.do_player_move(self.selected[0], self.selected[1], r, c)
                return
            if board[r][c] and board[r][c].isupper():
                self._select(r, c)
                return
            self._deselect()
            return

        if board[r][c] and board[r][c].isupper():
            self._select(r, c)

    def _select(self, r, c):
        self.selected   = (r, c)
        self.legal_sqrs = self.ctrl.get_legal_squares(r, c, 'w')
        self.draw_board()

    def _deselect(self):
        self.selected   = None
        self.legal_sqrs = []
        self.draw_board()

    # ─── CALLBACKS TỪ CONTROLLER ─────────────────────────────────────────────

    def _on_move_done(self, fr, fc, tr, tc, who):
        """Gọi sau mỗi nước đi người chơi — chạy trên main thread."""
        self.last_move   = ((fr, fc), (tr, tc))
        self.move_number = self.ctrl.move_number
        self.selected    = None
        self.legal_sqrs  = []
        self._log_move(fr, fc, tr, tc, who)
        self.draw_board()
        if who == 'w':
            self._set_card_active('b')
            self.update_status("⏳ AI đang suy nghĩ…")

    def _on_ai_done(self, fr, fc, tr, tc, elapsed):
        """Gọi sau khi AI xong — phải đẩy về main thread vì AI chạy trên thread riêng."""
        self.root.after(0, lambda: self._apply_ai_result(fr, fc, tr, tc, elapsed))

    def _apply_ai_result(self, fr, fc, tr, tc, elapsed):
        self.last_move   = ((fr, fc), (tr, tc))
        self.move_number = self.ctrl.move_number
        self._log_move(fr, fc, tr, tc, 'b', elapsed)
        self.draw_board()
        self._set_card_active('w')
        self.update_status("Lượt của bạn. Click chọn quân.")

    def _on_game_over(self, result):
        """Gọi khi ván kết thúc — đẩy về main thread."""
        if result == 'checkmate':
            winner = "Trắng" if self.ctrl.gs.turn == 'b' else "Đen"
            msg = f"♛ Chiếu hết!\n{winner} thắng!"
        else:
            msg = "½ Hòa!\nBế tắc (Stalemate)."
        self.root.after(0, lambda: self._show_popup(msg))

    # ─── TIỆN ÍCH UI ─────────────────────────────────────────────────────────

    def update_status(self, msg):
        self.status_var.set(msg)

    def _log_move(self, fr, fc, tr, tc, who, elapsed=None):
        from_sq = FILES[fc] + str(8 - fr)
        to_sq   = FILES[tc] + str(8 - tr)
        n = (self.move_number + 1) // 2
        if who == 'w':
            entry = f"{n}. {from_sq}→{to_sq}  "
        else:
            t     = f" ({elapsed:.1f}s)" if elapsed else ""
            entry = f"{from_sq}→{to_sq}{t}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", entry)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _show_popup(self, msg):
        top = tk.Toplevel(self.root)
        top.title("Kết thúc ván")
        top.resizable(False, False)
        top.configure(bg=C_PANEL)
        top.grab_set()

        pw, ph = 300, 160
        top.update_idletasks()
        sx = self.root.winfo_rootx() + BOARD_SIZE // 2 - pw // 2
        sy = self.root.winfo_rooty() + BOARD_SIZE // 2 - ph // 2
        top.geometry(f"{pw}x{ph}+{sx}+{sy}")

        tk.Label(top, text=msg, font=self.label_font,
                 bg=C_PANEL, fg=C_GOLD, pady=20).pack()
        tk.Button(top, text="↺  Ván mới",
                  font=self.label_font, bg=C_PANEL, fg=C_GOLD,
                  activebackground=C_GOLD, activeforeground=C_BG,
                  relief="flat", bd=0, cursor="hand2",
                  command=lambda: [top.destroy(), self.restart_game()]
                  ).pack(pady=(0, 16))

    def restart_game(self):
        self.ctrl.restart()
        self.selected    = None
        self.legal_sqrs  = []
        self.last_move   = None
        self.move_number = 0
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._set_card_active('w')
        self.draw_board()
        self.update_status("Ván mới bắt đầu! Lượt của bạn.")