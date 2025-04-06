import requests

BASE_URL = "http://localhost:8000"

def test_create_url():
    print("\n=== Testing URL Creation ===")
    
    data = {
        "url": "https://www.example.com/example",
    }
    
    response = requests.post(f"{BASE_URL}/shorten", json=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Short URL: {BASE_URL}/{result['short_url']}")
        print(f"Original URL: {result['original_url']}")
        return result['short_url']
    else:
        print(f"Error: {response.text}")
        return None

def test_redirect(short_url):
    print("\n=== Testing URL Redirect ===")
    
    if not short_url:
        print("No short URL to test")
        return
        
    response = requests.get(f"{BASE_URL}/{short_url}", allow_redirects=False)
    print(f"Status Code: {response.status_code}")
    print(f"Redirect Location: {response.headers.get('Location')}")

def test_stats():
    print("\n=== Testing URL Stats ===")
    
    response = requests.get(f"{BASE_URL}/stats/")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Total URLs: {result['total_urls']}")
        print(f"Total Visits: {result['total_visits']}")
        print(f"First {len(result['urls'])} URLs:")
        for url in result['urls']:
            print(f"  - {url['short_url']} -> {url['original_url']} ({url['visits']} visits)")


if __name__ == "__main__":
    print("===== URL Shortener API Test =====")
    short_url = test_create_url()
    test_redirect(short_url)
    test_stats()