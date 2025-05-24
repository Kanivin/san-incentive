echo "Checking SQLite DB..."
[ -f /home/san-incentive/database/db.sqlite3 ] && cp /home/san-incentive/database/db.sqlite3 /app/db.sqlite3
echo "Running Django migrations..."
python manage.py migrate
echo "Loading initial setup data..."
python manage.py shell < incentives/initial_setup.py
echo "Starting Gunicorn..."
exec gunicorn app.wsgi:application --bind 0.0.0.0:8000