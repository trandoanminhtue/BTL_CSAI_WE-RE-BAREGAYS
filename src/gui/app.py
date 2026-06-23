# app.py — Giao diện Tkinter: vẽ bàn cờ, xử lý click, cập nhật panel

import tkinter as tk
from tkinter import font as tkfont

from src.engine.rules import find_king, is_attacked
from src.engine.constant import FILES
from src.controller.game_controller import GameController, AI_DEPTH, AI_TIME_LIMIT

# ─── HẰNG SỐ GIAO DIỆN ───────────────────────────────────────────────────────

SQ_SIZE       = 72
BOARD_SIZE    = SQ_SIZE * 8
COORD_MARGIN  = 26          # lề vẽ chữ a-h / 1-8
CANVAS_SIZE   = BOARD_SIZE + COORD_MARGIN * 2

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
C_BORDER    = "#c9a84c"
C_CARD_ACT  = "#1e2d4a"
C_INNER     = "#0d1426"

UNICODE_PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
    None: '',
}


class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess vs AI")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)

        self._init_fonts()

        self.selected    = None
        self.legal_sqrs  = []
        self.last_move   = None
        self.move_number = 0

        self.ctrl = GameController()
        self.ctrl.on_move_done = self._on_move_done
        self.ctrl.on_ai_done   = self._on_ai_done
        self.ctrl.on_game_over = self._on_game_over

        self._build_ui()
        self.draw_board()
        self.update_status("Lượt của bạn (Trắng). Click chọn quân.")

    def _init_fonts(self):
        self.piece_font = tkfont.Font(family="Segoe UI Emoji", size=int(SQ_SIZE * 0.55))
        self.coord_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.title_font = tkfont.Font(family="Georgia", size=15, weight="bold")
        self.label_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.small_font = tkfont.Font(family="Segoe UI", size=9)
        self.log_font   = tkfont.Font(family="Consolas", size=9)

    # ─── XÂY DỰNG UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=C_BG)
        outer.pack(padx=20, pady=20)

        self._build_board_area(outer)
        self._build_panel(outer)

    def _build_board_area(self, parent):
        wrap = tk.Frame(parent, bg=C_BG, highlightthickness=2,
                        highlightbackground=C_BORDER, highlightcolor=C_BORDER)
        wrap.grid(row=0, column=0, padx=(0, 20))

        self.canvas = tk.Canvas(
            wrap, width=CANVAS_SIZE, height=CANVAS_SIZE,
            bg=C_BG, highlightthickness=0, bd=0,
        )
        self.canvas.pack(padx=4, pady=4)
        self.canvas.bind("<Button-1>", self.on_click)

    def _build_panel(self, parent):
        panel = tk.Frame(parent, bg=C_PANEL, width=240)
        panel.grid(row=0, column=1, sticky="ns")
        panel.grid_propagate(False)

        header = tk.Frame(panel, bg=C_PANEL)
        header.pack(fill="x", padx=16, pady=(16, 8))
        tk.Label(header, text="♟  Chess vs AI", font=self.title_font,
                 bg=C_PANEL, fg=C_GOLD, anchor="w").pack(fill="x")
        tk.Label(header, text="Hybrid AI · Minimax + Neural",
                 font=self.small_font, bg=C_PANEL, fg=C_DIM, anchor="w").pack(fill="x")

        tk.Frame(panel, bg=C_DIM, height=1).pack(fill="x", padx=16, pady=8)

        self.card_b = self._player_card(
            panel, "♟", "AI (Đen)",
            f"Depth ≤{AI_DEPTH}  ·  ~{AI_TIME_LIMIT:.0f}s/nước",
            active=False,
        )
        self.card_b.pack(fill="x", padx=14, pady=(0, 6))

        status_box = tk.Frame(panel, bg=C_INNER, highlightthickness=1,
                              highlightbackground="#2a3a5c")
        status_box.pack(fill="x", padx=14, pady=6)
        self.status_var = tk.StringVar(value="")
        tk.Label(status_box, textvariable=self.status_var,
                 font=self.small_font, bg=C_INNER, fg=C_TEXT,
                 wraplength=200, justify="left", anchor="nw",
                 padx=10, pady=10).pack(fill="x")

        tk.Label(panel, text="Lịch sử nước đi", font=self.small_font,
                 bg=C_PANEL, fg=C_DIM).pack(anchor="w", padx=16, pady=(8, 2))

        log_outer = tk.Frame(panel, bg=C_INNER, highlightthickness=1,
                             highlightbackground="#2a3a5c")
        log_outer.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        self.log_text = tk.Text(
            log_outer, height=11, width=26, font=self.log_font,
            bg=C_INNER, fg="#a8b4c8", relief="flat", bd=0,
            state="disabled", wrap="word", padx=8, pady=8, cursor="arrow",
            highlightthickness=0,
        )
        self.log_text.pack(fill="both", expand=True)

        self.card_w = self._player_card(panel, "♙", "Bạn (Trắng)", "Đi trước", active=True)
        self.card_w.pack(fill="x", padx=14, pady=6)

        btn_frame = tk.Frame(panel, bg=C_PANEL)
        btn_frame.pack(fill="x", padx=14, pady=(4, 16))
        tk.Button(
            btn_frame, text="↺  Ván mới", font=self.label_font,
            bg=C_CARD_ACT, fg=C_GOLD, activebackground=C_GOLD,
            activeforeground=C_BG, relief="flat", bd=0, cursor="hand2",
            padx=12, pady=10, command=self.restart_game,
        ).pack(fill="x")

    def _player_card(self, parent, icon, name, role, active):
        bg = C_CARD_ACT if active else C_PANEL
        frame = tk.Frame(parent, bg=bg, highlightthickness=1,
                         highlightbackground=C_BORDER if active else "#2a3a5c")
        inner = tk.Frame(frame, bg=bg)
        inner.pack(fill="x", padx=2, pady=2)

        tk.Label(inner, text=icon, font=tkfont.Font(size=24),
                 bg=bg, fg=C_TEXT).grid(row=0, column=0, rowspan=2,
                                        padx=(12, 8), pady=10)
        tk.Label(inner, text=name, font=self.label_font,
                 bg=bg, fg=C_GOLD if active else C_TEXT,
                 anchor="w").grid(row=0, column=1, sticky="w", pady=(10, 0))
        tk.Label(inner, text=role, font=self.small_font,
                 bg=bg, fg=C_DIM, anchor="w",
                 wraplength=160).grid(row=1, column=1, sticky="w", pady=(0, 10))
        return frame

    def _set_card_active(self, turn):
        for card, active_turn in [(self.card_w, 'w'), (self.card_b, 'b')]:
            active = turn == active_turn
            bg = C_CARD_ACT if active else C_PANEL
            border = C_BORDER if active else "#2a3a5c"
            card.configure(bg=bg, highlightbackground=border)
            for w in card.winfo_children():
                w.configure(bg=bg)
                for c in w.winfo_children():
                    c.configure(bg=bg)
                    if isinstance(c, tk.Label):
                        if c.grid_info().get("row") == 0:
                            c.configure(fg=C_GOLD if active else C_TEXT)

    # ─── VẼ BÀN CỜ ───────────────────────────────────────────────────────────

    def _board_offset(self):
        return COORD_MARGIN, COORD_MARGIN

    def _draw_coords(self):
        ox, oy = self._board_offset()
        for c, ch in enumerate(FILES):
            cx = ox + c * SQ_SIZE + SQ_SIZE // 2
            self.canvas.create_text(cx, oy - 14, text=ch,
                                    font=self.coord_font, fill=C_DIM)
            self.canvas.create_text(cx, oy + BOARD_SIZE + 14, text=ch,
                                    font=self.coord_font, fill=C_DIM)
        for r in range(8):
            cy = oy + r * SQ_SIZE + SQ_SIZE // 2
            label = str(8 - r)
            self.canvas.create_text(ox - 14, cy, text=label,
                                    font=self.coord_font, fill=C_DIM)
            self.canvas.create_text(ox + BOARD_SIZE + 14, cy, text=label,
                                    font=self.coord_font, fill=C_DIM)

    def draw_board(self):
        self.canvas.delete("all")
        ox, oy = self._board_offset()
        board = self.ctrl.gs.board
        lm = self.last_move
        check_sq = self.ctrl.is_in_check()

        self._draw_coords()

        for r in range(8):
            for c in range(8):
                x1 = ox + c * SQ_SIZE
                y1 = oy + r * SQ_SIZE
                x2 = x1 + SQ_SIZE
                y2 = y1 + SQ_SIZE

                color = C_LIGHT if (r + c) % 2 == 0 else C_DARK
                if lm:
                    if (r, c) == lm[0]:
                        color = C_LAST_FROM
                    if (r, c) == lm[1]:
                        color = C_LAST_TO
                if check_sq and (r, c) == check_sq:
                    color = C_CHECK
                if self.selected and (r, c) == self.selected:
                    color = C_SELECT

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                if (r, c) in self.legal_sqrs:
                    cx, cy = x1 + SQ_SIZE // 2, y1 + SQ_SIZE // 2
                    if board[r][c]:
                        self.canvas.create_oval(x1 + 3, y1 + 3, x2 - 3, y2 - 3,
                                                outline=C_LEGAL, width=4, fill="")
                    else:
                        dot = SQ_SIZE // 5
                        self.canvas.create_oval(cx - dot, cy - dot, cx + dot, cy + dot,
                                                fill=C_LEGAL, outline="")

                p = board[r][c]
                if p:
                    self.canvas.create_text(
                        x1 + SQ_SIZE // 2, y1 + SQ_SIZE // 2,
                        text=UNICODE_PIECES.get(p, ''),
                        font=self.piece_font,
                        fill="#1a1a1a" if p.isupper() else "#ffffff",
                        tags="piece",
                    )

    # ─── XỬ LÝ CLICK ─────────────────────────────────────────────────────────

    def on_click(self, event):
        if self.ctrl.gs.turn != 'w':
            return
        ox, oy = self._board_offset()
        c = (event.x - ox) // SQ_SIZE
        r = (event.y - oy) // SQ_SIZE
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
        self.selected = (r, c)
        self.legal_sqrs = self.ctrl.get_legal_squares(r, c, 'w')
        self.draw_board()

    def _deselect(self):
        self.selected = None
        self.legal_sqrs = []
        self.draw_board()

    # ─── CALLBACKS TỪ CONTROLLER ─────────────────────────────────────────────

    def _on_move_done(self, fr, fc, tr, tc, who):
        self.last_move = ((fr, fc), (tr, tc))
        self.move_number = self.ctrl.move_number
        self.selected = None
        self.legal_sqrs = []
        self._log_move(fr, fc, tr, tc, who)
        self.draw_board()
        if who == 'w':
            self._set_card_active('b')
            self.update_status("⏳ AI đang suy nghĩ…")

    def _on_ai_done(self, fr, fc, tr, tc, elapsed):
        self.root.after(0, lambda: self._apply_ai_result(fr, fc, tr, tc, elapsed))

    def _apply_ai_result(self, fr, fc, tr, tc, elapsed):
        self.last_move = ((fr, fc), (tr, tc))
        self.move_number = self.ctrl.move_number
        self._log_move(fr, fc, tr, tc, 'b', elapsed)
        self.draw_board()
        self._set_card_active('w')
        self.update_status("Lượt của bạn. Click chọn quân.")

    def _on_game_over(self, result):
        if result == 'checkmate':
            winner = "Trắng" if self.ctrl.gs.turn == 'b' else "Đen"
            msg = f"♛ Chiếu hết!\n{winner} thắng!"
        else:
            msg = "½ Hòa!\nBếtắc (Stalemate)."
        self.root.after(0, lambda: self._show_popup(msg))

    # ─── TIỆN ÍCH UI ─────────────────────────────────────────────────────────

    def update_status(self, msg):
        self.status_var.set(msg)

    def _log_move(self, fr, fc, tr, tc, who, elapsed=None):
        from_sq = FILES[fc] + str(8 - fr)
        to_sq = FILES[tc] + str(8 - tr)
        n = (self.move_number + 1) // 2
        if who == 'w':
            entry = f"{n:>2}. {from_sq}→{to_sq}  "
        else:
            t = f"  ({elapsed:.1f}s)" if elapsed else ""
            entry = f"     {from_sq}→{to_sq}{t}\n"

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

        pw, ph = 320, 180
        top.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        sx = rx + (rw - pw) // 2
        sy = ry + (rh - ph) // 2
        top.geometry(f"{pw}x{ph}+{sx}+{sy}")

        box = tk.Frame(top, bg=C_PANEL, highlightthickness=1,
                       highlightbackground=C_BORDER)
        box.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(box, text=msg, font=self.label_font,
                 bg=C_PANEL, fg=C_GOLD, pady=24).pack()
        tk.Button(
            box, text="↺  Ván mới", font=self.label_font,
            bg=C_CARD_ACT, fg=C_GOLD, activebackground=C_GOLD,
            activeforeground=C_BG, relief="flat", bd=0, cursor="hand2",
            padx=16, pady=8,
            command=lambda: [top.destroy(), self.restart_game()],
        ).pack(pady=(0, 12))

    def restart_game(self):
        self.ctrl.restart()
        self.selected = None
        self.legal_sqrs = []
        self.last_move = None
        self.move_number = 0
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._set_card_active('w')
        self.draw_board()
        self.update_status("Ván mới bắt đầu! Lượt của bạn.")
