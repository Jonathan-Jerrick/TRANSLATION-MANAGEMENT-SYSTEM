# Translation Management System - Setup Guide

This guide will help you set up and deploy the Translation Management System (TMS) in your environment.

## 🚀 Quick Start (Recommended)

### 1. Prerequisites
- Docker and Docker Compose installed
- Git installed
- At least 4GB RAM available
- Ports 80, 3000, 5432, 6379, 8000 available

### 2. Clone and Deploy
```bash
# Clone the repository
git clone <repository-url>
cd Translation_Management_System-main

# Make deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

### 3. Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit the environment file
nano .env
```

**Required Environment Variables:**
```bash
# Database Configuration
DATABASE_URL=postgresql://tms_user:tms_password@localhost:5432/tms_db
REDIS_URL=redis://localhost:6379

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# LLM API Keys (REQUIRED FOR TRANSLATION FEATURES)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Development Setup

### Backend Development

#### 1. Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Database Setup
```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Run database migrations
python -c "from app.database import create_tables; create_tables()"

# Seed initial data
python -c "
from app.bootstrap import seed_initial_data
from app.database import get_db
from app.services import ProjectService, TranslationMemoryService, TermBaseService, NMTService
from app.state import state

tm_service = TranslationMemoryService(state)
term_service = TermBaseService(state)
nmt_service = NMTService()
project_service = ProjectService(state, tm_service, term_service, nmt_service)

seed_initial_data(state, project_service, tm_service, term_service)
print('Initial data seeded successfully')
"
```

#### 3. Start Development Server
```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Start Development Server
```bash
npm run dev
```

## 🐳 Docker Deployment

### Development Environment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Environment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔐 Security Configuration

### 1. Generate Secure Keys
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT secret
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Database Security
```bash
# Change default database credentials
POSTGRES_USER=your_secure_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=your_secure_db_name
```

### 3. SSL Configuration (Production)
```bash
# Generate SSL certificates
mkdir ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem
```

## 📊 Monitoring Setup

### 1. Prometheus Configuration
```bash
# Create prometheus.yml
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'tms-backend'
    static_configs:
      - targets: ['backend:8000']
EOF
```

### 2. Grafana Dashboard
- Access Grafana at http://localhost:3001
- Default credentials: admin/admin
- Import TMS dashboard from `/monitoring/grafana-dashboard.json`

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_workflow.py -v
```

### Frontend Tests
```bash
cd frontend

# Run unit tests
npm test

# Run e2e tests
npm run test:e2e

# Run linting
npm run lint
```

## 🚀 Production Deployment

### 1. Environment Preparation
```bash
# Set production environment variables
export NODE_ENV=production
export PYTHON_ENV=production

# Configure reverse proxy (Nginx)
sudo cp nginx.prod.conf /etc/nginx/sites-available/tms
sudo ln -s /etc/nginx/sites-available/tms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 3. Database Backup
```bash
# Create backup script
cat > backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U tms_user tms_db > backup_\$DATE.sql
EOF

chmod +x backup.sh
```

### 4. Monitoring Setup
```bash
# Start monitoring stack
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Configure alerts
cp monitoring/alerts.yml /etc/prometheus/
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready -U tms_user -d tms_db

# Reset database
docker-compose down -v
docker-compose up -d db
```

#### 2. Redis Connection Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

#### 3. Backend API Issues
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

#### 4. Frontend Build Issues
```bash
# Clear node modules
cd frontend
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_projects_status ON projects(status);
CREATE INDEX CONCURRENTLY idx_segments_project_id ON segments(project_id);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
```

#### 2. Redis Configuration
```bash
# Optimize Redis for production
echo "maxmemory 256mb" >> redis.conf
echo "maxmemory-policy allkeys-lru" >> redis.conf
```

#### 3. Nginx Optimization
```nginx
# Add to nginx.conf
worker_processes auto;
worker_connections 1024;

# Enable gzip compression
gzip on;
gzip_types text/plain application/json application/javascript text/css;
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## 🆘 Support

If you encounter any issues:

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure all required ports are available
4. Check database and Redis connectivity
5. Verify API keys are correctly set

For additional help, create an issue in the GitHub repository.
