# ai_hybrid.py — Đánh giá lai: Neural net + PST + heuristic (tự fallback nếu thiếu model)

from src.ai.ai_eval import evaluate_pst, evaluate_heuristics, evaluate_full

_NEURAL = None          # 'ok' | 'missing' | 'error'
_NEURAL_EVAL = None


def _init_neural():
    global _NEURAL, _NEURAL_EVAL
    if _NEURAL is not None:
        return
    try:
        from src.ai import ai_neural
        _NEURAL_EVAL = ai_neural.evaluate
        _NEURAL = 'ok'
    except (ImportError, FileNotFoundError, OSError):
        _NEURAL = 'missing'
        _NEURAL_EVAL = None


def evaluate(board):
    """
    Hàm đánh giá chính (centipawn, dương = lợi Trắng).

    Có model:  60% neural + 25% PST + 15% heuristic
    Không có:  PST + heuristic (evaluate_full)
    """
    _init_neural()
    heur = evaluate_heuristics(board)

    if _NEURAL == 'ok' and _NEURAL_EVAL is not None:
        try:
            neural = _NEURAL_EVAL(board)
            pst = evaluate_pst(board)
            return int(neural * 0.60 + pst * 0.25 + heur * 0.15)
        except (ImportError, FileNotFoundError, OSError, RuntimeError):
            pass

    return evaluate_full(board)
