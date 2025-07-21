# gunicorn.conf.py
# Non logging stuff
bind = "0.0.0.0:5000"
workers = 1
# Access log - records incoming HTTP requests
accesslog = "/home/dev/workspace/projects/frappe/relay-server/relay-server/log/gunicorn.access.log"
# Error log - records Gunicorn server goings-on
errorlog = "/home/dev/workspace/projects/frappe/relay-server/relay-server/log/gunicorn.error.log"
# Whether to send Django output to the error log
capture_output = True
# How verbose the Gunicorn error logs should be 
loglevel = "debug"
