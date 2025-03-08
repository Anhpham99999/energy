import json
import time
import hashlib
import hmac
import requests
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# **Thông tin API Tuya**
BASE_URL = "https://openapi.tuyaus.com"
CLIENT_ID = "5gqk7ucmasgscpfz03dt"
SECRET = "ddfe60390b5046cb9c1c736fdfb154e8"

# **Lưu token**
tuya_token = None
tuya_refresh_token = None
token_expire_time = 0


# **Hàm tạo sign**
def create_sign(method, url, body=""):
    global CLIENT_ID, SECRET

    timestamp = str(int(time.time() * 1000))  # Tạo timestamp
    hash_body = hashlib.sha256(body.encode("utf-8")).hexdigest()  # Hash body
    str_to_sign = f"{method}#{hash_body}##{url}"  # Chuỗi cần mã hóa
    sign_str = CLIENT_ID + timestamp + str_to_sign  # Ghép chuỗi
    sign = hmac.new(SECRET.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256).hexdigest()  # Mã hóa HMAC-SHA256

    return sign, timestamp


# **Hàm lấy token**
def get_token():
    global tuya_token, tuya_refresh_token, token_expire_time

    url = "/v1.0/token?grant_type=1"
    sign, timestamp = create_sign("GET", url)
    headers = {
        "client_id": CLIENT_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256"
    }

    response = requests.get(BASE_URL + url, headers=headers)
    data = response.json()
    
    if data["success"]:
        tuya_token = data["result"]["access_token"]
        tuya_refresh_token = data["result"]["refresh_token"]
        token_expire_time = time.time() + data["result"]["expire_time"]
        print("✅ Lấy token thành công:", tuya_token)
    else:
        print("❌ Lỗi lấy token:", data)


# **Hàm refresh token**
def refresh_token():
    global tuya_token, tuya_refresh_token, token_expire_time

    url = f"/v1.0/token/{tuya_refresh_token}"
    sign, timestamp = create_sign("GET", url)
    headers = {
        "client_id": CLIENT_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256"
    }

    response = requests.get(BASE_URL + url, headers=headers)
    data = response.json()

    if data["success"]:
        tuya_token = data["result"]["access_token"]
        tuya_refresh_token = data["result"]["refresh_token"]
        token_expire_time = time.time() + data["result"]["expire_time"]
        print("✅ Refresh token thành công:", tuya_token)
    else:
        print("❌ Lỗi refresh token:", data)


# **Hàm lấy lịch sử log của thiết bị**
def get_device_logs(device_id, start_time, end_time):
    global tuya_token

    # Kiểm tra token
    if time.time() >= token_expire_time:
        refresh_token()

    url = f"/v1.0/devices/{device_id}/logs?start_time={start_time}&end_time={end_time}&type=1,2,3,4,5,6,7,8,9"
    sign, timestamp = create_sign("GET", url)
    
    headers = {
        "client_id": CLIENT_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
        "access_token": tuya_token
    }

    response = requests.get(BASE_URL + url, headers=headers)
    data = response.json()

    if data["success"]:
        return data["result"]
    else:
        print("❌ Lỗi lấy lịch sử log:", data)
        return []


# **API để lấy lịch sử log của thiết bị**
@app.route("/api/device_logs/<device_id>")
def api_device_logs(device_id):
    end_time = int(time.time() * 1000)  # Thời gian hiện tại
    start_time = end_time - (24 * 60 * 60 * 1000)  # 24 giờ trước

    logs = get_device_logs(device_id, start_time, end_time)
    return jsonify({"device_id": device_id, "logs": logs})


# **Trang web hiển thị lịch sử log**
@app.route("/")
def index():
    return render_template("device_logs.html")


if __name__ == "__main__":
    get_token()  # Lấy token lúc khởi động
    app.run(debug=True, host="0.0.0.0")
