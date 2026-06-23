# ai_eval.py — Hàm đánh giá nâng cao: PST + heuristic chiến thuật

from src.engine.constant import PIECE_VALUE, PST_OPENING, PST_ENDGAME
from src.engine.rules import is_white, is_black, is_attacked, find_king


def get_phase(board):
    """0.0 = cờ tàn, 1.0 = khai cuộc/trung cuộc (dựa trên quân nhẹ còn lại)."""
    total = 0
    for row in board:
        for p in row:
            if p and p.upper() not in ('K', 'P'):
                total += PIECE_VALUE[p.upper()]
    return max(0.0, min(1.0, total / 7800))


def evaluate_pst(board):
    """Material + bảng vị trí phase-blended (centipawn, dương = lợi Trắng)."""
    phase = get_phase(board)
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p:
                continue
            pt = p.upper()
            white = is_white(p)
            idx = r * 8 + c if white else (7 - r) * 8 + c
            val = PIECE_VALUE[pt]
            o = PST_OPENING.get(pt)
            e = PST_ENDGAME.get(pt)
            if o and e:
                val += int(o[idx] * phase + e[idx] * (1 - phase))
            elif o:
                val += o[idx]
            score += val if white else -val
    return score


def _pawn_file_counts(board):
    """Trả về (white_files, black_files): mỗi phần tử là list 8 cột đếm số tốt."""
    wf = [0] * 8
    bf = [0] * 8
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == 'P':
                wf[c] += 1
            elif p == 'p':
                bf[c] += 1
    return wf, bf


def _is_passed(board, r, c, white):
    enemy = 'p' if white else 'P'
    if white:
        for rr in range(0, r):
            for dc in (-1, 0, 1):
                cc = c + dc
                if 0 <= cc < 8 and board[rr][cc] == enemy:
                    return False
        return True
    for rr in range(r + 1, 8):
        for dc in (-1, 0, 1):
            cc = c + dc
            if 0 <= cc < 8 and board[rr][cc] == enemy:
                return False
    return True


def _evaluate_pawns(board):
    """Cấu trúc tốt: tốt lẹt, tốt cô lập, tốt thông, tốt passed."""
    score = 0
    wf, bf = _pawn_file_counts(board)

    for c in range(8):
        if wf[c] > 1:
            score -= 15 * (wf[c] - 1)
        if bf[c] > 1:
            score += 15 * (bf[c] - 1)

    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p not in ('P', 'p'):
                continue
            white = p == 'P'
            files = wf if white else bf
            opp_files = bf if white else wf

            isolated = files[c] == 1 and (c == 0 or files[c - 1] == 0) and (c == 7 or files[c + 1] == 0)
            if isolated:
                score += -20 if white else 20

            if _is_passed(board, r, c, white):
                rank_bonus = r if white else (7 - r)
                bonus = 20 + rank_bonus * 15
                score += bonus if white else -bonus

    return score


def _evaluate_bishops(board):
    """Thưởng cặp tượng."""
    score = 0
    if sum(1 for row in board for p in row if p == 'B') >= 2:
        score += 30
    if sum(1 for row in board for p in row if p == 'b') >= 2:
        score -= 30
    return score


def _file_has_pawn(board, col, white):
    target = 'P' if white else 'p'
    return any(board[r][col] == target for r in range(8))


def _evaluate_rooks(board):
    """Xe trên cột mở / bán mở."""
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p not in ('R', 'r'):
                continue
            white = p == 'R'
            w_pawn = _file_has_pawn(board, c, True)
            b_pawn = _file_has_pawn(board, c, False)
            if not w_pawn and not b_pawn:
                bonus = 25
            elif (white and not w_pawn) or (not white and not b_pawn):
                bonus = 12
            else:
                bonus = 0
            score += bonus if white else -bonus
    return score


def _king_zone_penalty(board, turn):
    """Phạt khi vua bị nhiều quân địch bao vây (king safety)."""
    kr = find_king(board, turn)
    if not kr:
        return 0
    kr_r, kr_c = kr
    opp = 'b' if turn == 'w' else 'w'
    attackers = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = kr_r + dr, kr_c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                p = board[rr][cc]
                if p and ((turn == 'w' and is_black(p)) or (turn == 'b' and is_white(p))):
                    attackers += 1
    if is_attacked(board, kr_r, kr_c, turn):
        attackers += 2
    return attackers * 12


def _evaluate_king_safety(board, phase):
    """An toàn vua — quan trọng hơn ở khai cuộc/trung cuộc."""
    weight = 0.5 + 0.5 * phase
    w_pen = _king_zone_penalty(board, 'w')
    b_pen = _king_zone_penalty(board, 'b')
    return int((b_pen - w_pen) * weight)


def _evaluate_mobility(board):
    """Mobility đơn giản: số ô tấn công của quân (pseudo), không cần full legal."""
    from src.engine.rules import pseudo_moves

    score = 0
    weights = {'P': 1, 'N': 3, 'B': 3, 'R': 2, 'Q': 1, 'K': 0}
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p:
                continue
            pt = p.upper()
            w = weights.get(pt, 0)
            if w == 0:
                continue
            turn = 'w' if is_white(p) else 'b'
            n = len(pseudo_moves(board, r, c, turn, None, {}))
            score += n * w if is_white(p) else -n * w
    return score


def evaluate_heuristics(board):
    """Các yếu tố chiến thuật bổ sung (centipawn)."""
    phase = get_phase(board)
    return (
        _evaluate_pawns(board)
        + _evaluate_bishops(board)
        + _evaluate_rooks(board)
        + _evaluate_king_safety(board, phase)
        + _evaluate_mobility(board) // 2
    )


def evaluate_full(board):
    """PST + heuristic — dùng khi không có neural net."""
    return evaluate_pst(board) + evaluate_heuristics(board)
