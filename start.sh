#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting Django application..."

# Create logs directory if it doesn't exist (important for volume mounts)
mkdir -p /app/logs

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
DB_HOST=${DB_HOST:-localhost} # Default to localhost if not set
DB_PORT=${DB_PORT:-5432}     # Default to 5432 if not set

until nc -z -v -w30 "$DB_HOST" "$DB_PORT"; do
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  sleep 5
done
echo "✅ Database is up and running!"

# Apply database migrations. This is the standard and safe way.
echo "📊 Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start the application
echo "🌐 Starting Gunicorn server..."
exec gunicorn farm_management.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile -
