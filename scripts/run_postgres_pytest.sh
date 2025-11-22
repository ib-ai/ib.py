#!/bin/bash
# Run tests with test postgreSQL database

set -euo pipefail

message() {
    echo -e "\033[47;34m$1\033[0m"
}

success() {
    echo -e "\033[47;32m$1\033[0m"
}

warning() {
    echo -e "\033[47;31m$1\033[0m"
}

# Cleanup function to ensure database is always torn down
cleanup() {
    unset TESTING_ENV

    message "Tearing down test database..."
    docker-compose -f "$COMPOSE_FILE" down -v
    success "Cleanup completed!"
}
trap cleanup EXIT

# script starts here

COMPOSE_FILE="docker-compose.test.yml"
CONTAINER_NAME="ib-py-test-db"
export TESTING_ENV=true

# If database is running, teardown first
if docker ps --filter "status=running" | grep "$CONTAINER_NAME"; then
    warning "Test database is already running. Tearing down..."
    docker-compose -f "$COMPOSE_FILE" down -v
fi

# Start the test database
message "Starting test database..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for database to be healthy
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f "$COMPOSE_FILE" exec -T test-db pg_isready -U test_user -d test_ib_py > /dev/null 2>&1; then
        success "Test database is ready!"
        break
    fi
    attempt=$((attempt + 1))
    message "Attempting to connect... ($attempt/$max_attempts)"
    sleep 1
done

# Setup virtual environment if not already done
message "Setting up virtual environment..."
if ! command -v uv &> /dev/null; then
    warning "uv command not found. Please install uv (e.g., via \033[47;30mpip install uv\033[47;31m)."
    exit 1
fi
uv sync

# Run the tests
message "Running tests..."
uv run pytest "$@"
success "Tests completed!"
