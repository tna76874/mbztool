FROM python:3.7.7

LABEL maintainer="dev@hilberg.eu"

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY requirements_web.txt ./
COPY requirements_build.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt -r requirements_web.txt -r requirements_build.txt

COPY . .

RUN python build.py -v && rm -rf /usr/src/app/.git

EXPOSE 5000

ENV LOG_LEVEL=debug
ENV GUNICORN_TIMEOUT=120
ENV UPLOAD_LIMIT_GB=0.5

CMD [ "sh", "-c", "gunicorn --workers=5 --timeout ${GUNICORN_TIMEOUT} --bind=0.0.0.0:5000 --log-level=${LOG_LEVEL} --access-logfile=- app:app" ]
