import requests
from bs4 import BeautifulSoup
import re

# Test a simple OPAC search
url = 'https://opac.iitrpr.ac.in/cgi-bin/koha/opac-search.pl'
params = {'q': 'title:"machine learning"'}

print('Testing OPAC search...')

try:
    response = requests.get(url, params=params, timeout=10)
    print(f'Status: {response.status_code}')

    soup = BeautifulSoup(response.content, 'html.parser')

    # Look for book records
    book_records = soup.find_all('div', class_=re.compile(r'result', re.I))
    print(f'Found {len(book_records)} book record divs')

    # Examine the first few records in detail
    for i, record in enumerate(book_records[:3]):
        print(f'\n--- Record {i+1} ---')
        print(f'Record classes: {record.get("class")}')

        # Get the full text
        record_text = record.get_text()
        print(f'Full text length: {len(record_text)}')
        print(f'First 300 chars: {record_text[:300]}')

        # Look for availability-related text
        availability_keywords = ['available', 'issued', 'checked out', 'on loan', 'borrowed', 'reference', 'not issued', 'on shelf']
        found_keywords = [word for word in availability_keywords if word in record_text.lower()]
        print(f'Found availability keywords: {found_keywords}')

        # Look for specific HTML elements that might contain availability
        availability_spans = record.find_all(['span', 'div'], class_=re.compile(r'status|available|issue', re.I))
        print(f'Found {len(availability_spans)} potential availability elements')

        for span in availability_spans[:3]:  # Show first 3
            print(f'  Element: {span.name}, class: {span.get("class")}, text: "{span.get_text(strip=True)}"')

        # Look for any elements with status-like text
        all_spans = record.find_all(['span', 'div', 'td'])
        status_candidates = []
        for elem in all_spans:
            text = elem.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['available', 'issued', 'checked', 'loan', 'borrow', 'reference']):
                status_candidates.append(f'{elem.name}: "{elem.get_text(strip=True)}"')

        print(f'Status candidates: {status_candidates[:5]}')  # Show first 5

except Exception as e:
    print(f'Error: {e}')