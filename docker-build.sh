#!/bin/bash
set -e

echo "🐳 Building SRTgo Web Docker Image..."

# Generate secret key if not exists
if [ ! -f .env ]; then
    echo "📝 Generating .env file..."
    cp .env.docker .env
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/please-change-this-secret-key-in-production/$SECRET_KEY/" .env
    echo "✓ .env file created with random SECRET_KEY"
fi

# Build Docker image
echo "📦 Building Docker image..."
docker-compose build

echo ""
echo "✅ Build complete!"
echo ""
echo "To start the application:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "Application will be available at:"
echo "  http://localhost:8000"
echo ""
