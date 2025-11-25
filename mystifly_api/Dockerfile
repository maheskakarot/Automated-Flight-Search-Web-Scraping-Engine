FROM python:3.8-slim-bullseye
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1 \
    PORT=7000

ENV TZ=Asia/Kolkata

RUN apt-get update && apt-get install -y wget gnupg ca-certificates
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
ARG CHROME_VERSION="114.0.5735.133-1"
RUN wget --no-verbose -O /tmp/chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb \
  && apt install -y /tmp/chrome.deb \
  && rm /tmp/chrome.deb \
  &&  apt-get install -y cron


WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN rm -rf /usr/local/lib/python3.8/site-packages/selenium/webdriver/common/service.py
RUN cp service.py /usr/local/lib/python3.8/site-packages/selenium/webdriver/common/service.py
RUN python manage.py makemigrations ryanair account v6 custom_logger easyjet
RUN python manage.py migrate
RUN python manage.py crontab add
EXPOSE 7000
ENTRYPOINT service cron start && gunicorn -w 32 --bind 0.0.0.0:7000 --timeout 300 mystifly_api.wsgi