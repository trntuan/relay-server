
* Thiết lập dự án
* Cấu hình Firebase
* Cách chạy (Flask/Gunicorn)
* Cách test API bằng Postman
* Gửi notification với dữ liệu JSON đúng định dạng

---

## 📦 Push Notification Relay Server for Frappe Apps

This project enables web push notifications for Frappe Apps such as Raven or HRMS using Firebase and VAPID.

---

## 🚀 Getting Started

### 1. Clone & setup environment

```bash
git clone <repo-url>
cd relay-server
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

---

### 2. Firebase Setup

1. **Create Firebase Project**
   [https://console.firebase.google.com](https://console.firebase.google.com)

2. **Generate Service Account JSON**
   Go to **Project Settings → Service Accounts → Generate New Private Key**

3. **Export credential path**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

---

### 3. Add secrets to `my_secrets.py`

```python
API_SECRET = 'your_custom_secret'
VAPID_PUBLIC_KEY = 'your_vapid_key'
FIREBASE_CONFIG = {
  "apiKey": "...",
  "authDomain": "...",
  ...
}
BADGE_ICON = "/icon-192x192.png"
```

---

### 4. Create user-device map file

```json
// user-device-map.json
{
  "raven_yoursite.com": {},
  "hrms_yoursite.com": {}
}
```

> Replace with `{project_name}_{site_name}` used in Frappe Bench.

---

## 🧪 Testing the Server

### Run Flask (for development)

Make sure at the end of `app.py`:

```python
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8899, debug=True)
```

Run:

```bash
python app.py
```

Test:

```bash
curl http://127.0.0.1:8899/api/method/notification_relay.api.get_config
```

---

## 🐘 Run with Gunicorn (for production)

### `gunicorn.conf.py`

```python
bind = '127.0.0.1:8899'
workers = 2
timeout = 120
```

Start:

```bash
gunicorn app:app -c gunicorn.conf.py
```

---

## 🔒 Secure with API\_KEY & API\_SECRET

Use HTTP Basic Auth for all API requests. Example using `curl`:

```bash
curl -u "API_KEY:API_SECRET" http://127.0.0.1:8899/api/...
```

---

## 🧪 Testing with Postman

### 1. **Authorization**

* Type: **Basic Auth**
* Username: `API_KEY`
* Password: `API_SECRET`

---

### 2. **Add token API**

* Method: `POST`
* URL:

  ```
  http://127.0.0.1:8899/api/method/notification_relay.api.token.add?project_name=raven&site_name=erpsgs.in&user_id=john@example.com&fcm_token=abc123
  ```

---

### 3. **Send notification (Recommended)**

* Method: `POST`

* URL:

  ```
  http://127.0.0.1:8899/api/method/notification_relay.api.send_notification.user?project_name=raven&site_name=erpsgs.in&user_id=john@example.com&title=Hello&body=World
  ```

* Body → `raw` → `JSON`:

```json
{
  "click_action": "https://example.com",
  "notification_icon": "/icon.png"
}
```

> **Important:** Server must parse `request.get_json()` in `app.py`.

---

## 🛠 Fix CORS for localhost

```bash
pip install flask-cors
```

In `app.py`:

```python
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})
```

---

## 🔁 Run as a systemd service

Create `/etc/systemd/system/push-relay.service`:

```ini
[Unit]
Description=Frappe Push Relay
After=network.target

[Service]
User=frappe
Group=www-data
WorkingDirectory=/home/frappe/relay-server
Environment="PATH=/home/frappe/relay-server/env/bin"
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/frappe/relay-server/firebase.json"
ExecStart=/home/frappe/relay-server/env/bin/gunicorn app:app -c /home/frappe/relay-server/gunicorn.conf.py

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable push-relay
sudo systemctl start push-relay
```

---

## ✅ Final Steps in ERPNext

* Go to **Push Notification Settings**
* Add `API_KEY`, `API_SECRET`
* Enable "Use Push Relay Server"
