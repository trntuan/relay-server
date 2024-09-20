import logging
import firebase_admin
import json
from firebase_admin import messaging
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from my_secrets import API_SECRET, FIREBASE_CONFIG, VAPID_PUBLIC_KEY

app = Flask(__name__)
firebase_app = firebase_admin.initialize_app()

basic_auth = HTTPBasicAuth()

API_KEY = 'pfZOoRCW-kHtAHQcqiDvb_sy5o8Hj14J_ahUBQgPfOI'

USER_DEVICE_MAP = {'raven_erpsgs.in':{}, 'hrms_erpsgs.in':{}}

TOPICS = []

with open('user-device-map.json', 'r') as jsonfile:
		USER_DEVICE_MAP = json.load(jsonfile)

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
@basic_auth.login_required
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
	with open('user-device-map.json', 'w') as jsonfile:
		json.dump(USER_DEVICE_MAP, jsonfile)
	print(json.dumps(USER_DEVICE_MAP, indent=4))
	response = {
		'message':{
			'success':200,
			'message':'User Token added'
			}
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
	app.logger.debug(f'Remove Token Request - {request.args}')
	if user_id in USER_DEVICE_MAP.get(key):
		try:
			USER_DEVICE_MAP[key][user_id].remove(fcm_token)
		except:
			pass
	with open('user-device-map.json', 'w') as jsonfile:
		json.dump(USER_DEVICE_MAP, jsonfile)
	print(json.dumps(USER_DEVICE_MAP, indent=4))
	response = {
		'message':{
			'success':200,
			'message':'User Token removed'
			}
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
	data = json.loads(request.args.get('data'))
	app.logger.debug(f'User Notification Request - {request.args}')
	registration_tokens = []
	if user_id in USER_DEVICE_MAP.get(key) and USER_DEVICE_MAP.get(key).get(user_id):
		registration_tokens = USER_DEVICE_MAP.get(key).get(user_id)
		message = messaging.MulticastMessage(
			webpush=messaging.WebpushConfig(
				notification=messaging.WebpushNotification(
					title=title,
					body=body,
					icon='https://erpsgs.in/assets/raven/raven_mobile/favicon-64x64.png',
				),
				fcm_options=messaging.WebpushFCMOptions(link=data.get('click_action')),
			),
			tokens=registration_tokens
		)
		response = messaging.send_each_for_multicast(message)
		if response.failure_count > 0:
			responses = response.responses
			failed_tokens = []
			for idx, resp in enumerate(responses):
				if not resp.success:
					# The order of responses corresponds to the order of the registration tokens.
					failed_tokens.append(registration_tokens[idx])
			app.logger.error('List of tokens that caused failures: {0}'.format(failed_tokens))
		elif response.success_count > 0 :
			
			app.logger.info(f'Successfully sent message: {response.success_count}, {response.responses}')
		
		response = {
			'message':{
				'success':200,
				'message':f'Notiifcation sent to {user_id} user'
				}
		}
		return response
	response = {
		'exc':{
			'status_code':404,
			'message':f'{user_id} not subscribed to push notifications'
			}
	}
	app.logger.info('Failed to send message:', response)
	return response, 400

@app.post("/api/method/notification_relay.api.send_notification.topic")
@basic_auth.login_required
def send_notification_to_topic():
	topic = request.args.get('topic_name')
	title = request.args.get('title')
	body = request.args.get('body')
	data = json.loads(request.args.get('data'))
	app.logger.debug(f'Topic Notification Request - {request.args}')
	message = messaging.Message(
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=title,
                body=body,
                icon='https://erpsgs.in/assets/raven/raven_mobile/favicon-64x64.png',
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
