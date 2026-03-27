import requests

def test_api():
    try:
        response = requests.get("http://localhost:8000/api/air-quality/shanghai")
        print(f"Status: {response.status_code}")
        print(f"Data: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
