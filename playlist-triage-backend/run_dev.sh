# Development script for running with auto-reload
#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "🚀 Starting Playlist Triage API in development mode..."
echo "Environment: $ENVIRONMENT"
echo "Log Level: $LOG_LEVEL"
echo ""

# Run with auto-reload
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level debug