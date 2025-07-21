# Push Notification Relay Server for Frappe Apps
This repo was created to enable push notifications for Frappe Apps such as Raven.

## Getting Started
To be able to run this application, you will need to do the following:

1. Clone this project and create a virtual environment `python -m venv env`
2. Install all requirements `pip install -r requirements.txt`
4. Create a Firebase Project & get Service Account credentials [Link](https://sharma-vikashkr.medium.com/firebase-how-to-setup-a-firebase-service-account-836a70bb6646)
5. Run this command on the shell
  ``` bash
  export GOOGLE_APPLICATION_CREDENTIALS="/home/frappe/relay-server/{service-account-file_name}.json"

  ```
6. Follow **Register you app** under Step 1 given in the [Firebase documentation](https://firebase.google.com/docs/web/setup#register-app) and obtain the `FIREBASE_CONFIG` JSON object. Save it to `my_secrets.py`.
7.  Follow this StackOverflow [Link](https://stackoverflow.com/a/54996207) to generate a VAPID key. Save it to `my_secrets.py`
8.  Generate `API_KEY` & `API_SECRET` and add the `API_SECRET` value to the `my_secrets.py`.
9.  Finally, your `my_secrets.py` should like this
``` python
API_SECRET = 'tIUAGguQH-xajbkcjsd-lsd'
VAPID_PUBLIC_KEY = "Bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
FIREBASE_CONFIG = {
  "apiKey": "AIzaSyC3UVxbCkUv3l4PpyWkQZGEuwOds76sdUgk0",
  "authDomain": "xxxxxxxx-frappe.firebaseapp.com",
  "projectId": "xxxxxxxxx-frappe",
  "storageBucket": "xxxxxxxxx-frappe.appspot.com",
  "messagingSenderId": "815115xxx703",
  "appId": "1:815115xxx703:web:e89fcdadfcf8df09e4852",
  "measurementId": "G-XXXXXXXXXG"
}
```
10. Change the `USER_DEVICE_MAP` key values to `{project_name}_{site_name}` where `project_name` could be `raven` or `hrms` & `site_name` as your site name while setting up the Frappe bench.
11. Run the application
12. Add the `API_SECRET` & `API_KEY` in ERPNext Push Notification settings and then enable the Push Notification Relay option.

## Running the Application
``` bash
gunicorn app:app -c gunicorn.conf.py
```
## Run a Systemd Service
- Create a Systemd service file at `/etc/systemd/system/push-relay.service` and copy the following and replace the paths/filenames accordingly :
``` bash
# /etc/systemd/system/push-relay.service
[Unit]
Description=Gunicorn instance to server Frappe Push Notification Relay Server
After=network.target

[Service]
User=frappe
Group=www-data
WorkingDirectory=/home/frappe/relay-server
Environment="PATH=/home/frappe/relay-server/env/bin"
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/frappe/relay-server/{service-account-file_name}.json"
ExecStart=/home/frappe/relay-server/env/bin/gunicorn app:app -c /home/frappe/relay-server/gunicorn.conf.py

[Install]
WantedBy=multi-user.target
```
- Run the following commands
  ``` bash
  sudo systemctl daemon-reload
  sudo systemctl enable push-relay
  sudo systemctl start push-relay
  ```




## Fix CORS issue [ localhost ] :
- In case you are running Frappe instance on localhost, then perform the following steps to avoid CORS issues

  - Run the following commands
    ``` bash
     pip install flask-cors
    ```

     
  - app.py                                          [add line 8 & 10]
    ``` bash
      7    from my_secrets import API_SECRET, FIREBASE_CONFIG, VAPID_PUBLIC_KEY, BADGE_ICON
    + 8    from flask_cors import CORS
    
      9    app = Flask(__name__)
    + 10   CORS(app, resources={r"/*": {"origins": "*"}})  # This will allow all origins
    
      11   firebase_app = firebase_admin.initialize_app()
      12   basic_auth = HTTPBasicAuth()
    ```
  
  - firebase_admin/_messaging_encoder.py            [ comment line : 507, 508 ]
      ``` bash
        506    link = result.get('link')
     - 507    # if link is not None and not link.startswith('https://'):
     - 508        # raise ValueError('WebpushFCMOptio ns.link must be a HTTPS URL.') 
        509    return result
      ```
  
  - Restart bench and gunicorn server

## 🔐 Secure with API\_KEY & API\_SECRET

All API requests require **HTTP Basic Auth** using your `API_KEY` as the username and `API_SECRET` as the password.

### Example using `curl`:

```bash
curl -u "API_KEY:API_SECRET" http://127.0.0.1:8899/api/...
```

---

## 🧚‍♂️ Testing with Postman

### 1. Authorization

* Type: `Basic Auth`
* Username: `API_KEY`
* Password: `API_SECRET`

---

## 📌 API Endpoints

### 1. Add FCM Token for a User

* **Method:** `POST`

* **Endpoint:** `/api/method/notification_relay.api.token.add`

* **Query Parameters:**

  * `project_name`: project name (e.g., `raven`)
  * `site_name`: site name (e.g., `erpsgs.in`)
  * `user_id`: user email or ID (e.g., `john@example.com`)
  * `fcm_token`: the FCM token from client

* **Example URL:**

```
http://127.0.0.1:8899/api/method/notification_relay.api.token.add?project_name=raven&site_name=erpsgs.in&user_id=john@example.com&fcm_token=abc123
```

---

### 2. Send Notification to a User (Recommended)

* **Method:** `POST`

* **Endpoint:** `/api/method/notification_relay.api.send_notification.user`

* **Query Parameters:**

  * `project_name`, `site_name`, `user_id`, `title`, `body`

* **Request Body (raw JSON):**

```json
{
  "click_action": "https://example.com",
  "notification_icon": "/icon.png"
}
```

* **Example URL:**

```
http://127.0.0.1:8899/api/method/notification_relay.api.send_notification.user?project_name=raven&site_name=erpsgs.in&user_id=john@example.com&title=Hello&body=World
```

---

### 3. Register a Site

* **Method:** `POST`

* **Endpoint:** `/api/method/raven_cloud.api.notification.register_site`

* **Auth:** Requires Basic Auth

* **Query Parameters:**

  * `site_name`: name of the site to register

* **Purpose:** Returns the `vapid_public_key` and Firebase configuration required by the client.

* **Example Response:**

```json
{
  "message": {
    "vapid_public_key": "<public_key>",
    "config": {
      "apiKey": "...",
      "authDomain": "..."
    }
  }
}
```

---

### 4. Send Bulk Notifications

* **Method:** `POST`

* **Endpoint:** `/api/method/raven_cloud.api.notification.send`

* **Query Parameters:**

  * `project_name`: name of the project
  * `site_name`: name of the site
  * `messages`: a JSON-encoded array of notification objects

* **Notification Format:**

```json
[
  {
    "tokens": ["fcm_token_1", "fcm_token_2"],
    "notification": {
      "title": "Hello",
      "body": "World"
    },
    "data": {
      "notification_icon": "/icon.png"
    },
    "click_action": "https://example.com",
    "image": "https://example.com/image.png"
  }
]
```

* **Notes:**

  * `click_action` is only included if it starts with `https://`.
  * You can send to multiple tokens per object.

* **Example Response:**

```json
{
  "message": {
    "success": 200,
    "message": "3 notifications sent via 'messages' payload"
  }
}
```

---

# manual start
```
$ source env/bin/activate
$ export GOOGLE_APPLICATION_CREDENTIALS="/home/dev/workspace/projects/frappe/relay-server/relay-server/my-firebase.json"
$ gunicorn app:app -c gunicorn.conf.py
```