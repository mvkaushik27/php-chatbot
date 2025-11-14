import requests
from bs4 import BeautifulSoup

response = requests.get('https://opac.iitrpr.ac.in/cgi-bin/koha/opac-search.pl', params={'q': 'bc:"19365"'}, timeout=10)
print('URL:', response.url)
print('Is details page:', 'opac-detail.pl' in response.url)

soup = BeautifulSoup(response.content, 'html.parser')
table_rows = soup.find_all('tr')
print('Found table rows:', len(table_rows))

for i, row in enumerate(table_rows[:10]):
    cells = row.find_all(['td', 'th'])
    print(f'Row {i}: {len(cells)} cells')
    if len(cells) >= 3:
        row_text = [cell.get_text(strip=True) for cell in cells]
        print(f'  Cell texts: {row_text}')
        # Check for availability keywords
        has_available = any('Available' in cell for cell in row_text)
        has_checked_out = any('Checked out' in cell for cell in row_text)
        if has_available or has_checked_out:
            print(f'  *** AVAILABILITY ROW ***')