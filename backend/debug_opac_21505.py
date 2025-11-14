import requests
from bs4 import BeautifulSoup

# Test the OPAC search for bc:21505
search_url = 'https://opac.iitrpr.ac.in/cgi-bin/koha/opac-search.pl'
params = {'q': 'bc:21505'}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Testing OPAC search for bc:21505...")
response = requests.get(search_url, params=params, headers=headers, timeout=10)
print('URL:', response.url)
print('Status:', response.status_code)

soup = BeautifulSoup(response.content, 'html.parser')

# Check if it's a details page
if 'opac-detail.pl' in response.url:
    print('DETAILS PAGE DETECTED')
    table_rows = soup.find_all('tr')
    print(f'Found {len(table_rows)} table rows')

    for i, row in enumerate(table_rows[:15]):  # First 15 rows
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 3:  # At least 3 cells
            row_text = [cell.get_text(strip=True) for cell in cells]
            print(f'Row {i}: {row_text}')
            if len(row_text) > 4:
                status_cell = row_text[4]
                print(f'  Status cell: "{status_cell}"')
else:
    print('SEARCH RESULTS PAGE')
    print('Page title:', soup.find('title').get_text() if soup.find('title') else 'No title')

    # Look for any mention of the book
    page_text = soup.get_text()
    if 'thermodynamics' in page_text.lower():
        print('Book title found in page text')
    else:
        print('Book title NOT found in page text')