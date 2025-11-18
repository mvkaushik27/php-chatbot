#!/usr/bin/env python3
"""
Quick test to verify the book search toggle is working with the live API server
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_config_endpoint():
    """Test the config endpoint"""
    try:
        response = requests.get(f"{API_URL}/config")
        if response.status_code == 200:
            config = response.json()
            print("📊 API Server Configuration:")
            print(f"  Book Search Enabled: {config.get('book_search_enabled')}")
            print(f"  Webscrape Enabled: {config.get('webscrape_enabled')}")
            print(f"  Timestamp: {config.get('timestamp')}")
            return config.get('book_search_enabled')
        else:
            print(f"❌ Config endpoint failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Config endpoint error: {e}")
        return None

def test_book_query():
    """Test a book query with the live API server"""
    try:
        response = requests.post(f"{API_URL}/chat", json={
            "query": "python books"
        })
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '')  # API returns 'response' not 'answer'
            
            # Check if it's a book result or general result  
            # API returns JSON format for books: {"books": [...]}
            if answer.startswith('```json') and '"books":' in answer:
                return "book_result"
            elif 'Book catalogue search is currently disabled' in answer:
                return "disabled_message"
            else:
                return "general_result"
        else:
            print(f"❌ Chat failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return None

def main():
    print("🧪 Live API Server Book Search Toggle Test")
    print("=" * 50)
    
    # Test config endpoint
    book_search_enabled = test_config_endpoint()
    print()
    
    # Test actual query
    print("🔍 Testing query: 'python books'")
    result_type = test_book_query()
    
    if result_type:
        if result_type == "book_result":
            print("✅ API returned book search results")
            if book_search_enabled is False:
                print("❌ ISSUE: Book search disabled but still returning book results!")
            else:
                print("✅ Expected behavior - book search is enabled")
        elif result_type == "disabled_message":
            print("✅ API returned disabled message")
            if book_search_enabled is True:
                print("❌ ISSUE: Book search enabled but returning disabled message!")
            else:
                print("✅ Expected behavior - book search is disabled")
        elif result_type == "general_result":
            print("✅ API returned general information")
            if book_search_enabled is False:
                print("✅ Expected behavior - book search disabled, returning general info")
            else:
                print("❓ Unexpected - book search enabled but returned general info")
    
    print()
    if book_search_enabled is False and result_type == "book_result":
        print("🔄 SOLUTION: The API server needs to be restarted to pick up configuration changes.")
        print("   Please stop and restart the API server (python api_server.py)")

if __name__ == "__main__":
    main()