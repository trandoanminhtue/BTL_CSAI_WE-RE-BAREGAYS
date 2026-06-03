# BTL_CSAI_WE-RE-BAREGAYS

## Tổng quan dự án
Ứng dụng cờ vua `Chess vs AI` sử dụng giao diện Tkinter, engine sinh nước đi và AI Minimax/Alpha-Beta. Dự án cho phép chơi Trắng vs Đen, AI lựa chọn nước đi bằng Minimax kết hợp bảng khai cuộc, bảng chuyển vị và đánh giá thế cờ.

## Cấu trúc dự án
Dưới đây là cấu trúc thư mục của dự án tương đương `tree /f`:

```
BTL_CSAI_WE-RE-BAREGAYS
│   main.py
│   README.md
│   requirements.txt
│
├── models
│       chess_model.pt
│
└── src
    ├── ai
    │       ai.py
    │       ai_neural.py
    │       ai_pst.py
    │       __init__.py
    ├── controller
    │       game_controller.py
    │       __init__.py
    ├── engine
    │       constant.py
    │       engine.py
    │       game_state.py
    │       rules.py
    │       __init__.py
    ├── gui
    │       app.py
    │       __init__.py
    └── utils
            opening_book.py
            __init__.py
```

## Luồng dữ liệu chính
1. `main.py` khởi tạo Tkinter và tạo `ChessApp`.
2. `ChessApp` xây dựng giao diện, giữ trạng thái lựa chọn ô và gọi `GameController`.
3. Khi người chơi click, `app.py` gọi `ctrl.do_player_move(...)`.
4. `GameController` kiểm tra tính hợp lệ bằng `src.engine.rules`, cập nhật trạng thái, rồi gọi AI nếu cần.
5. `AI` nằm trong `src.ai.ai.py`: nó lấy nước đi tốt nhất bằng `get_best_move(...)`.
6. Nếu có khai cuộc trong `src.utils.opening_book.py`, AI dùng trước.
7. Nếu không, AI chạy `minimax(...)` với Alpha-Beta và bảng chuyển vị.
8. Kết quả AI trả về `GameController`, cập nhật `GameState`, rồi callback về GUI để vẽ lại bàn cờ.

## Thành phần chính và công dụng

### `main.py`
- Điểm vào chương trình.
- Khởi động Tkinter và tạo `ChessApp`.

### `src/gui/app.py`
- Vẽ bàn cờ, quân cờ, trạng thái và lịch sử nước đi.
- Xử lý sự kiện click chuột.
- Gọi `GameController` để thực thi nước đi người chơi.
- Hiển thị ô được chọn, ô hợp lệ, nước đi cuối và chiếu.

### `src/controller/game_controller.py`
- Điều phối ván đấu và trạng thái game.
- Thực thi nước đi người chơi và AI.
- Gọi `all_legal_moves`, `apply_move`, `legal_moves` để xác nhận nước đi.
- Cập nhật `GameState`: `board`, `turn`, `en_passant`, `castling`, `move_history`.
- Kiểm tra kết thúc ván: `checkmate` hoặc `stalemate`.
- Chạy AI trên thread riêng để không block GUI.

### `src/engine/game_state.py`
- Lưu cấu hình ván cờ ban đầu.
- `board`: danh sách 8×8 chứa ký tự quân cờ.
- `turn`: lượt hiện tại `'w'` hoặc `'b'`.
- `castling`: quyền nhập thành.
- `en_passant`: ô có thể bị bắt tốt qua đường.
- `move_history`: lịch sử nước đi.

### `src/engine/rules.py`
- Làm tất cả logic luật cờ.
- `pseudo_moves(...)`: sinh nước đi lý thuyết của quân cờ.
- `legal_moves(...)`: lọc nước đi không để vua bị chiếu.
- `all_legal_moves(...)`: tổng hợp toàn bộ nước đi hợp lệ của phe đang đi.
- `apply_move(...)`: thực thi nước đi trên bản sao bàn cờ.
- `is_attacked(...)`: kiểm tra ô có bị đối phương tấn công.
- `find_king(...)`: tìm vị trí vua.
- Các luật đặc biệt: nhập thành (`castle`), bắt tốt qua đường (`ep`), phong cấp tốt.

### `src/ai/ai.py`
- Hàm trung tâm của AI.
- `get_best_move(...)`: ưu tiên mở sách khai cuộc, nếu không có thì dùng Minimax.
- Minimax với Alpha-Beta, bảng chuyển vị và sắp xếp nước đi.
- `order_moves(...)`: ưu tiên nước ăn quân, nhập thành, bắt tốt, phong cấp.
- Bảng chuyển vị `_tt`: tránh tính lại trạng thái đã duyệt.

