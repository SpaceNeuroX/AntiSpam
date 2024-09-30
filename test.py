import requests
from bs4 import BeautifulSoup

def gather_site_info(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return

    print(f"Site URL: {url}")
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")

    soup = BeautifulSoup(response.content, 'html.parser')
    paths = soup.find_all('path')  # Предположим, что пути хранятся в тегах <path>
    print("Paths:")
    for path in paths:
        print(f"- {path.text}")

if __name__ == "__main__":
    site_url = "https://real-dog-together.ngrok-free.app/"
    gather_site_info(site_url)