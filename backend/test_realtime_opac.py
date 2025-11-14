import os
os.environ['NANDU_WEBSCRAPE'] = '1'
from nandu_brain import check_book_availability_opac

print('🔍 Testing Real-Time OPAC Availability Checking')
print('=' * 50)

# Test with books that are likely in the IIT Ropar library
test_books = [
    {'title': 'Introduction to Algorithms', 'author': 'Cormen'},
    {'title': 'Computer Networks', 'author': 'Tanenbaum'},
    {'title': 'Operating System Concepts', 'author': 'Silberschatz'},
    {'title': 'python programming', 'author': 'Satyanarayana'}
]

for book in test_books:
    print(f'\n📚 Checking: "{book["title"]}" by {book["author"]}')
    print('-' * 40)

    result = check_book_availability_opac(**book)

    if result:
        status = result.get('status', 'unknown')
        available = result.get('available_copies', 0)
        total = result.get('total_copies', 0)
        results_count = result.get('total_results', 0)

        print(f'🔍 Search Results Found: {results_count}')
        print(f'📊 Status: {status.upper()}')
        print(f'📖 Available Copies: {available}/{total}')

        if result.get('details'):
            print('📋 Details:')
            for i, detail in enumerate(result['details'][:3]):  # Show first 3 details
                title = detail.get('title', 'N/A')[:50]  # Truncate long titles
                book_status = detail.get('status', 'N/A')
                print(f'   {i+1}. {title}... - {book_status}')

        # Interpret the status for user
        if status == 'available':
            print('✅ BOOK IS CURRENTLY AVAILABLE FOR BORROWING')
        elif status == 'issued':
            print('📖 BOOK IS CURRENTLY CHECKED OUT')
        elif status == 'not_found':
            print('❓ BOOK NOT FOUND IN LIBRARY CATALOG')
        else:
            print('❓ AVAILABILITY STATUS UNKNOWN')

    else:
        print('❌ OPAC CHECK FAILED - No result returned')

    print()

print('✅ Real-time OPAC availability checking test complete!')