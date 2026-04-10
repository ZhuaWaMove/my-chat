#!/bin/bash

echo "Starting Claude Agent..."
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found."
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Please edit .env file and add your Claude API key."
    exit 1
fi

# Check if anthropic_api_key is set
if ! grep -q "anthropic_api_key" .env; then
    echo "Warning: anthropic_api_key not found in .env file."
    echo "Please add your Claude API key to the .env file."
    exit 1
fi

# Install dependencies if needed
echo "Checking dependencies..."
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Initialize database
echo "Initializing database..."
python init_db.py

# Start the application
echo "Starting application..."
echo
echo "Open your browser and navigate to: http://localhost:8000"
echo
echo "Press Ctrl+C to stop the server."
echo

python run.py
