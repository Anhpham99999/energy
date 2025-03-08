import ssl
import socket

# Địa chỉ MQTT broker của Rạng Đông
hostname = "mqtt.rangdong.com.vn"
port = 8883

# Tạo context SSL
context = ssl.create_default_context()

try:
    # Kết nối đến broker và lấy thông tin chứng chỉ
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            print("✅ Kết nối thành công!")
            print("🔍 Chứng chỉ của MQTT broker:")
            print(cert)
except Exception as e:
    print(f"❌ Lỗi khi kết nối: {e}")
