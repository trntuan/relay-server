FROM python:3.10.12-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/my-firebase.json

EXPOSE 8080

CMD ["gunicorn", "app:app", "-c", "gunicorn.conf.py"]
