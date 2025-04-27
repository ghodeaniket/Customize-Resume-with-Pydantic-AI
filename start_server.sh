#!/bin/bash
#
# Resume Customizer Server Startup Script
#
# This script sets up and starts the Resume Customizer server
# with appropriate configuration for testing.
#

# Set default values
PORT=8000
DEBUG=true
TEST_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --port)
      PORT="$2"
      shift
      shift
      ;;
    --no-debug)
      DEBUG=false
      shift
      ;;
    --test-mode)
      TEST_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set up the server
echo "Setting up the server..."
if [ "$TEST_MODE" = true ]; then
  python server_setup.py --port $PORT --debug --test-mode
else
  python server_setup.py --port $PORT $([ "$DEBUG" = true ] && echo "--debug")
fi

# Start the server
echo "Starting server on port $PORT..."
if [ "$DEBUG" = true ]; then
  python run.py --port $PORT --reload
else
  python run.py --port $PORT
fi
