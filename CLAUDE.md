# CLAUDE.md

所有对话都要使用中文

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an enterprise-grade website monitoring system (网址监控系统) built with Flask backend and Vue.js frontend. The system provides real-time website monitoring, intelligent grouping, status tracking, email notifications, and comprehensive user management.

## Development Commands

### Backend Development
```bash
# Initialize database
python init_database.py

# Start backend server (development)
python run_backend.py

# Database migrations
python database_migration_v5.py

# Check dependencies
pip install -r requirements.txt

# Create admin user
python create_admin_user.py
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
# Quick start (auto-build and deploy)
bash quick_start.sh

# Build images only
bash build_images.sh

# Full build and deploy
bash build_and_deploy.sh

# Standard deployment
docker-compose up -d

# Backend only
docker-compose -f docker-compose.backend-only.yml up -d

# Production environment
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Reset and rebuild
docker-compose down -v && docker-compose up -d --build
```

### Local Image Building
```bash
# Build backend image
docker build -t web-monitoring-backend:latest -f Dockerfile .

# Build frontend image
cd frontend
docker build -t web-monitoring-frontend:latest -f Dockerfile .

# Build both images
bash build_images.sh

# Build and deploy in one command
bash build_and_deploy.sh
```

### Database Operations
```bash
# MySQL connection test
mysql -u webmonitor -p -h localhost -P 33061 website_monitor

# Backup database
mysqldump -u webmonitor -p -h localhost -P 33061 website_monitor > backup.sql

# Restore database
mysql -u webmonitor -p -h localhost -P 33061 website_monitor < backup.sql
```

## Architecture Overview

### Application Factory Pattern
The Flask application uses a factory pattern in `backend/app.py` with modular blueprint registration:
- Authentication, website management, task scheduling, file handling
- Unified error handling for 404, 405, 400, 500 responses
- Request/response logging and performance monitoring
- CORS configuration and JWT token management

### Backend Service Architecture
**Core Services Pattern**: Business logic separated into `backend/services/` with specialized responsibilities:
- **Scheduler Service**: Thread-pool based task scheduling with adaptive sleep strategy
- **Detection Service**: Batch processing (batch_size=10, max_concurrent=5) with memory limits
- **Website Detector**: Three-state detection engine (standard/redirect/failed) with SSL validation
- **Memory Monitor**: Real-time memory monitoring with automatic cleanup
- **Email Notification**: SMTP-based alerting with template support

### Database Model Relationships
**Entity Architecture** in `backend/models.py`:
- **Many-to-many**: DetectionTask ↔ Website (through `task_websites` table)
- **One-to-many**: WebsiteGroup → Website, DetectionTask → DetectionRecord
- **Status Tracking**: WebsiteStatusChange with automatic state transitions
- **User Management**: Role-based access control (admin/user)
- **Composite Indexes**: Optimized queries on time, status, and website_id

### Frontend State Management
**Pinia Store Pattern** in `frontend/src/stores/user.js`:
- Reactive state: user, token, refreshToken with computed properties
- Authentication methods: login, logout, refresh with localStorage persistence
- Permission system: hasPermission, isAdmin, userRole validation
- Auto-refresh mechanism for token expiration handling

### API Architecture
**RESTful Design** with consistent response format:
- Authentication: JWT-based stateless authentication
- Caching: 30-second request caching with Axios interceptors
- Error handling: Unified error format with automatic retry logic
- Rate limiting: Per-user request limits with Flask-Limiter

### Task Scheduling System
**APScheduler Integration** with advanced features:
- Adaptive scheduling: Load-based frequency adjustment
- Concurrent task management: Thread pool with configurable limits
- Failed site monitoring: High-frequency monitoring for failed websites
- Memory-aware scheduling: Automatic cleanup based on memory usage

## Configuration

### Environment-Based Configuration
Configuration is managed through `backend/config.py` with three environments:
- **Development**: Debug enabled, SQL echo, SQLite default
- **Production**: Security headers, session cookies, MySQL required
- **Testing**: In-memory SQLite, CSRF disabled

### Critical Configuration Sections
```python
# Detection engine configuration
DETECTION_CONFIG = {
    'min_interval_minutes': 10,
    'max_concurrent': 20,
    'timeout_seconds': 30,
    'retry_times': 3,
    'follow_redirects': True,
    'verify_ssl': False
}

# Task scheduler configuration
SCHEDULER_CONFIG = {
    'timezone': 'Asia/Shanghai',
    'job_defaults': {
        'coalesce': False,
        'max_instances': 3
    }
}

# Data retention policies
DATA_RETENTION = {
    'detection_records_days': 90,
    'log_files_days': 30,
    'upload_files_days': 7
}
```

### Docker Environment Variables
```bash
# Database connection
DATABASE_URL=mysql://webmonitor:webmonitor123@mysql:3306/website_monitor

# Redis cache
REDIS_HOST=redis
REDIS_PORT=6379

# Application security
SECRET_KEY=WebMonitorSecretKey2024ChangeMeInProduction
FLASK_ENV=production
```

### Default Credentials
- Username: `admin`
- Password: `admin123`
- Change immediately after first login

