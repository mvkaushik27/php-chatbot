import requests
from bs4 import BeautifulSoup
import re

# Test a simple OPAC search
url = 'https://opac.iitrpr.ac.in/cgi-bin/koha/opac-search.pl'
params = {'q': 'title:"machine learning"'}

print('Testing OPAC search...')
print(f'URL: {url}')
print(f'Params: {params}')

try:
    response = requests.get(url, params=params, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content length: {len(response.text)}')

    soup = BeautifulSoup(response.content, 'html.parser')

    # Look for results
    results = soup.find_all(['div', 'table'], class_=lambda x: x and ('result' in x.lower() or 'item' in x.lower()))
    print(f'Found {len(results)} potential result elements')

    # Look for result count
    match = re.search(r'(\d+)\s+results?\s+found', response.text, re.IGNORECASE)
    if match:
        print(f'Results found: {match.group(1)}')
    else:
        print('No result count found in page')

    # Look for book records
    book_records = soup.find_all('div', class_=re.compile(r'result', re.I))
    print(f'Found {len(book_records)} book record divs')

    # Show first 1000 chars of response
    print(f'First 1000 chars: {response.text[:1000]}')

except Exception as e:
    print(f'Error: {e}')