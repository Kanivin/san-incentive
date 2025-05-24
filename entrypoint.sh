# cp /home/san-incentive/database/db.sqlite3 /app/db.sqlite3
[ -f /home/san-incentive/database/db.sqlite3 ] || [ ! -f /app/db.sqlite3 ] && cp /home/san-incentive/database/db.sqlite3 /app/db.sqlite3

# python manage.py flush  # Clears all data

# Run migrate
#python manage.py migrate --run-syncdb  # Applies all migrations
python manage.py migrate --noinput

# setup_initial_data
python manage.py shell < incentives/initial_setup.py


gunicorn app.wsgi:application --bind 0.0.0.0:8000