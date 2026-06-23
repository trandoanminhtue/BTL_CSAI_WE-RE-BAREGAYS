# opening_book.py
# Danh sách khai cuộc phổ biến, lưu dưới dạng:
# key   = tuple các nước đã đi (từ góc nhìn bàn cờ: "e2e4", "e7e5", ...)
# value = list các nước tiếp theo có thể chọn ngẫu nhiên (để AI không đơn điệu)
#
# Ký hiệu: "frfctrtc" = from_row from_col to_row to_col (tọa độ mảng 0-7)
# Ví dụ: e2e4 → hàng 6 cột 4 đến hàng 4 cột 4 → "6444"

import random


def _sq_to_rc(square):
    """'e4' -> (row, col) trong mảng board."""
    col = ord(square[0].lower()) - ord('a')
    row = 8 - int(square[1])
    return row, col


def move_key(from_sq, to_sq):
    """Chuyển e2-e4 sang key. Ví dụ: move_key('e2', 'e4') -> '6444'"""
    fr, fc = _sq_to_rc(from_sq)
    tr, tc = _sq_to_rc(to_sq)
    return f"{fr}{fc}{tr}{tc}"


def uci_moves(uci_string):
    """uci_moves('e2e4 e7e5 g1f3') -> ('6444', '1454', '7554')"""
    return tuple(move_key(u[0:2], u[2:4]) for u in uci_string.split())

# Quy ước: mỗi nước đi là chuỗi "frfctrtc"
# e2e4 = (6,4)->(4,4) = "6444"
# d2d4 = (6,3)->(4,3) = "6343"
# ...

