import requests
from bs4 import BeautifulSoup
import re

response = requests.get('https://opac.iitrpr.ac.in/cgi-bin/koha/opac-search.pl', params={'q': 'bc:"19365"'}, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

print('Title:', soup.find('title').get_text() if soup.find('title') else 'No title')
print('URL:', response.url)
print('Status:', response.status_code)

# Look for availability information
availability_text = soup.get_text()
print('Contains "available":', 'available' in availability_text.lower())
print('Contains "checked out":', 'checked out' in availability_text.lower())

# Look for specific availability patterns
available_match = re.search(r'Items available for loan:[^)]*\((\d+)\)', availability_text)
issued_match = re.search(r'Checked out\((\d+)\)', availability_text)

print('Available match:', available_match.group(1) if available_match else 'None')
print('Issued match:', issued_match.group(1) if issued_match else 'None')

# Show some content around availability
lines = availability_text.split('\n')
for i, line in enumerate(lines):
    if 'available' in line.lower() or 'checked out' in line.lower():
        print(f'Line {i}: {line.strip()}')