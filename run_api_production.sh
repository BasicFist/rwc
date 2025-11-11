#!/bin/bash
# Production-ready API server using Gunicorn

set -euo pipefail

echo "Starting RWC API Server (Production Mode)"
echo "=========================================="

# Check if virtual environment is activated
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Consider running: source venv/bin/activate"
fi

# Install gunicorn if not present
if ! command -v gunicorn &> /dev/null; then
    echo "Installing gunicorn..."
    pip install gunicorn
fi

# Configuration
WORKERS=${RWC_WORKERS:-4}
BIND_HOST=${FLASK_HOST:-127.0.0.1}
BIND_PORT=${FLASK_PORT:-5000}
TIMEOUT=${RWC_TIMEOUT:-120}

echo "Configuration:"
echo "  Workers: $WORKERS"
echo "  Bind: $BIND_HOST:$BIND_PORT"
echo "  Timeout: ${TIMEOUT}s"
echo ""

# Run with Gunicorn
exec gunicorn \
    --workers "$WORKERS" \
    --bind "$BIND_HOST:$BIND_PORT" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    rwc.api:app
