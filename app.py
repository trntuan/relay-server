import firebase_admin
from firebase_admin import messaging
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from my_secrets import API_SECRET, FIREBASE_CONFIG, VAPID_PUBLIC_KEY

app = Flask(__name__)
firebase_app = firebase_admin.initialize_app()

basic_auth = HTTPBasicAuth()

API_KEY = 'pfZOoRCW-kHtAHQcqiDvb_sy5o8Hj14J_ahUBQgPfOI'

USER_DEVICE_MAP = {'raven_erp.srushty.com':{}, 'hrms_erp.srushty.com':{}}

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
	if user_id in USER_DEVICE_MAP.get(key):
		registration_tokens = USER_DEVICE_MAP.get(key).get(user_id)
		response = messaging.subscribe_to_topic(registration_tokens, topic_name)
		print(response.success_count, 'tokens were subscribed successfully')
		response = {
			'success':'OK',
			'message':'User subscribed'
		}
		return response
	return "User token not registered", 400

@app.post("/api/method/notification_relay.api.topic.unsubscribe")
@basic_auth.login_required
def unsubscribe_to_topic():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	topic_name = request.args.get('topic_name')
	if user_id in USER_DEVICE_MAP.get(key):
		registration_tokens = USER_DEVICE_MAP.get(key).get(user_id)
		response = messaging.unsubscribe_from_topic(registration_tokens, topic_name)
		print(response.success_count, 'tokens were unsubscribed successfully')
		response = {
			'success':'OK',
			'message':'User unsubscribed'
		}
		return response
	return "User token not registered", 400

@app.post("/api/method/notification_relay.api.token.add")
@basic_auth.login_required
def add_token():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	fcm_token = request.args.get('fcm_token')
	if user_id in USER_DEVICE_MAP.get(key):
		USER_DEVICE_MAP[key][user_id].append(fcm_token)
	else:
		USER_DEVICE_MAP[key][user_id] = [fcm_token]
	response = {
		'success':'OK',
		'message':'User Token added'
	}
	return response

@app.post("/api/method/notification_relay.api.token.remove")
@basic_auth.login_required
def remove_token():
	project_name = request.args.get('project_name')
	site_name = request.args.get('site_name')
	key = f'{project_name}_{site_name}'
	user_id = request.args.get('user_id')
	fcm_token = request.args.get('fcm_token')
	if user_id in USER_DEVICE_MAP.get(key):
		USER_DEVICE_MAP[key][user_id].remove(fcm_token)
	response = {
		'success':'OK',
		'message':'User Token removed'
	}
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
	data = request.args.get('data')
	registration_tokens = []
	if user_id in USER_DEVICE_MAP.get(key):
		registration_tokens = USER_DEVICE_MAP.get(key).get(user_id)
		message = messaging.MulticastMessage(
			title=title,
			body=body,
			data=data,
			tokens=registration_tokens
		)
		response = messaging.send(message)
		print('Successfully sent message:', response)
		response = {
			'success':'OK',
			'message':f'Notiifcation sent to {user_id} user'
		}
		return response
	return 'User registration not found', 400

@app.post("/api/method/notification_relay.api.send_notification.topic")
@basic_auth.login_required
def send_notification_to_topic():
	topic = request.args.get('topic_name')
	title = request.args.get('title')
	body = request.args.get('body')
	data = request.args.get('data')
	message = messaging.Message(
		title=title,
		body=body,
    	data=data,
    	topic=topic,
	)
	response = messaging.send(message)
	print('Successfully sent message:', response)
	response = {
		'success':'OK',
		'message':f'Notiifcation sent to {topic} topic'
	}
	return response