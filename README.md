# Push Notification Relay Server for Frappe Apps
This repo was created to enable push notifications for Frappe Apps such as Raven.

## Getting Started
To be able to run this application, you will need to do the following:

- Create a Firebase Project & get Service Account credentials [Link](https://sharma-vikashkr.medium.com/firebase-how-to-setup-a-firebase-service-account-836a70bb6646)
- Run this command on the shell
  ``` bash
  export GOOGLE_APPLICATION_CREDENTIALS="/home/frappe/relay-server/{service-account-file_name}.json"

  ```
- Follow **Register you app** under Step 1 given in the [Firebase documentation](https://firebase.google.com/docs/web/setup#register-app) and obtain the `FIREBASE_CONFIG` JSON object. Save it to `my_secrets.py`.
- Follow this StackOverflow [Link](https://stackoverflow.com/a/54996207) to generate a VAPID key. Save it to `my_secrets.py`
- Generate `API_KEY` & `API_SECRET` and add them to ERPNext Settings. Enable Push notifications in ERPNext settings.
- Add the `API_SECRET` value to the `my_secrets.py`.
- Finally, your `my_secrets.py` should like this
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
