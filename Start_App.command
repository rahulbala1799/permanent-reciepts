#!/bin/bash

# Navigate to the app directory
cd "$(dirname "$0")"

# Kill any existing Flask app on port 5001
echo "Stopping any existing app on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 2

# Activate virtual environment and start the app
echo "Starting Flask app..."
source venv/bin/activate
python app.py

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "App encountered an error. Press any key to close..."
    read -n 1
fi


