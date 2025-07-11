# CLAUDE.md

所有对话都要使用中文

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive website monitoring system (网址监控系统) built with Flask backend and Vue.js frontend. The system monitors website availability, tracks status changes, sends email notifications, and provides user management capabilities.

## Development Commands

### Backend Development
```bash
# Initialize database
python init_database.py

# Start backend server (development)
python run_backend.py

# Start backend server (production with Docker)
docker-compose up -d

# Database migrations
python database_migration_v5.py
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker Operations
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Architecture Overview

### Backend Structure
- **Flask Application**: Main app factory in `backend/app.py`
- **Database Models**: SQLAlchemy models in `backend/models.py`
- **API Endpoints**: RESTful APIs in `backend/api/` directory
- **Services**: Business logic in `backend/services/` directory
- **Configuration**: Environment-based config in `backend/config.py`

### Key Backend Components
- **Authentication**: JWT-based user authentication (`backend/api/auth.py`)
- **Website Detection**: Asynchronous website monitoring (`backend/services/website_detector.py`)
- **Task Scheduling**: APScheduler for automated monitoring (`backend/services/scheduler_service.py`)
- **Memory Management**: Optimized memory usage (`backend/services/memory_monitor.py`)
- **File Management**: Upload/download handling (`backend/api/files.py`)

### Frontend Structure
- **Vue 3**: Main framework with Composition API
- **Element Plus**: UI component library
- **Pinia**: State management
- **Vue Router**: Client-side routing
- **Vite**: Build tool and development server

### Key Frontend Components
- **Authentication**: User store and login system (`frontend/src/stores/user.js`)
- **API Integration**: Axios-based API client (`frontend/src/utils/api.js`)
- **Performance Monitoring**: Client-side performance tracking (`frontend/src/utils/performance.js`)
- **Routing**: Protected routes and navigation (`frontend/src/router/index.js`)

## Database Schema

### Core Tables
- `websites`: Website information and URLs
- `website_groups`: Website grouping and organization
- `detection_records`: Website monitoring results
- `detection_tasks`: Scheduled monitoring tasks
- `website_status_changes`: Status change tracking
- `users`: User authentication and management
- `system_settings`: Application configuration

### Key Relationships
- Websites belong to groups (many-to-one)
- Detection records link to websites and tasks
- Status changes track website state transitions
- Tasks can monitor multiple websites (many-to-many)

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=mysql://user:password@localhost:3306/website_monitor
# or
DATABASE_URL=sqlite:///database/website_monitor.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret

# Email Settings
MAIL_SERVER=smtp.qq.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@qq.com
MAIL_PASSWORD=your-app-password

# Application
FLASK_ENV=production
LOG_LEVEL=INFO
```

### Default Login Credentials
- Username: `admin`
- Password: `admin123`

## Development Guidelines

### Backend Development
- Follow Flask blueprint pattern for API organization
- Use SQLAlchemy models with proper relationships
- Implement proper error handling and logging
- Use decorators for authentication and rate limiting
- Optimize database queries with proper indexing

### Frontend Development
- Use Vue 3 Composition API consistently
- Implement reactive state management with Pinia
- Follow Element Plus component patterns
- Use async/await for API calls
- Implement proper error handling and user feedback

### Code Quality
- Backend: Follow PEP 8 style guide
- Frontend: Use ESLint and Prettier for formatting
- Write descriptive commit messages
- Use meaningful variable and function names
- Implement proper error handling

## Testing

### Backend Testing
```bash
# Run tests (when implemented)
python -m pytest tests/

# Test database connection
python -c "from backend.database import get_db; print('DB connection OK')"
```

### Frontend Testing
```bash
cd frontend

# Run unit tests (when implemented)
npm test

# Check build
npm run build
```

## Performance Optimization

### Backend Optimizations
- Connection pooling for database
- Memory monitoring and garbage collection
- Async HTTP requests for website detection
- Caching with Redis (optional)
- Task scheduling optimization

### Frontend Optimizations
- Code splitting and lazy loading
- Element Plus tree-shaking
- Optimized build configuration
- Component-level performance monitoring
- API response caching

## Common Issues and Solutions

### Database Connection Issues
- Check MySQL/SQLite connection strings
- Verify database permissions
- Run database initialization script
- Check for port conflicts

### Memory Management
- Monitor memory usage in production
- Use memory optimization services
- Implement proper cleanup on shutdown
- Regular garbage collection

### Email Notifications
- Verify SMTP server settings
- Check email credentials and app passwords
- Ensure firewall allows SMTP ports
- Test email configuration

## Deployment

### Docker Deployment (Recommended)
```bash
# Full stack deployment
docker-compose up -d

# Production environment variables
cp .env.template .env
# Edit .env with production values
```

### Manual Deployment
```bash
# Backend
pip install -r requirements.txt
python init_database.py
python run_backend.py

# Frontend
cd frontend
npm install
npm run build
# Deploy dist/ to web server
```

## Security Considerations

- Change default admin credentials
- Use strong SECRET_KEY in production
- Enable HTTPS in production
- Regular security updates
- Input validation and sanitization
- Rate limiting on APIs
- Secure database connections

## API Documentation

### Authentication
- `POST /api/auth/login`: User login
- `POST /api/auth/logout`: User logout
- `GET /api/auth/user`: Get current user

### Website Management
- `GET /api/websites`: List websites
- `POST /api/websites`: Add website
- `PUT /api/websites/{id}`: Update website
- `DELETE /api/websites/{id}`: Delete website

### Monitoring
- `GET /api/results`: Get monitoring results
- `GET /api/status-changes`: Get status changes
- `POST /api/tasks`: Create monitoring task
- `GET /api/tasks/{id}/run`: Run task manually

### System
- `GET /api/health`: Health check
- `GET /api/system/info`: System information
- `GET /api/performance`: Performance metrics