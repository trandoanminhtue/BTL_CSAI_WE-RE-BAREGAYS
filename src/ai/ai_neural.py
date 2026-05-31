# ai_neural.py
# Thay thế hàm evaluate() trong ai.py bằng mạng neuron đã train.
# Dùng khi đã có file chess_model.pt từ Kaggle.
#
# Cách dùng: đặt chess_model.pt cùng thư mục với file này.

import os
import numpy as np

# Import torch lazy — chỉ báo lỗi khi gọi evaluate(), không crash khi import
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ─── KIẾN TRÚC MODEL (phải khớp y hệt lúc train trên Kaggle) ─────────────────
class ChessNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(12, 64,  3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
            nn.Conv2d(128,128, 3, padding=1), nn.ReLU(),
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 256), nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        return self.fc(self.conv(x)).squeeze(-1)


# ─── LOAD MODEL (1 LẦN KHI KHỞI ĐỘNG) ───────────────────────────────────────
PIECE_IDX = {
    'P':0,'N':1,'B':2,'R':3,'Q':4,'K':5,
    'p':6,'n':7,'b':8,'r':9,'q':10,'k':11
}

_model  = None   # Cache model, không load lại mỗi lần gọi
_device = None

def _load_model():
    """Load chess_model.pt vào bộ nhớ. Gọi 1 lần duy nhất."""
    global _model, _device

    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch chưa được cài. Chạy: pip install torch")

    model_path = os.path.join(os.path.dirname(__file__),'..', '..', 'models', 'chess_model.pt')
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Không tìm thấy chess_model.pt tại {model_path}\n"
            "Hãy download model từ Kaggle và đặt vào thư mục project."
        )

    _device = torch.device('cpu')   # App chạy trên CPU, không cần GPU
    _model  = ChessNet().to(_device)
    _model.load_state_dict(torch.load(model_path, map_location=_device))
    _model.eval()   # Tắt Dropout khi inference
    print(f"[ai_neural] Loaded chess_model.pt")


# ─── CHUYỂN BOARD → TENSOR ───────────────────────────────────────────────────
def _board_to_tensor(board):
    """
    Chuyển board 8×8 (list of list) sang tensor (1, 12, 8, 8).
    12 kênh: P N B R Q K p n b r q k
    """
    t = np.zeros((12, 8, 8), dtype=np.float32)
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p in PIECE_IDX:
                t[PIECE_IDX[p], r, c] = 1.0
    return torch.tensor(t).unsqueeze(0)   # (1, 12, 8, 8)


# ─── HÀM ĐÁNH GIÁ CHÍNH ──────────────────────────────────────────────────────
def evaluate(board):
    """
    Thay thế hàm evaluate() PST trong ai.py.
    Nhận board 8×8, trả về điểm số (centipawn):
      Dương → có lợi cho Trắng
      Âm    → có lợi cho Đen
    """
    global _model

    # Load model lần đầu tiên
    if _model is None:
        _load_model()

    with torch.no_grad():
        tensor = _board_to_tensor(board).to(_device)
        score  = _model(tensor).item()   # số thực trong [-15, +15] (pawn units)

    # Scale về centipawn để khớp với hệ thống điểm của Minimax
    return score * 100
