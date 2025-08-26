// server.js - Phiên bản để Deploy
const express = require('express');
const http = require('http');
const path = require('path');
const { WebSocketServer } = require('ws'); // Thay đổi cách import một chút

// --- Phần cài đặt Server ---
const app = express();
const server = http.createServer(app);

// Lấy PORT từ biến môi trường của Render, hoặc dùng 8080 nếu chạy local
const PORT = process.env.PORT || 8080;

// Yêu cầu Express phục vụ các tệp tĩnh từ thư mục hiện tại
app.use(express.static(path.join(__dirname)));

// Route để phục vụ tệp index.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Khởi tạo WebSocket Server gắn với HTTP server
const wss = new WebSocketServer({ server });

console.log(`🚀 Server đang chuẩn bị khởi động trên cổng ${PORT}...`);

// --- Phần Logic WebSocket (Giữ nguyên) ---
const connected_clients = new Map(); // Dùng Map an toàn hơn

function sendUserList() {
    const userList = Array.from(connected_clients.values());
    const message = JSON.stringify({ type: "user_list", users: userList });
    for (const client of connected_clients.keys()) {
        client.send(message);
    }
}

function broadcast(message) {
    for (const client of connected_clients.keys()) {
        client.send(message);
    }
}

wss.on('connection', (ws) => {
    // Logic xử lý kết nối, tin nhắn, ngắt kết nối giữ nguyên như phiên bản trước...
    // Ở đây mình rút gọn lại, bạn chỉ cần copy-paste logic cũ vào là được
    console.log('Một client mới đã kết nối!');

    ws.on('message', (messageAsString) => {
        const message = JSON.parse(messageAsString);

        if (message.type === 'login') {
            const username = message.username;
            connected_clients.set(ws, username);
            console.log(`✅ ${username} đã tham gia.`);
            broadcast(JSON.stringify({ type: "announcement", message: `👋 ${username} đã tham gia phòng chat.` }));
            sendUserList();
        } else if (message.type === 'chat_message') {
            const sender = connected_clients.get(ws);
            broadcast(JSON.stringify({ type: "chat_message", sender: sender, message: message.message }));
        }
    });

    ws.on('close', () => {
        const username = connected_clients.get(ws);
        if (username) {
            connected_clients.delete(ws);
            console.log(`❌ ${username} đã rời đi.`);
            broadcast(JSON.stringify({ type: "announcement", message: `👋 ${username} đã rời phòng chat.` }));
            sendUserList();
        }
    });
});

// Khởi động server
server.listen(PORT, () => {
    console.log(`✅ Server đã chạy và lắng nghe trên http://localhost:${PORT}`);
});
