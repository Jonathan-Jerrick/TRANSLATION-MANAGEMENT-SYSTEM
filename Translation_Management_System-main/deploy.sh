#!/bin/bash

# Translation Management System Deployment Script
# This script sets up and deploys the TMS application

set -e

echo "🚀 Starting Translation Management System Deployment..."

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

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating environment file from template..."
    cp env.example .env
    print_warning "Please edit .env file with your configuration before continuing."
    print_warning "Especially set your API keys for OpenAI, Anthropic, etc."
    read -p "Press Enter to continue after editing .env file..."
fi

# Create uploads directory
print_status "Creating uploads directory..."
mkdir -p uploads
chmod 755 uploads

# Create SSL directory for nginx
print_status "Creating SSL directory..."
mkdir -p ssl

# Build and start services
print_status "Building Docker images..."
docker-compose build

print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check if services are running
print_status "Checking service health..."

# Check database
if docker-compose exec -T db pg_isready -U tms_user -d tms_db > /dev/null 2>&1; then
    print_success "Database is ready"
else
    print_error "Database is not ready"
    exit 1
fi

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API is ready"
else
    print_error "Backend API is not ready"
    exit 1
fi

# Run database migrations
print_status "Running database migrations..."
docker-compose exec backend python -c "
from app.database import create_tables
create_tables()
print('Database tables created successfully')
"

# Seed initial data
print_status "Seeding initial data..."
docker-compose exec backend python -c "
from app.bootstrap import seed_initial_data
from app.database import get_db
from app.services import ProjectService, TranslationMemoryService, TermBaseService, NMTService
from app.state import state

# Initialize services
tm_service = TranslationMemoryService(state)
term_service = TermBaseService(state)
nmt_service = NMTService()
project_service = ProjectService(state, tm_service, term_service, nmt_service)

# Seed data
seed_initial_data(state, project_service, tm_service, term_service)
print('Initial data seeded successfully')
"

print_success "🎉 Translation Management System deployed successfully!"
print_status "Services are running:"
print_status "  - Frontend: http://localhost:3000"
print_status "  - Backend API: http://localhost:8000"
print_status "  - API Documentation: http://localhost:8000/docs"
print_status "  - Database: localhost:5432"
print_status "  - Redis: localhost:6379"

print_status "To view logs: docker-compose logs -f"
print_status "To stop services: docker-compose down"
print_status "To restart services: docker-compose restart"

echo ""
print_success "Deployment completed! 🚀"
