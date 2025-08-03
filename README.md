# songsorter

Web App that makes organizing songs into genre playlists easier.

## Features

- **Smart Playlist Triage**: Uses Spotify's audio features to suggest the best playlists for your songs
- **OAuth Integration**: Secure Spotify authentication
- **Industry Best Practices**: Clean architecture, proper error handling, and comprehensive logging
- **Health Monitoring**: Built-in health checks for production deployment
- **Docker Support**: Containerized for easy deployment

## Architecture

The backend follows industry best practices with:

- **Separation of Concerns**: Clear separation between routers, services, and data models
- **Dependency Injection**: Using FastAPI's DI system for loose coupling
- **Error Handling**: Custom exceptions and middleware for consistent error responses
- **Configuration Management**: Environment-based configuration with validation
- **Structured Logging**: Comprehensive logging throughout the application
- **Health Checks**: Ready/live probes for Kubernetes/Docker deployment

## Development Setup

### Prerequisites

- Python 3.10+
- Spotify Developer Account (for API credentials)

### Quick Start

1. **Clone and navigate to the backend:**
   ```bash
   cd playlist-triage-backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Spotify API credentials
   ```

4. **Run in development mode:**
   ```bash
   ./run_dev.sh
   # Or manually: uvicorn app.main:app --reload
   ```

5. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health/

### Environment Variables

Required variables (see `.env.example`):

- `SPOTIFY_CLIENT_ID`: Your Spotify app client ID
- `SPOTIFY_CLIENT_SECRET`: Your Spotify app client secret  
- `SPOTIFY_REDIRECT_URI`: OAuth redirect URI
- `APP_SECRET_KEY`: Secret key for application security

Optional variables:
- `ENVIRONMENT`: development/staging/production
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR
- `DEBUG`: true/false

## Production Deployment

### Docker

1. **Build the image:**
   ```bash
   docker build -t playlist-triage-api .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 \
     -e SPOTIFY_CLIENT_ID=your_id \
     -e SPOTIFY_CLIENT_SECRET=your_secret \
     -e APP_SECRET_KEY=your_key \
     -e ENVIRONMENT=production \
     playlist-triage-api
   ```

### Manual Production Setup

```bash
# Set environment to production
export ENVIRONMENT=production
export DEBUG=false

# Run with production settings
./run_prod.sh
```

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate Spotify OAuth
- `GET /auth/callback` - OAuth callback handler
- `POST /auth/logout` - Logout user

### Triage
- `GET /triage/next` - Get next song to sort with playlist suggestions

### Health & Monitoring
- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed health check with external service checks
- `GET /health/ready` - Readiness probe (Kubernetes)
- `GET /health/live` - Liveness probe (Kubernetes)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

The project includes configuration for:
- **Black**: Code formatting
- **isort**: Import sorting  
- **Flake8**: Linting
- **mypy**: Type checking

Install development dependencies:
```bash
pip install -e .[dev]
```

### Project Structure

```
playlist-triage-backend/
├── app/
│   ├── core/           # Core functionality (config, logging, exceptions)
│   ├── middleware/     # Custom middleware
│   ├── routers/        # API route handlers
│   ├── schemas/        # Pydantic models
│   ├── services/       # Business logic services
│   └── main.py         # FastAPI application
├── tests/              # Test suite
├── Dockerfile          # Container definition
├── pyproject.toml      # Project configuration
└── requirements.txt    # Dependencies
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all health checks pass
