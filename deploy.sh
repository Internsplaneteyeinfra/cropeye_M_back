#!/bin/bash

# Farm Management Backend Deployment Script
# This script helps deploy the Django backend to production

set -e  # Exit on any error

echo "🚀 Starting Farm Management Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f env.example ]; then
        cp env.example .env
        print_warning "Please edit .env file with your production values before continuing."
        print_warning "Especially update: SECRET_KEY, DB_PASSWORD, EMAIL credentials, etc."
        read -p "Press Enter after updating .env file..."
    else
        print_error "env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
source .env

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose are available."

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p ssl
mkdir -p media
mkdir -p staticfiles

# Set proper permissions
chmod 755 logs
chmod 755 ssl
chmod 755 media
chmod 755 staticfiles

# Build and start services
print_status "Building Docker images..."
docker-compose build --no-cache

print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if services are running
print_status "Checking service status..."
docker-compose ps

# Run database migrations
print_status "Running database migrations..."
docker-compose exec web python manage.py migrate

# Collect static files
print_status "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser (optional)
print_status "Creating superuser..."
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Check if application is responding
print_status "Checking application health..."
sleep 10

if curl -f http://localhost:${WEB_PORT:-8000}/api/health/ > /dev/null 2>&1; then
    print_success "Application is responding successfully!"
else
    print_warning "Application health check failed. Check logs with: docker-compose logs web"
fi

# Display deployment information
echo ""
print_success "🎉 Deployment completed successfully!"
echo ""
echo "📋 Deployment Information:"
echo "=========================="
echo "🌐 Application URL: http://localhost:${WEB_PORT:-8000}"
echo "🔧 Admin Panel: http://localhost:${WEB_PORT:-8000}/admin/"
echo "📚 API Documentation: http://localhost:${WEB_PORT:-8000}/swagger/"
echo "👤 Admin Credentials: admin / admin123"
echo ""
echo "📊 Service Status:"
echo "=================="
docker-compose ps
echo ""
echo "📝 Useful Commands:"
echo "==================="
echo "View logs:           docker-compose logs -f"
echo "View web logs:       docker-compose logs -f web"
echo "View db logs:        docker-compose logs -f db"
echo "Stop services:       docker-compose down"
echo "Restart services:    docker-compose restart"
echo "Update services:     docker-compose pull && docker-compose up -d"
echo "Access shell:        docker-compose exec web bash"
echo "Run migrations:      docker-compose exec web python manage.py migrate"
echo "Create superuser:    docker-compose exec web python manage.py createsuperuser"
echo ""
print_success "Deployment script completed!"