### Admin Login Fix (If Login Fails)
If you encounter "username or password incorrect" error after Docker deployment:

```bash
# Method 1: Run fix script in container
docker compose exec backend python3 fix_login_container.py

# Method 2: Run fix script locally
python3 create_admin_fixed.py

# Method 3: Manual fix via Docker exec
docker compose exec backend python3 -c "
import sys, os
sys.path.insert(0, '/app')
os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'

from backend.app import create_app
from backend.models import User
from backend.database import get_db

app = create_app()
with app.app_context():
    with get_db() as db:
        # Delete existing admin
        existing = db.query(User).filter(User.username == 'admin').first()
        if existing:
            db.delete(existing)
            db.commit()
        
        # Create new admin
        admin = User(username='admin', email='admin@example.com', role='admin', status='active')
        admin.set_password('admin123')
        db.add(admin)
        db.commit()
        print('Admin user created successfully!')
"

# Method 4: Run the deployment fix script
bash deployment/fix-admin-login.sh
```

## Deployment Architecture

### Multi-Environment Docker Setup
The project supports multiple deployment configurations:
- **docker-compose.yml**: Full development stack (MySQL, Redis, Backend, Frontend)
- **docker-compose.prod.yml**: Production optimized with resource limits
- **docker-compose.backend-only.yml**: Backend-only deployment
- **docker-compose.with-nginx.yml**: Nginx reverse proxy included

### Service Dependencies
```yaml
# Health check dependencies
backend:
  depends_on:
    mysql:
      condition: service_healthy
    redis:
      condition: service_healthy
```

### Volume Management
Persistent data volumes:
- `mysql_data`: Database persistence
- `redis_data`: Cache persistence
- `backend_data`: Application logs
- `backend_uploads`: File uploads
- `backend_downloads`: Export files

## Performance Characteristics

### Memory Optimization
- **Optimized from 500MB+ to <200MB** (60-70% reduction)
- Real-time memory monitoring via `memory_monitor.py`
- Automatic garbage collection and cleanup
- Memory-aware task scheduling

### Detection Performance
- **Batch processing**: 10 websites per batch, 5 concurrent batches
- **Adaptive scheduling**: Load-based frequency adjustment
- **Three-state detection**: Standard, redirect, failed states
- **SSL validation**: Optional certificate verification

### Caching Strategy
- **Frontend**: 30-second API response caching
- **Backend**: Redis-based session and data caching
- **Database**: Connection pooling with pre-ping validation

## Common Development Patterns

### Error Handling Pattern
```python
# Backend API responses
{
    "success": True/False,
    "message": "Description",
    "data": {...},
    "error": {...}  # Only when success=False
}
```

### Authentication Flow
1. JWT token authentication with refresh mechanism
2. Role-based access control (admin/user)
3. Route guards in frontend with permission checks
4. Auto-refresh on token expiration

### Database Migration Pattern
- Use `database_migration_v*.py` for schema changes
- Always backup before running migrations
- Test migrations in development environment first

## Troubleshooting

### Container Issues
```bash
# Check container logs
docker-compose logs -f [service-name]

# Check health status
docker-compose ps

# Restart specific service
docker-compose restart [service-name]

# Clean rebuild
docker-compose down -v && docker-compose build --no-cache
```

### Database Connection Problems
```bash
# Test MySQL connection
mysql -u webmonitor -p -h localhost -P 33061

# Check MySQL container logs
docker-compose logs mysql

# Reset MySQL data
docker-compose down -v && docker volume rm webmonitor_mysql_data
```

### Memory Issues
```bash
# Monitor memory usage
docker stats

# Check backend memory logs
docker-compose logs backend | grep -i memory

# Restart backend to clear memory
docker-compose restart backend
```

## Security Implementation

### Authentication Security
- JWT tokens with configurable expiration
- Refresh token mechanism to prevent session hijacking
- Password hashing with secure algorithms
- Rate limiting on authentication endpoints

### API Security
- CORS configuration for cross-origin requests
- Input validation and sanitization
- SQL injection prevention through SQLAlchemy ORM
- Request size limits and timeout controls

### Production Security
- Secure session cookies (HttpOnly, Secure, SameSite)
- Environment-based configuration separation
- Database credentials management
- HTTPS enforcement in production

## Database Repair and Maintenance

### Critical Fix (2025-07-14)
System encountered database structure mismatch issues causing frontend error "Cannot read properties of null (reading 'websites')". Completely fixed through:

1. **Issue Diagnosis**: Database `websites` table missing required fields (`domain`, `original_url`, `normalized_url`, `description`, `group_id`)
2. **Database Repair**: Created comprehensive database initialization and repair scripts
3. **Structure Validation**: Ensured all table structures match application models

### Database Repair Scripts
```bash
# Fix database structure within container
docker-compose exec -T backend python3 /app/fix_database_container.py

# Or use complete initialization script
python3 database_init.py
```

### Required Database Fields
`websites` table must contain:
- id, name, url, domain, original_url, normalized_url
- description, group_id, is_active, check_interval, timeout
- created_at, updated_at

### Preventive Measures
- Built Docker images include `database_init.py` auto-initialization script
- Startup scripts automatically check and repair database structure
- Deployment to any platform won't encounter the same database issues