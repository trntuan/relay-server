import os
import logging
from dotenv import load_dotenv
import firebase_admin
import json
from firebase_admin import exceptions, messaging
from urllib.parse import urlparse, urlunparse
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS 
from my_secrets import API_SECRET, FIREBASE_CONFIG, VAPID_PUBLIC_KEY, BADGE_ICON

# Load env
load_dotenv()

app = Flask(__name__)

# get the allowed origin from environment variable
allowed_origin = os.getenv("ALLOWED_ORIGIN", "*")  # fallback is "*" if not set

CORS(app, resources={r"/*": {"origins": allowed_origin}})

firebase_app = firebase_admin.initialize_app()

basic_auth = HTTPBasicAuth()

API_KEY = 'pfZOoRCW-kHtAHQcqiDvb_sy5o8Hj14J_ahUBQgPfOI'

USER_DEVICE_MAP = {'raven_erpsgs.in':{}, 'hrms_erpsgs.in':{}}

TOPICS = []

with open('user-device-map.json', 'r') as jsonfile:
		USER_DEVICE_MAP = json.load(jsonfile)

def save_map_to_file(map):
	with open('user-device-map.json', 'w') as jsonfile:
		json.dump(map, jsonfile)
	print(json.dumps(map, indent=4))

@app.get('/api/method/notification_relay.api.get_config')
def get_config():
	response = {}
	response['vapid_public_key'] = VAPID_PUBLIC_KEY
	response['config'] = FIREBASE_CONFIG
	return response

@basic_auth.verify_password
def verify_api_key(api_key, api_secret):
	if api_key==API_KEY and api_secret==API_SECRET:
		return True
	return False

@app.post("/api/method/notification_relay.api.topic.subscribe")
@basic_auth.login_required
def subscribe_to_topic():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	topic_name = request.args.get('topic_name')
	app.logger.debug(f'Topic Subscribe Request - {request.args}')
	if user_id in USER_DEVICE_MAP.get(key):
		registration_tokens = USER_DEVICE_MAP.get(key).get(user_id)
		if registration_tokens:
			response = messaging.subscribe_to_topic(registration_tokens, topic_name)
			app.logger.info(f'{response.success_count} tokens were subscribed successfully')
			response = {
			'message':{
				'success':200,
				'message':'User subscribed'
				}
			}
			return response
		else:
			app.logger.info(f'No tokens found for user {user_id} to subscribe')
	app.logger.info(f'{user_id} not subscribed for push notifications')
	response = {
		'exc':{
			'status_code':404,
			'message':f'{user_id} not subscribed to push notifications'
			}
	}
	return response, 400

@app.post("/api/method/raven_cloud.api.notification.register_site")
@basic_auth.login_required
def register_site():
    site_name = request.args.get('site_name')
    app.logger.info(f"Registering site: {site_name}")

    # return the VAPID public key and Firebase config
    return jsonify({
        "message": {
            "vapid_public_key": VAPID_PUBLIC_KEY,
            "config": FIREBASE_CONFIG
        }
    })


@app.post("/api/method/notification_relay.api.topic.unsubscribe")
@basic_auth.login_required
def unsubscribe_to_topic():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	topic_name = request.args.get('topic_name')
	app.logger.debug(f'Topic Unsubscribe Request - {request.args}')
	if user_id in USER_DEVICE_MAP.get(key):
		registration_tokens = USER_DEVICE_MAP.get(key).get(user_id)
		if registration_tokens:
			response = messaging.unsubscribe_from_topic(registration_tokens, topic_name)
			app.logger.info(f'{response.success_count} tokens were unsubscribed successfully')
			response = {
			'message':{
				'success':200,
				'message':f'User {user_id} unsubscribed from {topic_name} topic'
				}
			}
			return response
	response = {
		'exc':{
			'status_code':404,
			'message':f'{user_id} not subscribed to push notifications'
			}
	}
	return response, 400

@app.post("/api/method/notification_relay.api.token.add")
def add_token():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	fcm_token = request.args.get('fcm_token')
	app.logger.debug(f'Add Token Request - {request.args}')
	if user_id in USER_DEVICE_MAP.get(key):
		if fcm_token in USER_DEVICE_MAP[key][user_id]:
			response = {
				'message':{
					'success':200,
					'message':'User Token duplicate found'
					}
			}
			app.logger.info(f'Duplicate token found for user {user_id}')
			return response
		else:
			USER_DEVICE_MAP[key][user_id].append(fcm_token)
			app.logger.info(f'Token added for user {user_id}')
	else:
		USER_DEVICE_MAP[key][user_id] = [fcm_token]
		app.logger.info(f'User entry created & Token added for user {user_id}')
	save_map_to_file(USER_DEVICE_MAP)
	response = {
		'message':{
			'success':200,
			'message':'User Token added'
			}
	}
	return response

