# Translation Management System (TMS)

A comprehensive, production-ready Translation Management System that combines automated content ingestion, neural machine translation (NMT), and expert human review into a single platform.

## 🚀 Features

### Core Capabilities
- **Content Connectivity** – Native connectors for CMS platforms and Git repositories
- **Translation Pipeline** – NMT with quality estimation, risk scoring, and human post-editing
- **Knowledge Assets** – Translation Memory (TM), Terminology Base (TB), and domain-specific glossaries
- **CAT Workspace** – Browser-based CAT tools with segment editor, TM/TB lookup, QA checks
- **Real-time Collaboration** – WebSocket-based real-time editing and collaboration
- **Quality & Analytics** – MTQE dashboards, MQM error tagging, productivity metrics
- **Security & Compliance** – Role-based access, JWT authentication, audit trails

### LLM Integration
- **OpenAI GPT-4** for high-quality translations
- **Anthropic Claude** for alternative translation approaches
- **Google Gemini** for additional translation options
- **Quality Estimation** using AI-powered quality scoring
- **Improvement Suggestions** with AI-generated recommendations

### Modern Tech Stack
- **Backend**: FastAPI, PostgreSQL, Redis, WebSockets
- **Frontend**: React 18, TypeScript, Tailwind CSS, Zustand
- **Real-time**: WebSocket connections for live collaboration
- **Deployment**: Docker, Docker Compose, Nginx

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd Translation_Management_System-main
```

### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

### 3. Deploy with Docker
```bash
chmod +x deploy.sh
./deploy.sh
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Development Setup

### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Run database migrations
python -c "from app.database import create_tables; create_tables()"

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📚 API Documentation

The API is fully documented with OpenAPI/Swagger. Access the interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

#### Projects
- `GET /projects` - List all projects
- `POST /projects` - Create a new project
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project

#### Translation
- `POST /translate` - Translate text using LLM
- `POST /quality-estimate` - Estimate translation quality
- `POST /suggest-improvements` - Get improvement suggestions

#### Real-time Collaboration
- `WebSocket /ws/{user_id}` - Real-time collaboration endpoint

## 🏗️ Architecture

### Backend Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI      │    │   PostgreSQL     │    │     Redis        │
│   Application  │◄──►│   Database       │    │     Cache        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   LLM Services  │
│   Real-time     │    │   (OpenAI, etc) │
└─────────────────┘    └─────────────────┘
```

### Frontend Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   Zustand       │    │   React Query   │
│   (TypeScript)  │◄──►│   State Mgmt    │    │   Data Fetching │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│   WebSocket      │    │   Tailwind CSS  │
│   Real-time      │    │   Styling       │
└─────────────────┘    └─────────────────┘
```

## 🔐 Security Features

- **JWT Authentication** with secure token management
- **Role-based Access Control** (Admin, Manager, Translator, Reviewer, Client)
- **Password Hashing** using bcrypt
- **CORS Protection** with configurable origins
- **Input Validation** using Pydantic models
- **SQL Injection Protection** with SQLAlchemy ORM
- **XSS Protection** with proper content sanitization

## 📊 Monitoring & Logging

- **Structured Logging** with JSON format
- **Health Checks** for all services
- **Performance Metrics** with Prometheus
- **Error Tracking** with detailed stack traces
- **Audit Trails** for all user actions

## 🚀 Production Deployment

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# LLM APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760
```

### Docker Production
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_workflow.py
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

## 📈 Performance

- **Database Indexing** for optimal query performance
- **Redis Caching** for frequently accessed data
- **Connection Pooling** for database connections
- **Async Processing** for background tasks
- **CDN Ready** for static asset delivery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🎯 Roadmap

- [ ] Advanced Analytics Dashboard
- [ ] Machine Learning Model Training
- [ ] Mobile Application
- [ ] Enterprise SSO Integration
- [ ] Advanced Workflow Automation
- [ ] Multi-tenant Architecture

---

**Built with ❤️ for the translation community**