# Production script for running the API
#!/bin/bash

echo "🚀 Starting Playlist Triage API in production mode..."

# Run with optimized settings for production
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --no-server-header