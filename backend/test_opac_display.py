import os
os.environ['NANDU_WEBSCRAPE'] = '1'
print('Testing OPAC integration without heavy model loading...')

# Test OPAC check directly
from nandu_brain import check_book_availability_opac

# Create a mock book result with OPAC data
mock_book = {
    'Title': 'Python Programming',
    'Author': 'Test Author',
    'ISBN': '1234567890',
    'opac_availability': {
        'status': 'not_found',
        'available_copies': 0,
        'total_copies': 0
    }
}

print('Mock book OPAC data:', mock_book.get('opac_availability'))

# Test the formatter
from formatters import render_book_card
html = render_book_card(mock_book)
if 'availability' in html:
    print('✅ Availability status found in rendered HTML')
    if 'unknown' in html:
        print('Status: unknown (book not found in OPAC)')
else:
    print('❌ No availability status in HTML')