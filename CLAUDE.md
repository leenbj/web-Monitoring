# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Website Monitoring Tool (网址监控工具) - a full-stack web application for batch monitoring Chinese domain websites. The application detects three states: standard resolution (中文域名正常), redirect resolution (跳转到英文域名), and failed access (无法访问).

## Development Commands

### Backend Commands
```bash
# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start backend server (Flask on port 5001)
python run_backend.py

# Run individual test files
python test_core_api.py
python test_api.py
python test_performance.py

# Database migrations
python database_migration_v4.py
python database_migration_v5.py
```

### Frontend Commands
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server (Vue.js on port 3000)
npm run dev

# Build for production
npm run build
```

### Project Management Scripts
```bash
# Use the comprehensive project manager
./project_manager.sh start      # Start both backend and frontend
./project_manager.sh status     # Check service status
./project_manager.sh stop       # Stop all services
./project_manager.sh restart    # Restart all services
./project_manager.sh logs       # View service logs

# Or use individual scripts
./前端启动脚本.sh               # Start frontend only
```

## Architecture Overview

### Backend Architecture (Flask + SQLAlchemy)

**Core Structure:**
- `app.py` - Flask application factory with blueprint registration
- `database.py` - High-concurrency SQLite configuration (QueuePool with 50 connections)
- `models.py` - SQLAlchemy models with Beijing timezone support and optimized indexing
- `config.py` - Environment-based configuration management

**Service Layer Pattern:**
- `services/website_detector.py` - Core detection engine with sync/async modes
- `services/scheduler_service.py` - APScheduler-based task management
- `services/detection_service.py` - Orchestrates monitoring workflows
- `services/batch_detector.py` - High-performance batch processing
- `services/async_detector.py` - Asynchronous HTTP request handling

**API Layer (Blueprint-based):**
- `api/websites.py` - Website CRUD with batch import/export
- `api/tasks.py` - Detection task lifecycle management
- `api/results.py` - Results querying with filtering and statistics
- `api/groups.py` - Website categorization
- `api/files.py` - File upload/download handling

### Frontend Architecture (Vue.js 3 + Element Plus)

**Build System:**
- Vite with hot module replacement
- Development proxy to backend (localhost:5001)
- ES modules with modern JavaScript

**Component Structure:**
- `src/App.vue` - Root component with Element Plus integration
- `src/router/index.js` - Hash-based routing configuration
- `src/utils/api.js` - Centralized API client with interceptors
- `src/views/` - Page-level components (Home, Websites, Tasks, Results, etc.)

### Data Models

**Core Entities:**
- `Website` - Target monitoring sites with URL normalization
- `DetectionTask` - Scheduled jobs with configurable intervals
- `DetectionRecord` - Historical results with response metrics
- `WebsiteGroup` - Organizational categorization
- `WebsiteStatusChange` - Audit trail for status transitions

## Key Implementation Details

### Website Detection Logic
The detection engine (`WebsiteDetector`) implements intelligent mode selection:
- **Synchronous mode**: ThreadPoolExecutor for smaller batches or when async unavailable
- **Asynchronous mode**: aiohttp for large-scale concurrent detection
- **Three-state classification**: Analyzes final URL domain to determine standard/redirect/failed status
- **Retry strategy**: Configurable retries for network resilience

### Database Optimization
- QueuePool configuration for high concurrency (50 connections, 100 max overflow)
- Strategic indexing on frequently queried fields
- Context manager pattern for automatic session management
- Beijing timezone handling for consistent datetime operations

### Task Scheduling
- APScheduler with thread pool execution
- Dynamic task management (add/remove/modify jobs at runtime)
- Failed site monitoring with specialized intervals
- Status change detection and notification system

### File Processing
- Pandas-based Excel/CSV parsing with automatic column detection
- Batch website import with data validation
- Export functionality with customizable formats
- File cleanup services for storage management

## Development Workflow

### API Testing
The project includes comprehensive test files:
- `test_core_api.py` - Basic CRUD operations
- `test_api.py` - Extended API functionality
- `test_performance.py` - Performance benchmarks
- All tests target `http://localhost:5001` and require running backend

### Configuration Management
- Environment variables loaded via python-dotenv
- Development/production configurations in `config.py`
- Database path: `database/website_monitor.db`
- File storage: `uploads/` and `downloads/` directories

### Logging and Monitoring
- Structured logging to `logs/` directory
- Service-specific log files (backend.log, frontend.log)
- Performance monitoring APIs available
- Status change tracking for audit purposes

## Port Configuration
- Backend (Flask): http://localhost:5001
- Frontend (Vue.js): http://localhost:3000
- API proxy configuration handles cross-origin requests during development

## Important Notes

- The application uses SQLite with connection pooling optimizations for high-concurrency scenarios
- Chinese domain detection relies on final URL analysis after following redirects
- APScheduler runs in background threads and persists across application restarts
- File uploads are limited to 16MB with support for .xlsx, .xls, and .csv formats
- Beijing timezone (UTC+8) is used consistently throughout the application