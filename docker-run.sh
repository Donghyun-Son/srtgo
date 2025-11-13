#!/bin/bash
set -e

echo "🚀 Starting SRTgo Web..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Run ./docker-build.sh first to generate .env"
    exit 1
fi

# Start containers
docker-compose up -d

echo ""
echo "✅ SRTgo Web is starting..."
echo ""
echo "Checking health..."
sleep 5

# Check health
if docker-compose ps | grep -q "Up"; then
    echo "✓ Container is running"
    echo ""
    echo "Application is available at:"
    echo "  🌐 http://localhost:8000"
    echo ""
    echo "API Documentation:"
    echo "  📚 http://localhost:8000/docs"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "To stop:"
    echo "  docker-compose down"
else
    echo "❌ Failed to start. Check logs:"
    docker-compose logs
    exit 1
fi
