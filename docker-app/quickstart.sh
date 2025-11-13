#!/bin/bash
# Crosshatch API Quick Start Script

set -e

echo "=========================================="
echo "Crosshatch API Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker is installed"

# Check for GPU support
GPU_AVAILABLE=false
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        GPU_AVAILABLE=true
        echo "✓ NVIDIA GPU detected"
    fi
fi

if [ "$GPU_AVAILABLE" = false ]; then
    echo "ℹ No GPU detected, will use CPU version"
fi

# Ask user which version to use
echo ""
echo "Which version do you want to run?"
echo "1) GPU version (faster, requires NVIDIA GPU)"
echo "2) CPU version (slower, works everywhere)"
echo ""

read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        if [ "$GPU_AVAILABLE" = false ]; then
            echo ""
            echo "⚠️  Warning: No GPU detected, but GPU version selected."
            read -p "Continue anyway? (y/n): " confirm
            if [ "$confirm" != "y" ]; then
                echo "Exiting..."
                exit 0
            fi
        fi
        COMPOSE_FILE="docker-compose.yml"
        VERSION="GPU"
        ;;
    2)
        COMPOSE_FILE="docker-compose.cpu.yml"
        VERSION="CPU"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Starting Crosshatch API ($VERSION version)"
echo "=========================================="
echo ""

# Go to project root
cd "$(dirname "$0")/.."

# Start the service
echo "Building and starting container..."
docker-compose -f "$COMPOSE_FILE" up -d

echo ""
echo "Waiting for service to be healthy..."
sleep 5

# Check if service is running
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo ""
        echo "✓ Service is running!"
        break
    fi
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo ""
    echo "❌ Service failed to start. Check logs:"
    echo "   docker-compose -f $COMPOSE_FILE logs"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ Crosshatch API is ready!"
echo "=========================================="
echo ""
echo "API URL: http://localhost:5000"
echo ""
echo "Try it out:"
echo "  curl http://localhost:5000/health"
echo ""
echo "Process an image:"
echo "  curl -X POST -F \"file=@your_image.jpg\" http://localhost:5000/api/crosshatch -o output.jpg"
echo ""
echo "View logs:"
echo "  docker-compose -f $COMPOSE_FILE logs -f"
echo ""
echo "Stop service:"
echo "  docker-compose -f $COMPOSE_FILE down"
echo ""
