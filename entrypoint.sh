echo "Running Django migrations..."
python manage.py migrate
# First time only
# echo "Loading initial setup data..."
# python manage.py shell < incentives/initial_setup.py
echo "Starting Gunicorn..."
exec gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 1 --timeout 120 --limit-request-line 8190 --limit-request-field_size 8190 --limit-request-fields 100