# [Raven v2.6.2] Replaces legacy endpoint `/api/method/notification_relay.api.token.add`
# New API to create user token
@app.post("/api/method/raven_cloud.api.notification.create_user_token")
def create_user_token():
	site_name = request.args.get('site_name')
	user_id = request.args.get('user_id')
	fcm_token = request.args.get('token')

	# Check if all required parameters are provided
	if not all([site_name, user_id, fcm_token]):
		app.logger.warning(f"Missing parameters: site_name={site_name}, user_id={user_id}, fcm_token={fcm_token}")
		return {
			'message': {
				'success': 400,
				'message': 'Missing required parameters'
			}
		}, 400

	key = site_name
	app.logger.debug(f'Add Token Request - {request.args}')

	# Init nested map if needed
	if key not in USER_DEVICE_MAP:
		USER_DEVICE_MAP[key] = {}

	if user_id in USER_DEVICE_MAP[key]:
		if fcm_token in USER_DEVICE_MAP[key][user_id]:
			app.logger.info(f'Duplicate token found for user {user_id}')
			return {
				'message': {
					'success': 200,
					'message': 'User Token duplicate found'
				}
			}
		else:
			USER_DEVICE_MAP[key][user_id].append(fcm_token)
	else:
		USER_DEVICE_MAP[key][user_id] = [fcm_token]

	app.logger.info(f'Token saved for user {user_id} at {key}')
	save_map_to_file(USER_DEVICE_MAP)

	return {
		'message': {
			'success': 200,
			'message': 'User Token added'
		}
	}


@app.post("/api/method/notification_relay.api.token.remove")
@basic_auth.login_required
def remove_token():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	fcm_token = request.args.get('fcm_token')
	response = {
		'message':{
			'success':200,
			'message':'User Token removed'
			}
	}
	app.logger.debug(f'Remove Token Request - {request.args}')
	if user_id in USER_DEVICE_MAP.get(key) and USER_DEVICE_MAP.get(key).get(user_id):
		try:
			USER_DEVICE_MAP[key][user_id].remove(fcm_token)
			save_map_to_file(USER_DEVICE_MAP)
		except ValueError:
			app.logger.info(f'FCM Token not found for user {user_id}')
	return response

@app.post("/api/method/notification_relay.api.send_notification.user")
@basic_auth.login_required
def send_notification_to_user():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	title = request.args.get('title')
	body = request.args.get('body')
	data = json.loads(request.args.get('data'))
	notification_icon = data.get('notification_icon')
	if not notification_icon:
		notification_icon = ''
	app.logger.debug(f'User Notification Request - {request.args}')
	registration_tokens = []
	if user_id in USER_DEVICE_MAP.get(key) and USER_DEVICE_MAP.get(key).get(user_id):
		registration_tokens = USER_DEVICE_MAP.get(key).get(user_id)
		message = messaging.MulticastMessage(
			webpush=messaging.WebpushConfig(
				notification=messaging.WebpushNotification(
					title=title,
					body=body,
					icon= notification_icon,
					badge= BADGE_ICON
				),
				fcm_options=messaging.WebpushFCMOptions(link=data.get('click_action')),
			),
			tokens=registration_tokens
		)
		try:
			response = messaging.send_each_for_multicast(message)
			if response.failure_count > 0:
				responses = response.responses
				failed_tokens = []
				for idx, resp in enumerate(responses):
					if not resp.success:
						# The order of responses corresponds to the order of the registration tokens.
						failed_tokens.append(registration_tokens[idx])
						if isinstance(resp.exception, exceptions.NotFoundError):
							USER_DEVICE_MAP.get(key).get(user_id).remove(registration_tokens[idx])
							save_map_to_file(USER_DEVICE_MAP)
						else:
							app.logger.debug(f'Exception : {resp.exception}, {resp.exception.code}, {resp.exception.cause}, {resp.exception.http_response}')
			app.logger.info(f'Successfully sent message: {response.success_count}, {[resp.message_id for resp in response.responses]}')
		except exceptions.FirebaseError:
			pass
		response = {
			'message':{
				'success':200,
				'message':f'{response.success_count} Notiifcation sent to {user_id} user'
				}
		}
	else:
		response = {
			'exc':{
				'status_code':404,
				'message':f'{user_id} not subscribed to push notifications'
				}
		}
		app.logger.info(f'User {user_id} has not enabled notifications')
		return response, 400
	return response


@app.post("/api/method/raven_cloud.api.notification.send")
def send_notification():
    messages_param = request.args.get('messages')

    try:
        messages = json.loads(messages_param)
    # If the 'messages' parameter is not a valid JSON, return an error
    except json.JSONDecodeError:
        return {"error": "Invalid 'messages' format"}, 400

    success_count = 0
    for msg in messages:
        tokens = msg.get('tokens', [])
        title = msg.get('notification', {}).get('title', '')
        body = msg.get('notification', {}).get('body', '')
        data = msg.get('data', {})
        click_action = msg.get('click_action')
        image = msg.get('image', None)

        webpush_config = messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=title,
                body=body,
                icon=data.get('notification_icon', ''),
                image=image,
                badge=BADGE_ICON
            )
        )

        # Only add fcm_options if link is HTTPS
        if click_action and click_action.startswith("https://"):
            webpush_config.fcm_options = messaging.WebpushFCMOptions(link=click_action)

        message = messaging.MulticastMessage(
            webpush=webpush_config,
            tokens=tokens
        )

        try:
            response = messaging.send_each_for_multicast(message)
            success_count += response.success_count
        except exceptions.FirebaseError as e:
            app.logger.error(f"Firebase error: {str(e)}")
            continue

    return {
        "message": {
            "success": 200,
            "message": f"{success_count} notifications sent via 'messages' payload"
        }
    }

