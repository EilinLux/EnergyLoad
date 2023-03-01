FROM python:3.7-slim-stretch

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY app .

RUN pip install -r requirements.txt
ENV PORT 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 3 main:app --timeout 0 
# https://cloud.google.com/appengine/docs/standard/python3/runt