import requests
from bs4 import BeautifulSoup
import json

def scrape_homepro_products():
    url = "https://www.homepro.co.th/search?searchtype=&q=tv+samsung"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    products = []
    
    # Find product containers
    product_items = soup.find_all('div', class_='product-item')
    
    for item in product_items:
        try:
            # Extract product name
            name_elem = item.find('h3') or item.find('a', class_='product-name')
            name = name_elem.get_text(strip=True) if name_elem else 'N/A'
            
            # Extract price
            price_elem = item.find('span', class_='price') or item.find('div', class_='price')
            price = price_elem.get_text(strip=True) if price_elem else 'N/A'
            
            # Extract product URL
            link_elem = item.find('a')
            link = link_elem.get('href') if link_elem else 'N/A'
            if link and not link.startswith('http'):
                link = 'https://www.homepro.co.th' + link
            
            products.append({
                'name': name,
                'price': price,
                'url': link
            })
            
        except Exception as e:
            continue
    
    return products

if __name__ == "__main__":
    products = scrape_homepro_products()
    
    print(f"Found {len(products)} products:")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['name']}")
        print(f"   Price: {product['price']}")
        print(f"   URL: {product['url']}")
        print()
    
    # Save to JSON file
    with open('samsung_tv_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"Data saved to samsung_tv_products.json")