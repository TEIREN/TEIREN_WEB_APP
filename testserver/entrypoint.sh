#!/bin/sh
python manage.py makemigrations
python manage.py migrate --no-input

# python manage.py makemigrations api
# python manage.py migrate --no-input

python manage.py collectstatic --no-input
python manage.py createsuperuser --noinput --username=yoonan --email=yoonan@teiren.io --password=cute428!

python /app/src/initial/init.py

gunicorn service.wsgi:application --bind 0.0.0.0:8000
