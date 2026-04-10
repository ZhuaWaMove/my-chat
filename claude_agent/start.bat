@echo off
echo Starting Claude Agent...
echo.

REM Check if .env exists
if not exist ".env" (
    echo Warning: .env file not found.
    echo Copying .env.example to .env...
    copy .env.example .env > nul
    echo Please edit .env file and add your Claude API key.
    pause
    exit /b 1
)

REM Check if ANTHROPIC_API_KEY is set
findstr "ANTHROPIC_API_KEY" .env > nul
if %errorlevel% neq 0 (
    echo Warning: ANTHROPIC_API_KEY not found in .env file.
    echo Please add your Claude API key to the .env file.
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
python -c "import fastapi" > nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Initialize database
echo Initializing database...
python init_db.py

REM Start the application
echo Starting application...
echo.
echo Open your browser and navigate to: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server.
echo.

python run.py