# [Raven v2.6.2] Replaces legacy endpoint `/api/method/notification_relay.api.send_notification.user`
@app.post("/api/method/raven_cloud.api.notification.send_to_users")
def send_notification_to_users():
    messages_param = request.args.get("messages")
    site_name = request.args.get("site_name")
#     app.logger.info(f"[Input] Raw messages_param: {messages_param}")
#     app.logger.info(f"[Input] site_name: {site_name}")
    if not messages_param or not site_name:
        return jsonify({"error": "Missing 'messages' or 'site_name' parameter"}), 400

    try:
        messages = json.loads(messages_param)
        # app.logger.info(f"[Parse] Parsed messages: {json.dumps(messages, indent=2)}")
        assert isinstance(messages, list), "'messages' must be a list"
    except (json.JSONDecodeError, AssertionError) as e:
        return jsonify({"error": f"Invalid 'messages' format: {str(e)}"}), 400

    def sanitize_click_action(url: str) -> str:
        try:
            parsed = urlparse(url)
            scheme = 'https' if parsed.scheme == 'http' else parsed.scheme
            hostname_only = parsed.hostname or ""
            new_netloc = hostname_only
            return urlunparse(parsed._replace(scheme=scheme, netloc=new_netloc))
        except Exception:
            return url

    success_count = 0
    failures = []

    for i, msg in enumerate(messages):
        try:
            user_ids = msg.get('users', [])
            if not user_ids:
                raise ValueError("Missing 'users' field or it's empty.")

            notification = msg.get('notification', {})
            title = notification.get('title', '')
            body = notification.get('body', '')

            data = msg.get('data', {})
            image = msg.get('image', None)
            tag = msg.get('tag', '')

            #  Add title & body to data for Raven display
            data["title"] = title
            data["body"] = body
            if tag:
                data["tag"] = tag
            if image:
                data["image"] = image

            #  Clean click_action in data
            original_click_action = msg.get('click_action') or data.get('click_action')
            if isinstance(original_click_action, str) and original_click_action:
                cleaned_click_action = sanitize_click_action(original_click_action)
                parsed = urlparse(cleaned_click_action)
                cleaned_base = f"{parsed.scheme}://{parsed.hostname}"
                data["base_url"] = cleaned_base
                data["message_url"] = cleaned_click_action


            registration_tokens = []
            for user_id in user_ids:
                tokens = USER_DEVICE_MAP.get(site_name, {}).get(user_id, [])
                if tokens:
                    registration_tokens.extend(tokens)

            if not registration_tokens:
                raise ValueError("No valid tokens found for specified users.")

            #  Send data-only push (no notification object)
            message = messaging.MulticastMessage(
                tokens=registration_tokens,
                data={k: str(v) for k, v in data.items() if isinstance(v, (str, int, float, str))}
            )

            response = messaging.send_each_for_multicast(message)
            success_count += response.success_count

            #  Handle failed tokens as before
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_token = registration_tokens[idx]
                        for user_id in user_ids:
                            if failed_token in USER_DEVICE_MAP.get(site_name, {}).get(user_id, []):
                                if isinstance(resp.exception, exceptions.NotFoundError):
                                    USER_DEVICE_MAP[site_name][user_id].remove(failed_token)
                                    save_map_to_file(USER_DEVICE_MAP)
                        app.logger.warning(f"Failed token: {failed_token}, reason: {str(resp.exception)}")

        except Exception as e:
            app.logger.error(f"[Notification Error] index {i}: {str(e)}")
            failures.append({"index": i, "error": str(e), "users": msg.get("users", [])})

    return jsonify({
        "message": f"{success_count} notifications sent successfully.",
        "success_count": success_count,
        "failures": failures,
    }), 200


@app.post("/api/method/notification_relay.api.send_notification.topic")
@basic_auth.login_required
def send_notification_to_topic():
	topic = request.args.get('topic_name')
	title = request.args.get('title')
	body = request.args.get('body')
	data = json.loads(request.args.get('data'))
	notification_icon = data.get('notification_icon')
	if not notification_icon:
		notification_icon = ''
	app.logger.debug(f'Topic Notification Request - {request.args}')
	message = messaging.Message(
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=title,
                body=body,
                icon=notification_icon,
				badge= BADGE_ICON
            ),
			fcm_options=messaging.WebpushFCMOptions(link=data.get('click_action')),
        ),
        topic=topic,
    )
	response = messaging.send(message)
	app.logger.info(f'Successfully sent message: {response}')
	response = {
		'message':{
			'success':200,
			'message':f'Notiifcation sent to {topic} topic'
			}
	}
	return response

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
