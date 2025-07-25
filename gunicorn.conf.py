# gunicorn.conf.py
# Non logging stuff
bind = "0.0.0.0:8080"
workers = 1
# Access log - records incoming HTTP requests
accesslog = "./log/gunicorn.access.log"
# Error log - records Gunicorn server goings-on
errorlog = "./log/gunicorn.error.log"
# Whether to send Django output to the error log
capture_output = True
# How verbose the Gunicorn error logs should be 
loglevel = "debug"
