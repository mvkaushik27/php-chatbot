# Exclusion Pattern Analysis Summary

## Overview
- **Total questions in general_queries.json:** 3,981
- **Questions matching exclusion patterns:** 978 (24.6%)
- **These queries should be processed as GENERAL queries, not book searches**

## Top Exclusion Patterns

### 1. "should i" - 494 matches
**Examples:**
- "why should i use the library"
- "when should i return books"  
- "whom should i contact for help"
- "what should i know about library timing"

### 2. "how to" - 281 matches
**Examples:**
- "how to access online journals"
- "how to issue book"
- "how to search books"
- "how to reserve a book"

### 3. "membership" - 74 matches
**Examples:**
- "how to get library membership"
- "membership rules"
- "library membership form"
- "external membership"

### 4. "where to" - 31 matches
**Examples:**
- "where to check new arrivals"
- "where to find library forms"
- "where to find phd theses"

### 5. "library service" - 23 matches
**Examples:**
- "library services"
- "library services list"
- "list all library services"

## Questions by Intent Category

| Intent | Count | Description |
|--------|-------|-------------|
| general | 371 | General library information |
| access | 105 | Access procedures and permissions |
| membership | 85 | Membership-related queries |
| borrowing | 80 | Book borrowing procedures |
| rules | 55 | Library rules and policies |
| service | 52 | Library services |
| resources | 46 | Library resources |
| search | 32 | Search procedures |
| plagiarism | 26 | Plagiarism checking |
| research | 25 | Research support |

## Key Personal Belongings Queries Fixed

### Before Fix: ❌ Incorrectly classified as BOOK queries
- "Do I have to make entry of my books and laptop?"
- "Can I bring own books and laptop?"
- "Do I have to make entry for issued book in register?"

### After Fix: ✅ Correctly classified as GENERAL queries
- These queries now properly go to general_queries.json lookup
- Users get accurate answers about library policies
- No confusion with catalogue book searches

## Impact

This exclusion pattern system ensures that:
1. **Library policy questions** get answered from general_queries.json
2. **Personal belongings questions** are handled correctly
3. **Procedural questions** don't trigger book searches
4. **Book search functionality** remains accurate for actual book queries

## Files Generated

1. **exclusion_pattern_queries.csv** - Spreadsheet format for analysis
2. **exclusion_pattern_queries.json** - Detailed JSON format
3. **export_exclusion_queries.py** - Analysis script

The exclusion patterns successfully prevent 978 general library queries from being misclassified as book searches!