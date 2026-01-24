web: python manage.py collectstatic --noinput && python manage.py migrate && python create_admin.py && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
