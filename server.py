# server.py - Phiên bản cuối cùng, ổn định và có chú thích
import asyncio
import websockets
import json
import logging

# Cài đặt logging để xem thông báo rõ ràng hơn
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===================================================================
# 1. QUẢN LÝ CLIENT
# Sử dụng Dictionary để lưu trữ {websocket_object: "username"}
# Giúp chúng ta biết kết nối nào thuộc về người dùng nào
# ===================================================================
connected_clients = {}


async def broadcast(message):
    """Gửi một tin nhắn đến TẤT CẢ các client đang kết nối."""
    if connected_clients:
        # Gửi đồng thời tới tất cả client để tăng hiệu suất
        await asyncio.wait([client.send(message) for client in connected_clients])

async def send_user_list():
    """Cập nhật danh sách người dùng online và gửi cho mọi người."""
    user_list = list(connected_clients.values())
    logging.info(f"Cập nhật danh sách người dùng: {user_list}")
    user_list_message = json.dumps({"type": "user_list", "users": user_list})
    await broadcast(user_list_message)


# ===================================================================
# 2. XỬ LÝ LOGIC CHAT
# Đây là hàm chính xử lý mọi việc khi có một client kết nối
# ===================================================================
async def chat_handler(websocket):
    """
    Hàm này được chạy riêng cho mỗi client kết nối vào server.
    """
    username = None
    try:
        # Bước A: Đăng nhập
        # Tin nhắn ĐẦU TIÊN client gửi phải là tin nhắn đăng nhập.
        login_message = await websocket.recv()
        data = json.loads(login_message)

        if data.get("type") == "login":
            username = data.get("username")
            # Kiểm tra nếu tên người dùng hợp lệ
            if not username or username in connected_clients.values():
                # Nếu tên rỗng hoặc đã tồn tại, từ chối kết nối
                await websocket.send(json.dumps({"type": "error", "message": "Tên đã tồn tại hoặc không hợp lệ."}))
                await websocket.close()
                logging.warning(f"Đăng nhập thất bại: Tên '{username}' không hợp lệ hoặc đã tồn tại.")
                return

            # Thêm client vào danh sách quản lý
            connected_clients[websocket] = username
            logging.info(f"✅ Người dùng '{username}' đã kết nối. Tổng số: {len(connected_clients)}")

            # Gửi thông báo cho mọi người và cập nhật danh sách online
            announcement = json.dumps({"type": "announcement", "message": f"👋 '{username}' đã tham gia phòng chat."})
            await broadcast(announcement)
            await send_user_list()
        else:
            logging.warning("Kết nối bị từ chối: Tin nhắn đầu tiên không phải là 'login'.")
            return

        # Bước B: Lắng nghe tin nhắn chat
        # Vòng lặp để nhận các tin nhắn tiếp theo sau khi đã đăng nhập thành công
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "chat_message":
                chat_payload = json.dumps({
                    "type": "chat_message",
                    "sender": username, # Lấy tên từ biến đã lưu
                    "message": data.get("message")
                })
                await broadcast(chat_payload)

    except websockets.exceptions.ConnectionClosedError:
        logging.info(f"Kết nối với '{username}' bị đóng đột ngột.")
    except Exception as e:
        logging.error(f"Đã xảy ra lỗi với người dùng '{username}': {e}")
    finally:
        # Bước C: Dọn dẹp khi client ngắt kết nối
        if websocket in connected_clients:
            # Xóa client khỏi danh sách
            del connected_clients[websocket]
            if username:
                logging.info(f"❌ Người dùng '{username}' đã ngắt kết nối. Còn lại: {len(connected_clients)}")
                # Thông báo cho mọi người và cập nhật lại danh sách online
                announcement = json.dumps({"type": "announcement", "message": f"👋 '{username}' đã rời phòng chat."})
                await broadcast(announcement)
                await send_user_list()


# ===================================================================
# 3. KHỞI ĐỘNG SERVER
# Phần này để chạy server trên một địa chỉ và cổng xác định
# ===================================================================
async def main():
    # Sử dụng 'async with' để đảm bảo server được quản lý tốt
    async with websockets.serve(chat_handler, "localhost", 8765):
        logging.info("🚀 Server WebSocket đã sẵn sàng và đang chạy trên ws://localhost:8765")
        await asyncio.Future()  # Giữ cho server chạy mãi mãi

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server đã được tắt.")