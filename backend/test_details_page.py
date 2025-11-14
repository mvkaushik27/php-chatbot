import requests
from bs4 import BeautifulSoup
import re

response = requests.get('https://opac.iitrpr.ac.in/cgi-bin/koha/opac-search.pl', params={'q': 'bc:"19365"'}, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

print('Final URL:', response.url)

# Look for availability-related elements
availability_divs = soup.find_all(['div', 'span', 'td'], string=lambda text: text and ('available' in text.lower() or 'checked' in text.lower()))
print(f'Found {len(availability_divs)} availability-related elements')

for i, elem in enumerate(availability_divs[:5]):  # Show first 5
    print(f'Element {i}: {elem.name} - "{elem.get_text(strip=True)}"')
    # Show parent context
    parent = elem.parent
    if parent:
        print(f'  Parent: {parent.name}, class: {parent.get("class")}')
        print(f'  Parent text: {parent.get_text(strip=True)[:100]}...')

# Look for table rows that might contain item information
table_rows = soup.find_all('tr')
print(f'Found {len(table_rows)} table rows')

for row in table_rows[:10]:  # Check first 10 rows
    cells = row.find_all(['td', 'th'])
    if cells and len(cells) >= 3:
        row_text = ' | '.join(cell.get_text(strip=True) for cell in cells)
        if 'available' in row_text.lower() or 'checked' in row_text.lower():
            print(f'Relevant row: {row_text}')