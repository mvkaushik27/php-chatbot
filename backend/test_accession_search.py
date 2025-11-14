import requests
from bs4 import BeautifulSoup

# Test different field codes for accession/barcode search
test_queries = [
    'bc:"19365"',
    'barcode:"19365"',
    'accession:"19365"',
    'item:"19365"',
    '19365'  # Just the number
]

for query in test_queries:
    print(f'Testing query: {query}')
    try:
        response = requests.get('https://opac.iitrpr.ac.in/cgi-bin/koha/opac-search.pl',
                               params={'q': query}, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for results
        results = soup.find_all('div', class_=lambda x: x and 'result' in x.lower())
        print(f'  Found {len(results)} result divs')

        # Check title
        title_elem = soup.find('title')
        if title_elem:
            title_text = title_elem.get_text()
            if 'results of search' in title_text.lower():
                print(f'  SUCCESS: Found search results page')
                # Show first result title
                first_result = soup.find('div', class_=lambda x: x and 'result' in x.lower())
                if first_result:
                    title_link = first_result.find('a', href=lambda x: x and 'biblio' in x)
                    if title_link:
                        print(f'  First result: {title_link.get_text(strip=True)}')
                break
            else:
                print(f'  Title: {title_text[:100]}')

    except Exception as e:
        print(f'  Error: {e}')
    print()