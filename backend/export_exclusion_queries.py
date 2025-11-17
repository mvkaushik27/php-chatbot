#!/usr/bin/env python3
"""
Export queries from general_queries.json that match exclusion patterns
These are queries that should NOT be classified as book searches
"""

import json
import csv
from pathlib import Path

def main():
    # Load general queries
    general_queries_file = Path("general_queries.json")
    if not general_queries_file.exists():
        print("❌ general_queries.json not found!")
        return
    
    with open(general_queries_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Exclusion patterns - same as in nandu_brain.py
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
        
        # General library questions
        'how to', 'what to do', 'where to', 'when to', 'why to'
    ]
    
    # Find matching queries
    matching_queries = []
    
    for question, info in data.items():
        question_lower = question.lower()
        
        # Check if question matches any exclusion pattern
        for pattern in exclusion_patterns:
            if pattern in question_lower:
                matching_queries.append({
                    'question': question,
                    'intent': info.get('intent', 'unknown'),
                    'answer': info.get('answer', '')[:100] + '...' if len(info.get('answer', '')) > 100 else info.get('answer', ''),
                    'matched_pattern': pattern
                })
                break
    
    # Sort by matched pattern
    matching_queries.sort(key=lambda x: x['matched_pattern'])
    
    print(f"📊 EXCLUSION PATTERN ANALYSIS")
    print(f"{'='*50}")
    print(f"Total questions in general_queries.json: {len(data)}")
    print(f"Questions matching exclusion patterns: {len(matching_queries)}")
    print()
    
    # Group by pattern
    pattern_groups = {}
    for query in matching_queries:
        pattern = query['matched_pattern']
        if pattern not in pattern_groups:
            pattern_groups[pattern] = []
        pattern_groups[pattern].append(query)
    
    # Display results
    for pattern, queries in pattern_groups.items():
        print(f"🔍 Pattern: '{pattern}' ({len(queries)} matches)")
        print("-" * 60)
        for query in queries[:5]:  # Show first 5 examples
            print(f"   Question: {query['question']}")
            print(f"   Intent: {query['intent']}")
            print(f"   Answer: {query['answer']}")
            print()
        if len(queries) > 5:
            print(f"   ... and {len(queries) - 5} more questions")
        print()
    
    # Export to CSV
    csv_file = Path("exclusion_pattern_queries.csv")
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['question', 'intent', 'matched_pattern', 'answer'])
        writer.writeheader()
        for query in matching_queries:
            writer.writerow({
                'question': query['question'],
                'intent': query['intent'],
                'matched_pattern': query['matched_pattern'],
                'answer': query['answer']
            })
    
    print(f"✅ Exported {len(matching_queries)} queries to '{csv_file}'")
    
    # Export to JSON for detailed analysis
    json_file = Path("exclusion_pattern_queries.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(matching_queries, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported detailed data to '{json_file}'")
    
    # Summary statistics
    print(f"\n📈 SUMMARY STATISTICS:")
    print(f"{'='*50}")
    intent_counts = {}
    for query in matching_queries:
        intent = query['intent']
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    print("Questions by intent:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {intent}: {count} questions")
    
    print(f"\nTop exclusion patterns:")
    pattern_counts = {}
    for query in matching_queries:
        pattern = query['matched_pattern']
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   '{pattern}': {count} matches")

if __name__ == "__main__":
    main()