OPENING_BOOK = {
    # Chỉ thêm key khi đến lượt ĐEN (1, 3, 5, ... nước trong lịch sử).

    # ══════════════════════════════════════════════════════════════════════════
    # 1. e4 — Phòng thủ đen (nước 1)
    # ══════════════════════════════════════════════════════════════════════════
    uci_moves("e2e4"): [
        move_key("e7", "e5"),   # Open Game
        move_key("c7", "c5"),   # Sicilian
        move_key("e7", "e6"),   # French
        move_key("c7", "c6"),   # Caro-Kann
        move_key("g8", "f6"),   # Alekhine
        move_key("d7", "d5"),   # Scandinavian
        move_key("d7", "d6"),   # Pirc / Philidor
    ],

    # ── Open Game ─────────────────────────────────────────────────────────────
    uci_moves("e2e4 e7e5 g1f3"): [
        move_key("b8", "c6"),
        move_key("g8", "f6"),   # Petrov
        move_key("d7", "d6"),   # Philidor
        move_key("f8", "c5"),
    ],
    uci_moves("e2e4 e7e5 g1f3 b8c6"): [
        move_key("f8", "b4"),   # Berlin / Nimzowitsch
        move_key("d7", "d6"),
    ],
    uci_moves("e2e4 e7e5 g1f3 b8c6 f1b5"): [
        move_key("a7", "a6"),   # Morphy Ruy Lopez
        move_key("g8", "f6"),   # Berlin
        move_key("f8", "e7"),
    ],
    uci_moves("e2e4 e7e5 g1f3 b8c6 f1c4"): [
        move_key("g8", "f6"),
        move_key("f8", "c5"),
    ],
    uci_moves("e2e4 e7e5 g1f3 b8c6 d2d4"): [
        move_key("e5", "d4"),   # ...exd4 Scotch
    ],
    uci_moves("e2e4 e7e5 g1f3 g8f6"): [
        move_key("d7", "d6"),
        move_key("b8", "c6"),
    ],
    uci_moves("e2e4 e7e5 b1c3"): [
        move_key("b8", "c6"),
        move_key("g8", "f6"),
    ],

    # ── Sicilian ────────────────────────────────────────────────────────────────
    uci_moves("e2e4 c7c5 g1f3"): [
        move_key("b8", "c6"),
        move_key("d7", "d6"),
        move_key("e7", "e6"),
        move_key("g7", "g6"),
    ],
    uci_moves("e2e4 c7c5 g1f3 b8c6 d2d4"): [
        move_key("c5", "d4"),   # ...cxd4
    ],
    uci_moves("e2e4 c7c5 g1f3 d7d6 d2d4"): [
        move_key("c5", "d4"),
    ],
    uci_moves("e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4"): [
        move_key("g8", "f6"),
        move_key("b8", "c6"),
    ],
    uci_moves("e2e4 c7c5 g1f3 b8c6 d2d4 c5d4 f3d4"): [
        move_key("g8", "f6"),
    ],

    # ── French ──────────────────────────────────────────────────────────────────
    uci_moves("e2e4 e7e6 d2d4"): [
        move_key("d7", "d5"),
    ],
    uci_moves("e2e4 e7e6 d2d4 d7d5 e4e5"): [
        move_key("c7", "c5"),
        move_key("b8", "c6"),
    ],
    uci_moves("e2e4 e7e6 d2d4 d7d5 b1c3"): [
        move_key("g8", "f6"),
        move_key("f8", "b4"),
    ],

    # ── Caro-Kann ───────────────────────────────────────────────────────────────
    uci_moves("e2e4 c7c6 d2d4"): [
        move_key("d7", "d5"),
    ],
    uci_moves("e2e4 c7c6 d2d4 d7d5 b1c3"): [
        move_key("g8", "f6"),
        move_key("e7", "e6"),
    ],
    uci_moves("e2e4 c7c6 d2d4 d7d5 e4e5"): [
        move_key("b8", "d7"),
        move_key("c8", "f5"),
    ],

    # ── Alekhine ────────────────────────────────────────────────────────────────
    uci_moves("e2e4 g8f6 e4e5"): [
        move_key("f6", "d5"),
        move_key("f6", "g4"),
    ],
    uci_moves("e2e4 g8f6 e4e5 f6d5"): [
        move_key("d7", "d6"),
        move_key("c7", "c6"),
    ],

    # ── Scandinavian ────────────────────────────────────────────────────────────
    uci_moves("e2e4 d7d5 e4d5"): [
        move_key("d8", "d5"),
        move_key("g8", "f6"),
    ],
    uci_moves("e2e4 d7d5 e4d5 d8d5"): [
        move_key("b8", "c6"),
        move_key("g8", "f6"),
    ],

    # ── Pirc ────────────────────────────────────────────────────────────────────
    uci_moves("e2e4 d7d6 d2d4"): [
        move_key("g8", "f6"),
        move_key("e7", "e5"),   # Philidor
    ],
    uci_moves("e2e4 d7d6 d2d4 g8f6 b1c3"): [
        move_key("g7", "g6"),
        move_key("c7", "c6"),
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # 1. d4 — Phòng thủ đen (nước 1)
    # ══════════════════════════════════════════════════════════════════════════
    uci_moves("d2d4"): [
        move_key("d7", "d5"),
        move_key("g8", "f6"),
        move_key("e7", "e6"),
        move_key("f7", "f5"),   # Dutch
        move_key("c7", "c5"),   # Benoni
        move_key("c7", "c6"),   # Slav
    ],

    # ── Queen's Gambit / Slav ───────────────────────────────────────────────────
    uci_moves("d2d4 d7d5 c2c4"): [
        move_key("c7", "c6"),   # Slav
        move_key("e7", "e6"),   # QGD
        move_key("d5", "c4"),   # QGA
        move_key("g8", "f6"),
    ],
    uci_moves("d2d4 d7d5 c2c4 c7c6 b1c3"): [
        move_key("g8", "f6"),
        move_key("e7", "e6"),
    ],
    uci_moves("d2d4 d7d5 c2c4 e7e6 b1c3"): [
        move_key("g8", "f6"),
        move_key("f8", "b4"),
    ],
    uci_moves("d2d4 d7d5 c2c4 d5c4 e2e3"): [
        move_key("b8", "c6"),
        move_key("g8", "f6"),
    ],

    # ── London System ───────────────────────────────────────────────────────────
    uci_moves("d2d4 d7d5 c1f4"): [
        move_key("g8", "f6"),
        move_key("c7", "c5"),
        move_key("e7", "e6"),
    ],
    uci_moves("d2d4 d7d5 c1f4 g8f6 e2e3"): [
        move_key("e7", "e6"),
        move_key("c7", "c5"),
        move_key("c8", "f5"),
    ],
    uci_moves("d2d4 d7d5 e2e3 g8f6"): [
        move_key("c7", "c5"),
        move_key("e7", "e6"),
        move_key("c8", "f5"),
    ],

    # ── Indian Defenses ─────────────────────────────────────────────────────────
    uci_moves("d2d4 g8f6 c2c4"): [
        move_key("e7", "e6"),   # Nimzo / QI
        move_key("g7", "g6"),   # King's Indian
        move_key("c7", "c5"),   # Benoni
    ],

    # ── King's Indian ───────────────────────────────────────────────────────────
    uci_moves("d2d4 g8f6 c2c4 g7g6 b1c3"): [
        move_key("f8", "g7"),
    ],
    uci_moves("d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4"): [
        move_key("d7", "d6"),
        move_key("e7", "e5"),   # ...e5 KID
    ],
    uci_moves("d2d4 g8f6 c2c4 g7g6 g1f3 f8g7"): [
        move_key("b1", "c3"),
        move_key("d7", "d6"),
    ],

    # ── Nimzo / Queen's Indian ──────────────────────────────────────────────────
    uci_moves("d2d4 g8f6 c2c4 e7e6 b1c3"): [
        move_key("f8", "b4"),   # Nimzo
        move_key("b7", "b6"),   # Queen's Indian
    ],
    uci_moves("d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 e2e3"): [
        move_key("c7", "c5"),
        move_key("b8", "c6"),
    ],
    uci_moves("d2d4 g8f6 c2c4 e7e6 b1c3 b7b6 g1f3"): [
        move_key("f8", "b7"),
        move_key("c8", "b7"),
    ],

    # ── Benoni ──────────────────────────────────────────────────────────────────
    uci_moves("d2d4 g8f6 c2c4 c7c5 d4d5"): [
        move_key("e7", "e6"),
        move_key("g7", "g6"),
    ],

    # ── Dutch ───────────────────────────────────────────────────────────────────
    uci_moves("d2d4 f7f5 c2c4"): [
        move_key("g8", "f6"),
        move_key("e7", "e6"),
    ],
    uci_moves("d2d4 f7f5 c2c4 g8f6 b1c3"): [
        move_key("e7", "e6"),
        move_key("g7", "g6"),
    ],

    # ── Slav via 1.d4 c6 ────────────────────────────────────────────────────────
    uci_moves("d2d4 c7c6 c2c4"): [
        move_key("d7", "d5"),
        move_key("g8", "f6"),
    ],
    uci_moves("d2d4 c7c6 c2c4 d7d5 g1f3"): [
        move_key("g8", "f6"),
        move_key("c8", "f5"),
    ],
}


def get_opening_move(move_history):
    """
    Tra cứu opening book theo lịch sử nước đi.
    move_history: list các tuple (fr,fc,tr,tc) — tất cả nước đi từ đầu ván.
    Trả về (fr,fc,tr,tc) nếu có trong sách, None nếu không.
    """
    # Chuyển lịch sử thành key dạng chuỗi
    key = tuple(f"{fr}{fc}{tr}{tc}" for fr, fc, tr, tc in move_history)

    candidates = OPENING_BOOK.get(key)
    if not candidates:
        return None

    # Chọn ngẫu nhiên trong danh sách để AI không đơn điệu
    chosen = random.choice(candidates)
    fr, fc, tr, tc = int(chosen[0]), int(chosen[1]), int(chosen[2]), int(chosen[3])
    return (fr, fc, tr, tc)