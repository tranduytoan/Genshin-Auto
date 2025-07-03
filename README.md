# Genshin Auto Daily Check-in

Tự động điểm danh hàng ngày cho Genshin Impact thông qua GitHub Actions hoặc chạy local.

## ✨ Tính năng

- 🤖 Tự động điểm danh hàng ngày
- ☁️ Chạy trên GitHub Actions (không cần máy tính)
- 🖥️ Hỗ trợ chạy local trên Windows
- 📊 Lưu log chi tiết trên GitHub Gist
- 🎮 Tích hợp với launcher game (chạy local)

## 🚀 Cách sử dụng

### Phương pháp 1: GitHub Actions (Khuyến nghị)

1. **Fork repository này về tài khoản GitHub của bạn**

2. **Cấu hình Secrets trong GitHub:**
   - Vào `Settings` > `Secrets and variables` > `Actions`
   - Thêm các secrets sau:
     - `ACT_ID`: ID hoạt động từ URL check-in
     - `COOKIE`: Cookie từ trình duyệt
     - `API_URL`: `https://sg-hk4e-api.hoyolab.com/event/sol/sign?lang=vi-vn`
     - `METRICS_TOKEN`: GitHub Personal Access Token (optional, để upload log)
     - `GIST_ID`: ID của Gist để lưu log (optional)

3. **Kích hoạt GitHub Actions:**
   - Vào tab `Actions` > `Enable workflows`
   - Workflow sẽ chạy tự động mỗi ngày lúc 8:00 AM UTC

### Phương pháp 2: Chạy Local

1. **Cài đặt:**
   ```bash
   git clone https://github.com/your-username/Genshin-Auto-Daily.git
   cd Genshin-Auto-Daily
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Cấu hình:**
   - Copy `.env.example` thành `.env`
   - Điền thông tin `ACT_ID`, `COOKIE`, `APP_PATH` vào file `.env`

3. **Chạy:**
   - Chạy trực tiếp: `python local/dailyCheckin.py`
   - Chạy với launcher: Double-click `local/genshin.bat`

## 🔧 Lấy thông tin cần thiết

### ACT_ID và COOKIE:
1. Truy cập [Hoyolab](https://www.hoyolab.com/genshin/)
2. Đăng nhập tài khoản Genshin
3. Vào trang check-in
4. **ACT_ID**: Lấy từ URL `?act_id=xxxxxxxxxxxxxxxx`
5. **COOKIE**: 
   - Nhấn F12 > Network > Refresh trang
   - Tìm request đầu tiên > Headers > Copy giá trị `cookie`

⚠️ **Lưu ý**: Không chia sẻ COOKIE với ai khác!

## 📋 Yêu cầu hệ thống

- **GitHub Actions**: Không cần gì thêm
- **Local**: Windows 10/11, Python 3.10+
- **Server**: Hiện tại chỉ hỗ trợ server Asia

## 📊 Xem log

[Gist](https://gist.github.com/tranduytoan/b5179b470dcb5b3d5d573ecc0f164a61)

## ⚖️ Lưu ý

- Chỉ sử dụng cho mục đích cá nhân
- Tuân thủ Terms of Service của HoYoverse
- Không spam requests để tránh bị ban