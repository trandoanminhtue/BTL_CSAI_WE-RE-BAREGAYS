# opening_book.py
# Danh sách khai cuộc phổ biến, lưu dưới dạng:
# key   = tuple các nước đã đi (từ góc nhìn bàn cờ: "e2e4", "e7e5", ...)
# value = list các nước tiếp theo có thể chọn ngẫu nhiên (để AI không đơn điệu)
#
# Ký hiệu: "frfctrtc" = from_row from_col to_row to_col (tọa độ mảng 0-7)
# Ví dụ: e2e4 → hàng 6 cột 4 đến hàng 4 cột 4 → "6444"

import random

# Quy ước: mỗi nước đi là chuỗi "frfctrtc"
# e2e4 = (6,4)->(4,4) = "6444"
# d2d4 = (6,3)->(4,3) = "6343"
# ...

OPENING_BOOK = {
    # ── SAU KHI TRẮNG ĐI e4 ──────────────────────────────────────────────────
    ("6444",): [           # Trắng: e4
        "1454",            # e5 (Ruy Lopez / Italian)
        "1343",            # d5 (Scandinavian)
        "0215",            # Nf6 (Alekhine)
        "1344",            # c5 (Sicilian)
        "1253",            # e6 (French)
    ],
    ("6444","1454"): [     # Trắng e4, Đen e5
        "7352",            # Nc3 (Vienna)
        "7554",            # Nf3 (Ruy Lopez / Italian)
        "6343",            # d4 (Center)
    ],
    ("6444","1454","7554"): [   # e4 e5 Nf3
        "0216",            # Nc6
        "0125",            # Nf6 (Petrov)
    ],
    ("6444","1454","7554","0216"): [  # e4 e5 Nf3 Nc6
        "6555",            # Bb5 (Ruy Lopez)
        "6253",            # Bc4 (Italian)
        "6343",            # d4 (Scotch)
    ],

    # ── SAU KHI TRẮNG ĐI d4 ──────────────────────────────────────────────────
    ("6343",): [           # Trắng: d4
        "1343",            # d5 (Queen's Gambit / Slav)
        "0215",            # Nf6 (Indian defenses)
        "1253",            # e6
    ],
    ("6343","1343"): [     # d4 d5
        "6242",            # c4 (Queen's Gambit)
        "7352",            # Nc3
        "6555",            # Bf4 (London)
        "6454",            # e3 (London)
    ],
    ("6343","1343","6242"): [   # d4 d5 c4 — Queen's Gambit
        "1252",            # c6 (Slav)
        "1253",            # e6 (QGD)
        "1242",            # dxc4 (QGA)
    ],
    ("6343","0215"): [     # d4 Nf6
        "6242",            # c4 (Indian)
        "7352",            # Nc3
        "6555",            # Bf4 (London)
    ],
    ("6343","0215","6242"): [   # d4 Nf6 c4
        "1253",            # e6 (Nimzo / Queen's Indian)
        "1243",            # g6 (King's Indian)
        "1252",            # c5 (Benoni)
    ],

    # ── SICILIAN (e4 c5) ──────────────────────────────────────────────────────
    ("6444","1344"): [     # e4 c5 (Sicilian)
        "7554",            # Nf3
        "7352",            # Nc3
    ],
    ("6444","1344","7554"): [   # e4 c5 Nf3
        "0216",            # Nc6
        "1343",            # d6
        "1253",            # e6
    ],
    ("6444","1344","7554","0216"): [
        "6343",            # d4 (Open Sicilian)
        "6252",            # Bb5 (Rossolimo)
    ],

    # ── FRENCH (e4 e6) ────────────────────────────────────────────────────────
    ("6444","1253"): [     # e4 e6
        "6343",            # d4
    ],
    ("6444","1253","6343"): [
        "1343",            # d5
    ],
    ("6444","1253","6343","1343"): [
        "7352",            # Nc3 (Classical)
        "6544",            # e5 (Advance)
        "7453",            # Nd2 (Tarrasch)
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