#!/bin/sh
python manage.py makemigrations
python manage.py migrate --no-input

# python manage.py makemigrations api
# python manage.py migrate --no-input

python manage.py collectstatic --no-input
python manage.py createsuperuser --noinput --username=teiren --email=teiren@teiren.io --password=test1234!
python manage.py createsuperuser --noinput --username=finevoadmin --email=finevoadmin@finevo.io --password=test1234!

# python /app/src/initial/init.py # ?

gunicorn service.wsgi:application --bind 0.0.0.0:8000