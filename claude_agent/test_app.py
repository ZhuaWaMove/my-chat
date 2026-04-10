import subprocess
import time
import requests
import sys

def test_app():
    # Start server
    print("Starting server...")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(5)

    try:
        # Test root endpoint
        print("Testing root endpoint...")
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✓ Root endpoint works")
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")

        # Test sessions endpoint
        print("Testing sessions endpoint...")
        response = requests.get("http://localhost:8000/api/sessions/")
        if response.status_code == 200:
            print("✓ Sessions endpoint works")
        else:
            print(f"✗ Sessions endpoint failed: {response.status_code}")

        # Test creating a session
        print("Testing session creation...")
        response = requests.post("http://localhost:8000/api/sessions/", json={})
        if response.status_code == 200:
            session_id = response.json()["id"]
            print(f"✓ Session created: {session_id}")
        else:
            print(f"✗ Session creation failed: {response.status_code}")

    except Exception as e:
        print(f"Error during testing: {e}")

    finally:
        # Kill server
        print("Stopping server...")
        server.terminate()
        server.wait()
        print("Server stopped")

if __name__ == "__main__":
    test_app()
