#!/usr/bin/env python3
"""
Test how exclusion patterns work for specific queries
"""

def test_exclusion_patterns(query):
    query_lower = query.lower()
    
    print(f'Testing query: "{query}"')
    print(f'Query lowercase: "{query_lower}"')
    print()
    
    # Exclusion patterns from nandu_brain.py
    exclusion_patterns = [
        # Personal belongings and entry procedures
        'make entry', 'entry of', 'bring my', 'my books and laptop', 'personal books',
        'own books', 'entry portal', 'entry exit',
        
        # Library rules and procedures
        'do i have to', 'should i', 'can i bring', 'allowed to bring',
        'entry register', 'register entry',
        
        # Library services and policies
        'library rule', 'library policy', 'library service', 'library procedure',
        'fine policy', 'membership', 'card required', 'id card',
        
        # Vacation and borrowing policies
        'books for vacation', 'vacation books', 'books for summer', 'books for winter',
        'can i get books for', 'vacation period', 'holiday books', 'semester break',
        
        # Borrowing policy questions
        'can i issue', 'can i borrow', 'how many books can i', 'book limit',
        'borrowing limit', 'issue limit', 'renewal policy', 'due date',
        
        # General library questions
        'how to', 'what to do', 'where to', 'when to', 'why to'
    ]
    
    print('Checking exclusion patterns:')
    print('=' * 40)
    
    matches = []
    for pattern in exclusion_patterns:
        if pattern in query_lower:
            matches.append(pattern)
            print(f'✅ MATCH: "{pattern}"')
    
    if not matches:
        print('❌ No exclusion patterns matched')
        print('This query would be checked for BOOK SEARCH keywords')
    else:
        print()
        print(f'RESULT: Query matches {len(matches)} exclusion pattern(s)')
        print('🚫 This query will be EXCLUDED from book search classification')
        print('📋 It will be processed as a GENERAL QUERY instead')
        print()
        print('Processing flow:')
        print('1. ✅ Exclusion pattern matched -> Skip book classification')
        print('2. 🔍 Search in general_queries.json for semantic match')
        print('3. 💬 Return appropriate library policy answer')

# Test the specific query
if __name__ == "__main__":
    test_exclusion_patterns("should i need to make entry")
    print()
    print("=" * 60)
    print()
    test_exclusion_patterns("Do I have to make entry of my books and laptop")
    print()
    print("=" * 60)
    print()
    test_exclusion_patterns("Can I get books for vacations (Winter/Summer)?")
    print()
    print("=" * 60)
    print()
    test_exclusion_patterns("find machine learning books")