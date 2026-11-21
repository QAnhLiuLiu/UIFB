# FarmBot UI – điều khiển ruộng + nhận diện xà lách / cỏ dại bằng AI

Giao diện web điều khiển FarmBot (gieo hạt, tưới, phun thuốc, dò ruộng) kèm nhận diện cây trực tiếp từ webcam
bằng 3 model đã huấn luyện: **YOLO** (nhanh), **Grounding DINO chỉ xà lách** và **Grounding DINO xà lách + cỏ dại**.
Model chạy trên máy của bạn qua một server Python nhỏ; giao diện mở bằng trình duyệt.

> Giao diện mặc định ở **chế độ mô phỏng** (chưa gửi lệnh tới bot thật) – xem [Nối bot thật](#nối-bot-thật).

## Yêu cầu

| | |
|---|---|
| Hệ điều hành | Windows 10 / 11, 64-bit |
| Python | **3.14** – tải ở <https://www.python.org/downloads/>, khi cài **tick "Add python.exe to PATH"** |
| Card đồ họa | Nên có **NVIDIA** (đã cài driver). Không có thì vẫn chạy bằng CPU: YOLO dùng được, DINO rất chậm |
| Trình duyệt | Chrome hoặc Edge |
| Mạng | Cần cho lần cài đầu (tải khoảng 3 GB thư viện) |

## 1. Tải về

1. Ở trang repo bấm **Code → Download ZIP**, giải nén ra một chỗ cố định (ví dụ Desktop).
2. **Tải model DINO** (không bắt buộc nếu chỉ dùng YOLO): vào mục **Releases** ở cột bên phải trang repo, mở bản mới nhất,
   tải 2 file:
   - `dino_chi_xa_lach.safetensors`
   - `dino_xa_lach_co_dai.safetensors`

   rồi chép **cả 2 file vào thư mục `models`** (để nguyên tên, không cần đổi). Lần chạy tới, `2_CHAY.bat` tự xếp chúng vào đúng chỗ.

## 2. Cài đặt (chỉ làm 1 lần)

Bấm đúp **`1_CAI_DAT.bat`** và chờ tới khi hiện `CAI DAT XONG` (10–30 phút tùy mạng).
File này tạo môi trường Python riêng trong thư mục `.venv` và tự chọn PyTorch bản GPU (nếu có card NVIDIA) hoặc bản CPU.

## 3. Chạy

1. Bấm đúp **`2_CHAY.bat`**. Một cửa sổ đen hiện ra – đó là server nhận diện, **để nguyên, đừng tắt**.
2. Sau khoảng 8 giây trình duyệt tự mở <http://127.0.0.1:8001/> (báo lỗi thì đợi thêm vài giây rồi bấm **F5**).
3. Thẻ **🧠 Mô hình nhận diện**: chọn model rồi bấm **Tải model**

   | Model | Nhận diện | Cần |
   |---|---|---|
   | YOLO – chỉ xà lách (nhanh) | xà lách | máy nào cũng chạy được |
   | DINO – chỉ xà lách (chính xác) | xà lách | card NVIDIA |
   | DINO – xà lách + cỏ dại | xà lách + cỏ dại (khung đỏ, có cảnh báo đỏ) | card NVIDIA |

4. Thẻ **📷 Camera thực tế** → **Bật camera** → cho phép trình duyệt dùng camera. Cây được đóng khung trực tiếp trên hình.
5. Dùng xong: đóng cửa sổ đen.

## Dùng giao diện

- **Gieo / Tưới / Phun:** chọn chức năng bên trái rồi bấm vào ruộng → ô được thêm vào **hàng chờ**; sửa X, Y, Z nếu cần,
  bấm **✅ Xác nhận** thì bot mới chạy. **E-STOP** (góc phải trên) dừng khẩn cấp.
- **FarmBot:** bấm vào ruộng để đưa bot tới điểm đó, hoặc **🐍 Dò toàn ruộng** – bot tự đi hết các ô (trái → phải, xuống 1 ô,
  phải → trái…); cỏ dại camera thấy trong lúc dò được đánh dấu ⚠ lên bản đồ.
- **💡 Đề xuất:** bấm để xem các ô trống nên gieo và việc nên làm tiếp (tưới, phun cỏ dại, dò ruộng…).
- **💬 Trợ lý chat** (góc phải dưới hoặc phím `/`): ra lệnh bằng tiếng Việt, ví dụ `tưới tất cả cây`, `dò toàn ruộng`,
  `gieo ô đề xuất`; gõ `trợ giúp` để xem tất cả lệnh.
- Đơn vị: **mm**. Ruộng mặc định 300 × 300 mm, đổi ở thẻ **⚙️ Cài đặt**.

## Nối bot thật

Mở `index.html` bằng Notepad, điền địa chỉ server của bot vào dòng

```js
const BOT_URL = '';      // vd 'http://raspberrypi.local:8000/command'
const SENSOR_URL = '';   // (nếu có cảm biến) trả JSON {"soil": 42, "humidity": 65, "temperature": 28.5}
```

lưu lại rồi tải lại trang. Lệnh gửi đi dạng `{"kind": "move_absolute", "args": {"x":…, "y":…, "z":…}}`,
`{"kind": "write_pin", …}`, `{"kind": "emergency_stop", …}`. Chân van/bơm đặt ở dòng `const PINS = …`.

## Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `Chua co Python 3.14` | Cài Python 3.14 (tick "Add python.exe to PATH") rồi chạy lại `1_CAI_DAT.bat` |
| `2_CHAY.bat` báo `Chua cai dat` | Chạy `1_CAI_DAT.bat` trước |
| Model DINO hiện "(thiếu file model)" | Chưa tải 2 file DINO ở mục Releases vào thư mục `models` (bước 1.2) |
| Tải DINO báo hết bộ nhớ (out of memory) | Card đồ họa không đủ VRAM – dùng YOLO |
| Không thấy hình camera | Cho phép quyền camera trong trình duyệt, chọn đúng camera trong danh sách |
| Báo cổng 8001 đang bị dùng | Đóng cửa sổ đen cũ rồi chạy lại `2_CHAY.bat` |

## Cấu trúc thư mục

```
index.html            giao diện
1_CAI_DAT.bat         cài đặt (1 lần)
2_CHAY.bat            chạy server + mở giao diện
server/               server nhận diện (FastAPI): detect_server.py, detectors.py, gdino_utils.py
models/               yolo_xa_lach.pt + 2 thư mục DINO (file .safetensors tải ở Releases)
requirements.txt      thư viện Python
```

## Giấy phép dữ liệu

Model cỏ dại được huấn luyện có dùng bộ dữ liệu **CropAndWeed** (giấy phép chỉ dùng cho nghiên cứu, phi thương mại)
và **LACSA**. Chỉ dùng các model này cho mục đích học tập / nghiên cứu.