### `src/ai/ai_pst.py`
- Hàm `evaluate(board)` dựa trên giá trị quân và bảng vị trí PST.
- `get_phase(board)`: xác định giai đoạn ván cờ:
  - `phase = total / 7800`
  - `total` là tổng giá trị quân nhẹ (không tính K, P).
  - Giá trị giai đoạn được chuẩn hoá trong `[0.0, 1.0]`.
- Giá trị thế cờ = `material + positional`.
- Bảng `PST_OPENING` / `PST_ENDGAME` cho từng quân và vị trí ô.

### `src/ai/ai_neural.py`
- Dùng mạng neuron nếu có `models/chess_model.pt`.
- Chuyển `board` sang tensor 12 kênh.
- Mạng CNN dự đoán giá trị `score` rồi scale thành centipawn.
- Nếu không có PyTorch, cần cài `torch`.

### `src/utils/opening_book.py`
- Lưu các khai cuộc phổ biến theo chuỗi nước đi.
- `get_opening_move(...)` tìm nước đi tiếp theo dựa trên lịch sử.
- Trả về nước đi ngẫu nhiên trong danh sách ứng viên.

## Logic và công thức quan trọng

### Luật nước đi và đánh giá hợp lệ
- `pseudo_moves`: sinh nước đi theo luật từng quân.
- `legal_moves`: với mỗi nước đi giả định, `apply_move(...)` rồi kiểm tra:
  - `find_king(nb, t)` xác định vị trí Vua sau nước đi.
  - `not is_attacked(nb, kr[0], kr[1], t)` đảm bảo Vua không bị chiếu.

### `apply_move(...)`
- Sao chép bàn cờ: `b = [row[:] for row in board]`.
- Di chuyển quân và xóa ô cũ.
- Xử lý `flag == 'castle'`: di chuyển thêm Xe.
- Xử lý `flag == 'ep'`: xóa tốt bị bắt qua đường.
- Phong cấp: tốt đến hàng cuối chuyển thành Hậu.

### Minimax + Alpha-Beta
- `minimax(board, depth, alpha, beta, is_max, t, en_passant, castling)`.
- Nếu `depth == 0`, trả về `evaluate(board)`.
- Tính tất cả nước đi hợp lệ `all_legal_moves(...)`.
- Nếu không có nước đi:
  - `checkmate` nếu vua bị chiếu → trả `-99999` cho max, `+99999` cho min.
  - `stalemate` nếu không chiếu → trả `0`.

Công thức cơ bản:
- Max node: `best = max(best, score)`
- Min node: `best = min(best, score)`
- Alpha-Beta:
  - `alpha = max(alpha, best)` tại Max node
  - `beta = min(beta, best)` tại Min node
  - prune khi `beta <= alpha`

### Bảng chuyển vị (Transposition Table)
- Key: `(_hash_board(board), depth, is_max)`.
- Giá trị lưu: `(score, best_move, flag)`.
- Flag:
  - `exact`: giá trị chính xác.
  - `lower`: giá trị là lower bound.
  - `upper`: giá trị là upper bound.
- Khi truy bảng: cập nhật `alpha` / `beta` và prune nếu có thể.

### Sắp xếp nước đi
Điểm nước đi được tính bằng hàm `_move_score(...)`:
- Nếu ăn quân: `+10 * giá trị quân bị ăn - giá trị quân đi` (MVV-LVA).
- `flag == 'castle'` → +60.
- `flag == 'ep'` → +105.
- Phong cấp tốt → +800.

### Hàm đánh giá thế cờ PST
Trong `ai_pst.py`:
- `phase = max(0.0, min(1.0, total / 7800))`
- Tổng điểm cho mỗi quân:
  - `val = PIECE_VALUE[pt]`
  - `idx = r * 8 + c if white else (7-r) * 8 + c`
  - `val += int(o[idx] * phase + e[idx] * (1-phase))`
- Tổng thế cờ: `score += val if white else -val`
- Kết quả dương ưu lợi cho Trắng; âm ưu lợi cho Đen.

### Hàm đánh giá neural
- Chuyển board sang tensor 12 kênh với `PIECE_IDX`.
- Đầu ra mạng là số thực.
- Scale
  - `score = model(tensor).item()`
  - `return score * 100`

## Chạy ứng dụng
- Cài đặt môi trường Python và yêu cầu trong `requirements.txt`.
- Chạy `python main.py`.

## Ghi chú
- AI hiện tại mặc định dùng `ai_neural.py` nếu có model trong `models/chess_model.pt`.
- Nếu không muốn dùng neural net, đổi import trong `src/ai/ai.py` thành `from src.ai.ai_pst import evaluate`.
- `AI_DEPTH = 3` trong `src/controller/game_controller.py` điều khiển độ sâu tìm kiếm.

---

Phiên bản README này mô tả rõ cấu trúc dự án, luồng dữ liệu, công dụng từng phần và các công thức thuật toán quan trọng.

