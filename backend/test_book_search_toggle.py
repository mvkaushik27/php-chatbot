#!/usr/bin/env python3
"""
Test Book Search Toggle Functionality
====================================
This script tests the new book search toggle feature.
"""

import os
import sys
sys.path.append('.')

from nandu_brain import get_nandu_response, _get_book_search_enabled, classify_query

def test_book_search_toggle():
    """Test the book search toggle functionality"""
    
    print("🧪 Testing Book Search Toggle Functionality")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "machine learning books",
        "books by einstein", 
        "physics textbooks",
        "library timing",
        "borrowing policy",
        "how to search books"
    ]
    
    print(f"\n📊 Current Configuration:")
    print(f"Book Search Enabled: {_get_book_search_enabled()}")
    print(f"NANDU_BOOK_SEARCH env var: {os.getenv('NANDU_BOOK_SEARCH', 'not set')}")
    
    print("\n🔍 Query Classification Tests:")
    for query in test_queries:
        classification = classify_query(query)
        print(f"'{query}' → {classification}")
    
    print("\n📚 Book Search ENABLED Test:")
    print("-" * 30)
    # Temporarily enable book search
    os.environ['NANDU_BOOK_SEARCH'] = '1'
    
    for query in test_queries[:3]:  # Only test book queries
        print(f"\nQuery: '{query}'")
        try:
            response = get_nandu_response(query)
            # Show first 100 characters of response
            print(f"Response: {response[:100]}...")
            if "Note:" in response and "disabled" in response:
                print("❌ UNEXPECTED: Book search disabled message shown when enabled")
            else:
                print("✅ Book search working as expected")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🚫 Book Search DISABLED Test:")
    print("-" * 30)
    # Disable book search
    os.environ['NANDU_BOOK_SEARCH'] = '0'
    
    for query in test_queries[:3]:  # Only test book queries
        print(f"\nQuery: '{query}'")
        try:
            response = get_nandu_response(query)
            # Show first 100 characters of response
            print(f"Response: {response[:100]}...")
            if "Note:" in response and "disabled" in response:
                print("✅ Book search disabled message shown correctly")
            else:
                print("⚠️ Book search disabled message not shown")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_book_search_toggle()