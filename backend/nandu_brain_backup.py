from typing import Dict, List, Optional, Tuple
"""
Nandu Brain - Nalanda Library Assistant Backend
------------------------------------------------
✅ Intelligent Query Classification via LLaMA (Groq API)
✅ Enhanced Local Rule-Based Fallback Classifier
✅ Auto Spelling Correction
✅ Hybrid Search (Catalogue + FAISS)
✅ General Inquiries (JSON)
✅ Web Scraping from Official Library Website
✅ OPAC Fallback
✅ Professional Response Formatting
✅ Comprehensive Error Handling & Logging
✅ Works Offline When Groq API Unavailable
✅ Rate Limiting & Security Hardening
"""

import os
import sys
import sqlite3
import json
import pickle
import logging
import requests
import re
import time
import warnings
import io
import contextlib
from pathlib import Path
from difflib import get_close_matches
from dotenv import load_dotenv
from formatters import format_results
from collections import defaultdict, Counter
import string
from functools import lru_cache, wraps  # ⚡ Add LRU cache for speed + decorators
from datetime import datetime

# Reduce noisy logs from third-party libraries early
os.environ.setdefault("TORCH_CPP_LOG_LEVEL", "ERROR")  # Silence PyTorch C++ logs
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")  # Avoid parallel tokenizer warnings

# Suppress noisy PyTorch warnings during model loading
warnings.filterwarnings('ignore', message='Examining the path of torch.classes')
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')
warnings.filterwarnings('ignore', category=UserWarning, module='torch')

# For web scraping
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None  # type: ignore
    logging.warning("BeautifulSoup4 not available - web scraping disabled")

# Optional: TextBlob for spelling correction
try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    TextBlob = None  # type: ignore
    
# Optional: Groq for LLaMA
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    Groq = None  # type: ignore

# Configure logging
logger = logging.getLogger(__name__)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# Install stderr silencer to drop specific noisy lines that bypass Python warnings/logging
class _StderrSilencer:
    def __init__(self, stream, patterns):
        self._stream = stream
        self._patterns = tuple(patterns)
    def write(self, s):
        try:
            if any(p in s for p in self._patterns):
                # Drop the line silently
                return len(s)
        except Exception:
            # On any error, fall back to original stream
            pass
        return self._stream.write(s)
    def flush(self):
        try:
            return self._stream.flush()
        except Exception:
            pass

try:
    sys.stderr = _StderrSilencer(sys.stderr, [
        "Examining the path of torch.classes",
        "Tried to instantiate class '__path__._path'",
        "Ensure that it is registered via torch::class_",
    ])
except Exception:
    # Non-fatal: if we cannot install the silencer, continue normally
    pass

# -------------------- RUNTIME TUNABLES (with safe defaults for Spaces) --------------------
# Groq LLaMA classification for better accuracy (adds ~1-2s latency per query)
# ⚠️ DISABLED until valid API key is set in HF Spaces secrets
NANDU_USE_GROQ = os.getenv("NANDU_USE_GROQ", "0") == "1"  # Set to "0" until API key configured
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "2"))  # Reduced to 2s for faster failure

# Disable website scraping by default (avoid slow network calls on Spaces)
NANDU_WEBSCRAPE = os.getenv("NANDU_WEBSCRAPE", "0") == "1"

# Use keyword fallback classification (fast, accurate for most queries)
FORCE_FALLBACK_CLASSIFICATION = os.getenv("FORCE_FALLBACK_CLASSIFICATION", "1") == "1"  # Set to "1" for now

# Initialize Groq client
groq_client = None
if HAS_GROQ and Groq is not None and GROQ_API_KEY and NANDU_USE_GROQ:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("✅ Groq client initialized successfully (key present: True, enabled via NANDU_USE_GROQ: True)")
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client: {e}")
else:
    # Emit a single concise status line about Groq availability without exposing secrets
    # We intentionally do NOT log the key itself, only its presence (boolean) and whether usage is enabled.
    logger.info(
        "ℹ️ Groq status | has_library: %s | key_present: %s | NANDU_USE_GROQ=%s | FORCE_FALLBACK_CLASSIFICATION=%s" % (
            HAS_GROQ,
            bool(GROQ_API_KEY),
            NANDU_USE_GROQ,
            FORCE_FALLBACK_CLASSIFICATION,
        )
    )

# -------------------- SMART CLASSIFICATION CACHE --------------------
# Cache classification results to minimize API calls (2 hours TTL)
CLASSIFICATION_CACHE_TTL = 7200  # ⚡ Increased from 1 hour to 2 hours
classification_cache = {}  # {normalized_query: (classification, timestamp)}

def get_cached_classification(query):
    """Get cached classification if still valid"""
    query_key = query.lower().strip()
    if query_key in classification_cache:
        classification, timestamp = classification_cache[query_key]
        if time.time() - timestamp < CLASSIFICATION_CACHE_TTL:
            logger.info(f"⚡ Cache hit for classification: '{query[:50]}...' → {classification}")
            return classification
        else:
            # Expired - remove from cache
            del classification_cache[query_key]
    return None

def cache_classification(query, classification):
    """Add classification to cache with timestamp"""
    query_key = query.lower().strip()
    classification_cache[query_key] = (classification, time.time())
    
    # ⚡ Cleanup old cache entries if size exceeds limit (500 entries)
    if len(classification_cache) > 500:
        # Remove 100 oldest entries
        sorted_cache = sorted(classification_cache.items(), key=lambda x: x[1][1])
        for key, _ in sorted_cache[:100]:
            del classification_cache[key]
        logger.info(f"🧹 Cleaned up classification cache (removed 100 oldest entries)")

# -------------------- SECURITY: RATE LIMITING --------------------
_rate_limiter = defaultdict(list)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # window in seconds

def rate_limit(max_requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW):
    """
    Rate limiter decorator - prevents abuse by limiting requests per client.
    
    Args:
        max_requests: Maximum requests allowed within window
        window: Time window in seconds
    
    Returns:
        Decorator function that enforces rate limiting
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get client identifier (use 'default' if not provided)
            client_id = kwargs.get('client_ip', 'default')
            current_time = time.time()
            
            # Clean old timestamps outside window
            _rate_limiter[client_id] = [
                ts for ts in _rate_limiter[client_id]
                if current_time - ts < window
            ]
            
            # Check if limit exceeded
            if len(_rate_limiter[client_id]) >= max_requests:
                logger.warning(f"⚠️ Rate limit exceeded for client: {client_id}")
                return {
                    "error": "rate_limit_exceeded",
                    "message": f"⚠️ **Too many requests.** Please wait {window} seconds and try again.",
                    "retry_after": window
                }
            
            # Add current timestamp
            _rate_limiter[client_id].append(current_time)
            
            # Call original function
            return func(*args, **kwargs)
        return wrapper
    return decorator

# -------------------- SECURITY: AUDIT LOGGING --------------------
_error_tracker = {
    "count": 0,
    "last_reset": time.time(),
    "recent_errors": []
}

def audit_log_query(query: str, response: str, client_ip: str, processing_time: float, success: bool = True):
    """
    Log queries for security audit and analytics (GDPR-compliant).
    Stores anonymized query logs for troubleshooting and abuse detection.
    
    Args:
        query: User query (truncated to 100 chars for privacy)
        response: Response text (length only, not content)
        client_ip: Client IP (anonymized - first 10 chars only)
        processing_time: Time taken to process in seconds
        success: Whether query succeeded
    """
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query[:100],  # Truncate for privacy
            "response_length": len(str(response)),
            "client_ip": client_ip[:10] + "***" if client_ip != "default" else "default",  # Anonymize
            "processing_time_ms": round(processing_time * 1000, 2),
            "success": success
        }
        
        # Append to JSONL audit log (create logs directory if needed)
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(exist_ok=True)
        
        audit_file = log_dir / "query_audit.jsonl"
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
            
    except Exception as e:
        # Don't fail query if audit logging fails
        logger.debug(f"Audit logging failed: {e}")

def track_error(error: Exception, context: str):
    """
    Track errors and alert if threshold exceeded.
    Helps detect system issues or attacks.
    
    Args:
        error: Exception that occurred
        context: Context where error happened (function name, etc.)
    """
    _error_tracker["count"] += 1
    _error_tracker["recent_errors"].append({
        "error": str(error),
        "context": context,
        "timestamp": time.time()
    })
    
    # Keep only last 10 errors
    _error_tracker["recent_errors"] = _error_tracker["recent_errors"][-10:]
    
    # Reset counter every hour
    if time.time() - _error_tracker["last_reset"] > 3600:
        _error_tracker["count"] = 0
        _error_tracker["last_reset"] = time.time()
    
    # Alert if >50 errors/hour (indicates system issue or attack)
    if _error_tracker["count"] > 50:
        logger.critical(f"🚨 HIGH ERROR RATE: {_error_tracker['count']} errors in last hour. Recent: {_error_tracker['recent_errors'][-3:]}")

# -------------------- MONITORING: HEALTH CHECK --------------------
def health_check() -> dict:
    """
    Check system health for monitoring/alerting.
    Returns status of critical components.
    
    Returns:
        dict with 'status' (healthy/degraded/unhealthy) and component checks
    """
    checks = {
        "database": False,
        "faiss_index": False,
        "general_queries": False,
        "groq_client": False
    }
    
    try:
        # Check database
        if CATALOGUE_DB.exists():
            with sqlite3.connect(CATALOGUE_DB, timeout=5.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM catalogue")
                count = cursor.fetchone()[0]
                checks["database"] = count > 0
        
        # Check FAISS index
        checks["faiss_index"] = INDEX_FILE.exists() and MAPPING_FILE.exists()
        
        # Check general queries
        if GENERAL_QUERIES.exists():
            with open(GENERAL_QUERIES, 'r') as f:
                data = json.load(f)
                checks["general_queries"] = len(data) > 0
        
        # Check Groq client
        checks["groq_client"] = groq_client is not None
        
        # Determine overall status
        critical_checks = [checks["database"], checks["general_queries"]]
        if all(critical_checks):
            status = "healthy"
        elif any(critical_checks):
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
            "error_count_last_hour": _error_tracker["count"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        track_error(e, "health_check")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


    # ⚡ Increased cache size from 200 to 500 entries (better hit rate)
    if len(classification_cache) > 500:
        sorted_cache = sorted(classification_cache.items(), key=lambda x: x[1][1])
        for key, _ in sorted_cache[:100]:  # Remove oldest 100
            del classification_cache[key]
    
    logger.debug(f"📦 Cached classification: '{query[:50]}...' → {classification}")

# Paths
BASE_DIR = Path(__file__).parent

# ========================
# OPTIMIZATION: INPUT SANITIZATION
# ========================
@lru_cache(maxsize=500)
def sanitize_input(query: str) -> str:
    """
    Sanitize user input to prevent injection attacks and normalize query
    
    Args:
        query: Raw user input
    
    Returns:
        Sanitized query (max 300 chars, alphanumeric + spaces only)
    """
    if not query or not isinstance(query, str):
        return ""
    
    # Remove control characters and dangerous symbols
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)
    
    # Keep only alphanumeric, spaces, and basic punctuation
    query = re.sub(r'[^a-zA-Z0-9\s\-\.,?!\']', '', query)
    
    # Normalize whitespace
    query = ' '.join(query.split())
    
    # Limit length to prevent DoS
    query = query[:300]
    
    return query.strip()


@lru_cache(maxsize=500)
def is_valid_query(query: str) -> tuple[bool, str]:
    """
    Validate if query is meaningful or just gibberish
    
    Returns:
        (is_valid, error_message) tuple
    """
    if not query or len(query.strip()) < 2:
        return False, "⚠️ Please enter a valid query with at least 2 characters."
    
    # Check if query has at least some vowels (basic gibberish detection)
    vowels = set('aeiouAEIOU')
    consonants = set('bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ')
    
    has_vowels = any(c in vowels for c in query)
    has_consonants = any(c in consonants for c in query)
    
    # If only consonants or very few vowels, likely gibberish
    letter_count = sum(1 for c in query if c.isalpha())
    vowel_count = sum(1 for c in query if c in vowels)
    
    if letter_count > 5 and vowel_count < letter_count * 0.15:  # Less than 15% vowels
        return False, "⚠️ I couldn't understand your query. Please enter a valid question about books, authors, or library services."
    
    # Check for repeated characters (like "aaaaaaa" or "dkdkdkdk")
    if len(query) > 4:
        # Check for excessive repetition
        for i in range(len(query) - 3):
            pattern = query[i:i+2]
            if query.count(pattern) > len(query) / 4:  # Pattern repeats too much
                return False, "⚠️ I couldn't understand your query. Please enter a valid question about books, authors, or library services."
    
    return True, ""


# Note: Caching is now handled in nandu_streamlit_ui.py via st.session_state
# This avoids duplication and leverages Streamlit's session management


CATALOGUE_DB = BASE_DIR / "catalogue.db"
GENERAL_QUERIES = BASE_DIR / "general_queries.json"
INDEX_FILE = BASE_DIR / "catalogue_index.faiss"
MAPPING_FILE = BASE_DIR / "catalogue_mapping.pkl"

# FAISS indices for general queries (semantic search)
GENERAL_QUERIES_INDEX_FILE = BASE_DIR / "general_queries_index.faiss"
GENERAL_QUERIES_MAPPING_FILE = BASE_DIR / "general_queries_mapping.pkl"

# -------------------------
# Utility Functions
# -------------------------
@lru_cache(maxsize=1000)  # ⚡ Cache spelling corrections
def auto_correct_spelling(query):
    """
    Auto-correct spelling errors using TextBlob (cached).
    Preserves common library terms and known author-name tokens to avoid over-correction.
    """
    if not HAS_TEXTBLOB or TextBlob is None or not query:
        return query

    # Lazy-load and cache a lexicon of author tokens from the catalogue
    import string

    @lru_cache(maxsize=1)
    def _author_token_lexicon() -> set:
        try:
            tokens = set()
            if CATALOGUE_DB.exists():
                conn = sqlite3.connect(str(CATALOGUE_DB))
                cur = conn.cursor()
                cur.execute("SELECT DISTINCT author FROM catalogue WHERE author IS NOT NULL")
                rows = cur.fetchall()
                conn.close()
                punct_table = str.maketrans('', '', string.punctuation)
                for (author,) in rows:
                    if not author:
                        continue
                    # split on whitespace and commas, strip punctuation, lowercase
                    for tok in str(author).replace('|', ' ').replace('/', ' ').split():
                        tok = tok.translate(punct_table).strip().lower()
                        if tok and tok.isalpha():
                            tokens.add(tok)
            return tokens
        except Exception:
            return set()

    try:
        # Don't correct common library terms
        preserve_words = ['timings', 'ebooks', 'eresources', 'opac', 'scopus',
                          'webopac', 'vpn', 'wifi', 'technobooth', 'grammarly',
                          'turnitin', 'mendeley', 'zotero', 'jstor',
                          'phd', 'pg', 'ug', 'btech', 'mtech', 'msc', 'bsc',
                          'iit', 'ropar', 'isbn', 'doi', 'issn']

        # Check if query contains preserve_words (check whole words to avoid partial matches)
        query_lower = query.lower()
        query_words = query_lower.split()
        for word in preserve_words:
            if word in query_words:
                logger.debug(f"Preserving common acronym/term '{word}', skipping correction")
                return query

        # If query contains known author tokens, avoid altering those tokens
        author_tokens = _author_token_lexicon()

        blob = TextBlob(query)
        corrected = str(blob.correct())

        # Only apply correction if it's a meaningful change (not over-correction)
        if corrected.lower() != query.lower():
            # Heuristic 1: similar overall length
            length_ok = abs(len(corrected) - len(query)) <= 3

            # Heuristic 2: do not remove known author tokens (e.g., 'chetan', 'bhagat')
            orig_tokens = set(re.findall(r"[A-Za-z']+", query_lower))
            corr_tokens = set(re.findall(r"[A-Za-z']+", corrected.lower()))
            protected = {t for t in orig_tokens if t in author_tokens}
            author_tokens_preserved = protected.issubset(corr_tokens)

            if length_ok and author_tokens_preserved:
                logger.info(f"📝 Auto-corrected: '{query}' → '{corrected}'")
                return corrected
            else:
                logger.debug(
                    "Skipping autocorrect due to safety checks | length_ok=%s, protected=%s",
                    length_ok,
                    ",".join(sorted(protected)) if protected else "-"
                )

        # Default: return original
        return query
    except Exception as e:
        logger.warning(f"Spelling correction failed: {e}")
        return query

def fetch_website_content(url="https://www.iitrpr.ac.in/library/", cache_timeout=3600):
    """
    Fetch and cache content from the official IIT Ropar library website.
    
    Args:
        url (str): Library website URL
        cache_timeout (int): Cache validity in seconds (default 1 hour)
        
    Returns:
        dict: Extracted website data including sections, links, and text content
    """
    # Respect runtime setting to avoid network calls unless explicitly enabled
    if not NANDU_WEBSCRAPE:
        logger.info("🌐 Website fetch disabled (NANDU_WEBSCRAPE=0)")
        return None

    if not HAS_BS4:
        logger.warning("BeautifulSoup4 not installed - cannot fetch website content")
        return None
    
    cache_file = Path("cache/website_cache.json")
    cache_file.parent.mkdir(exist_ok=True)
    
    try:
        # Check if cache exists and is valid
        if cache_file.exists():
            import time
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < cache_timeout:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    logger.info(f"✅ Using cached website content (age: {cache_age:.0f}s)")
                    return cached_data
        
        # Fetch fresh content
        logger.info(f"🌐 Fetching content from {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        if not HAS_BS4 or BeautifulSoup is None:
            logger.warning("BeautifulSoup4 unavailable after check - skipping website parse")
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract useful information
        website_data = {
            "url": url,
            "title": soup.title.string if soup.title else "IIT Ropar Library",
            "sections": [],
            "links": [],
            "contact": {},
            "text_content": []
        }
        
        # Extract main content sections
        for section in soup.find_all(['section', 'div'], class_=re.compile(r'content|section|main', re.I)):
            section_text = section.get_text(strip=True, separator=' ')
            if section_text and len(section_text) > 50:
                website_data["text_content"].append(section_text[:500])
        
        # Extract important links
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            link_href = getattr(link, 'get', lambda *a, **k: None)('href', None)
            if link_text and len(link_text) > 3 and isinstance(link_href, str):
                # Convert relative URLs to absolute
                if link_href.startswith('/'):
                    link_href = f"https://www.iitrpr.ac.in{link_href}"
                website_data["links"].append({
                    "text": link_text,
                    "url": link_href
                })
        
        # Extract contact information
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b'
        
        page_text = soup.get_text()
        emails = re.findall(email_pattern, page_text)
        phones = re.findall(phone_pattern, page_text)
        
        if emails:
            website_data["contact"]["emails"] = list(set(emails))[:3]  # First 3 unique
        if phones:
            website_data["contact"]["phones"] = list(set(phones))[:3]
        
        # Extract headings for sections
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if heading_text and len(heading_text) > 5:
                website_data["sections"].append(heading_text)
        
        # Cache the results
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(website_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Fetched and cached website content: {len(website_data['sections'])} sections, {len(website_data['links'])} links")
        return website_data
        
    except requests.RequestException as e:
        logger.error(f"❌ Failed to fetch website: {e}")
        # Try to use stale cache if available
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                logger.info("⚠️ Using stale cached data due to fetch error")
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"❌ Error processing website content: {e}")
        return None

def search_website_content(query, website_data):
    """
    Search through cached website content for relevant information.
    
    Args:
        query (str): User's search query
        website_data (dict): Cached website content
        
    Returns:
        dict: Relevant information found on website, or None
    """
    if not website_data:
        return None
    
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Search in sections
    relevant_sections = []
    for section in website_data.get("sections", []):
        if any(word in section.lower() for word in query_words):
            relevant_sections.append(section)
    
    # Search in links
    relevant_links = []
    for link in website_data.get("links", []):
        if any(word in link["text"].lower() for word in query_words):
            relevant_links.append(link)
    
    # Search in text content
    relevant_text = []
    for text in website_data.get("text_content", []):
        if any(word in text.lower() for word in query_words):
            relevant_text.append(text)
    
    if relevant_sections or relevant_links or relevant_text:
        result = {
            "intent": "website_info",
            "answer": "📌 **Information from IIT Ropar Library Website:**\n\n"
        }
        
        if relevant_sections:
            result["answer"] += "**Relevant Sections:**\n"
            for section in relevant_sections[:3]:
                result["answer"] += f"• {section}\n"
            result["answer"] += "\n"
        
        if relevant_text:
            result["answer"] += "**Details:**\n"
            result["answer"] += f"{relevant_text[0][:300]}...\n\n"
        
        if relevant_links:
            result["answer"] += "**Related Links:**\n"
            for link in relevant_links[:3]:
                result["answer"] += f"• [{link['text']}]({link['url']})\n"
        
        result["answer"] += f"\n🔗 [Visit Official Library Website]({website_data['url']})"
        
        logger.info(f"✅ Found website content matching '{query}'")
        return result
    
    return None

def classify_query_with_llama(query):
    """
    Use LLaMA (via Groq API) to intelligently classify whether a query is a 'book' or 'general' query.
    Falls back to keyword-based classification if Groq is unavailable.
    
    PERFORMANCE: Skip Groq by default for 10x faster response time (fallback is very accurate).
    
    Returns:
        str: 'book' or 'general'
    """
    # Check cache first
    cached = get_cached_classification(query)
    if cached:
        return cached
    
    # PERFORMANCE: Use fast fallback by default (Groq adds 1-2s latency)
    if FORCE_FALLBACK_CLASSIFICATION or not groq_client:
        if FORCE_FALLBACK_CLASSIFICATION:
            logger.debug("⚡ Using fast fallback classification (FORCE_FALLBACK_CLASSIFICATION=1)")
        else:
            logger.info("⚠️ Groq API not available, using fallback keyword-based classification")
        result = classify_query_fallback(query)
        cache_classification(query, result)
        return result
    
    try:
        classification_prompt = f"""You are a library assistant AI that classifies user queries. Analyze the query and classify it as either 'book' or 'general'.

**Classification Rules:**

CLASSIFY AS 'book' when:
- User wants to search for/find a specific book or books
- Looking for books on a topic/subject (e.g., "machine learning books", "chemistry textbooks")
- Searching by author name (e.g., "books by Stephen Hawking")
- Looking for ISBN, call numbers, or accession numbers
- Wants to know if a specific book is available
- Examples: "find python books", "books on AI", "organic chemistry textbook", "author: tolkien"

CLASSIFY AS 'general' when:
- Asking about library policies, rules, services, or procedures
- Questions about library hours, timings, location, or contact info
- Asking about borrowing limits, loan duration, or how many books they can borrow
- Questions about membership, registration, fines, penalties, or renewals
- Asking about library facilities, resources, or services (e.g., printing, wifi, study rooms)
- Questions about e-resources, databases, or digital access (e.g., "online journals", "e-journals", "how to access databases")
- Questions about accessing online materials (NOT searching for physical books)
- Any information request about the library itself (NOT searching for books)
- Examples: "library hours", "how to get membership", "how many books can I borrow", "fine policy", "e-journals access", "how to access online journals", "digital resources"

Query to classify: "{query}"

Respond with ONLY ONE WORD: 'book' OR 'general'"""

        api_start = time.time()
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert library query classifier. You must respond with exactly one word: 'book' or 'general'."},
                {"role": "user", "content": classification_prompt}
            ],
            max_tokens=10,
            temperature=0.0,  # Set to 0 for deterministic classification
            timeout=GROQ_TIMEOUT  # fast-fail per env
        )
        api_elapsed = time.time() - api_start
        logger.info(f"⏱️ Classification API took {api_elapsed:.2f}s")
        
        response = (completion.choices[0].message.content or "").strip().lower()
        
        # Parse response
        if 'book' in response:
            logger.info(f"🤖 LLaMA classified '{query}' as BOOK QUERY")
            cache_classification(query, 'book')
            return 'book'
        elif 'general' in response:
            logger.info(f"🤖 LLaMA classified '{query}' as GENERAL QUERY")
            cache_classification(query, 'general')
            return 'general'
        else:
            logger.warning(f"⚠️ Unclear LLaMA response: '{response}', using fallback")
            result = classify_query_fallback(query)
            cache_classification(query, result)
            return result
            
    except Exception as e:
        logger.error(f"❌ Error in LLaMA classification: {e}, using fallback")
        result = classify_query_fallback(query)
        cache_classification(query, result)
        return result

def enhance_query_with_llama(query, query_type):
    """
    Use LLaMA to enhance/expand user queries for better search results.
    Only called for book queries to generate better search terms.
    
    Args:
        query: User's original query
        query_type: 'book' or 'general'
    
    Returns:
        dict: {'original': query, 'enhanced': enhanced_query, 'keywords': [list]}
    """
    if query_type != 'book' or not groq_client:
        return {'original': query, 'enhanced': query, 'keywords': []}
    
    try:
        enhancement_prompt = f"""You are a library search assistant. Analyze this book search query and extract key search terms.

User query: "{query}"

Task:
1. Identify the main topic/subject
2. Extract author names if mentioned
3. Generate 3-5 relevant keywords for better search
4. Remove filler words (like "I want", "looking for", "need")

Respond in JSON format:
{{
    "main_topic": "core subject",
    "author": "author name or null",
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a library search optimization assistant. Respond only with valid JSON."},
                {"role": "user", "content": enhancement_prompt}
            ],
            max_tokens=150,
            temperature=0.3,
            timeout=max(1.0, GROQ_TIMEOUT)
        )
        
        response_text = (completion.choices[0].message.content or "").strip()
        
        # Parse JSON response
        import json
        try:
            parsed = json.loads(response_text)
            enhanced_query = parsed.get('main_topic', query)
            keywords = parsed.get('keywords', [])
            
            logger.info(f"🔍 LLaMA enhanced query: '{query}' → '{enhanced_query}' + {keywords}")
            return {
                'original': query,
                'enhanced': enhanced_query,
                'keywords': keywords,
                'author': parsed.get('author')
            }
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Failed to parse LLaMA enhancement response")
            return {'original': query, 'enhanced': query, 'keywords': []}
            
    except Exception as e:
        logger.error(f"❌ Error in LLaMA query enhancement: {e}")
        return {'original': query, 'enhanced': query, 'keywords': []}

@lru_cache(maxsize=500)
def classify_query_fallback(query):
    """
    Fallback keyword-based classification when Groq/LLaMA is unavailable.
    Streamlined for performance.
    
    Returns:
        str: 'book' or 'general'
    """
    query_lower = query.lower().strip()
    
    # ISBN pattern
    if re.search(r'\b(?:\d{9}[\dX]|\d{13})\b', query_lower):
        logger.info(f"📚 Fallback: BOOK (ISBN)")
        return 'book'
    
    # General keywords (library services, policies, facilities)
    general_keywords = [
        'timing', 'hours', 'open', 'close', 'schedule',
        'policy', 'rules', 'regulation', 'membership', 'register',
        'wifi', 'printer', 'facility', 'service', 'reading room',
        'fine', 'penalty', 'overdue', 'charges',
        'ebook', 'e-book', 'database', 'e-journal', 'vpn',
        'how to issue', 'how to return', 'how to borrow', 'how to renew',
        'grammarly', 'turnitin', 'scopus', 'mendeley',
        'librarian', 'staff', 'helpdesk', 'contact',
        'borrow limit', 'issue limit', 'borrowing limit',
        'technobooth',  # Technology resources facility
        # Student/faculty queries about privileges
        'student', 'students', 'faculty', 'phd', 'pg', 'ug', 'mtech', 'btech',
        'how many books', 'can i borrow', 'can i issue', 'allowed to borrow'
    ]
    
    # Priority check for e-resources/journals (must check BEFORE book keywords)
    eresource_patterns = [
        'online journal', 'e-journal', 'ejournals', 'e-journals',
        'digital journal', 'electronic journal', 'journal access',
        'how to access journal', 'access online', 'access e-',
        'online resource', 'digital resource', 'e-resource',
        'online database', 'digital database', 'remote access'
    ]
    
    if any(pattern in query_lower for pattern in eresource_patterns):
        logger.info(f"📋 Fallback: GENERAL (e-resources/journals query)")
        return 'general'
    
    if any(kw in query_lower for kw in general_keywords):
        logger.info(f"📋 Fallback: GENERAL")
        return 'general'
    
    # Instructional 'how to search/find' queries should be GENERAL (give guidance, not book results)
    instructional_patterns = [
        r"\bhow (to|do i|can i)\s+(search|find)\b",
        r"\bhow to use (opac|catalogue|catalog)\b",
        r"\bhow do i use (opac|catalogue|catalog)\b",
        r"\bguide\b.*\b(search|find)\b",
    ]
    if any(re.search(p, query_lower) for p in instructional_patterns):
        logger.info("📋 Fallback: GENERAL (instructional search guidance)")
        return 'general'
    
    # Enhanced book detection keywords
    book_keywords = [
        # Direct book references
        'book', 'books', 'textbook', 'textbooks', 'reference book',
        
        # Author searches
        'author', 'written by', 'book by', 'books by', 'author:', 'by author',
        
        # Title and edition
        'title', 'edition', 'volume', 'vol', 'publication', 'published',
        
        # ISBN and catalog
        'isbn', 'call number', 'accession', 'accession number',
        'catalogue', 'catalog', 'classification',
        
        # Book properties
        'publisher', 'cover', 'hardcover', 'paperback', 'binding',
        
        # Search and find
        'find book', 'search book', 'looking for book', 'need book',
        'find books', 'search books', 'show me books',
        
        # Subject-specific
        'book on', 'books on', 'book about', 'books about',
        'textbook on', 'reference on',
        
        # Specific phrases
        'available book', 'book available', 'in library',
        'library book', 'library books'
    ]
    
    # Check if it matches book keywords
    for keyword in book_keywords:
        if keyword in query_lower:
            logger.info(f"Fallback classified '{query}' as BOOK QUERY (keyword: '{keyword}')")
            return 'book'
    
    # Check for explicit book indicators (phrases that strongly suggest book search)
    book_indicators = [
        'book by', 'books by', 'author', 'written by',
        'isbn', 'call number', 'accession',
        'edition', 'publication', 'publisher',
        'textbook on', 'reference on', 'find book', 'search book'
    ]
    
    for indicator in book_indicators:
        if indicator in query_lower:
            logger.info(f"📚 Fallback classified '{query}' as BOOK QUERY (indicator: '{indicator}')")
            return 'book'
    
    # Check for subject/topic patterns (likely book searches)
    # e.g., "machine learning", "organic chemistry", "data structures"
    subject_patterns = [
        r'\b(physics|chemistry|biology|mathematics|math)\b',
        r'\b(computer|programming|coding|algorithm|data)\b',
        r'\b(engineering|mechanical|electrical|civil)\b',
        r'\b(history|geography|economics|sociology)\b',
        r'\b(novel|fiction|literature|poetry|drama)\b',
        r'\b(psychology|philosophy|anthropology)\b'
    ]
    
    for pattern in subject_patterns:
        if re.search(pattern, query_lower):
            logger.info(f"📚 Fallback classified '{query}' as BOOK QUERY (subject pattern matched)")
            return 'book'
    
    # If query is very short (1-2 words) and contains no general keywords, likely a book search
    words = query_lower.split()
    if len(words) <= 3 and not any(kw in query_lower for kw in general_keywords):
        logger.info(f"📚 Fallback classified '{query}' as BOOK QUERY (short query, likely topic search)")
        return 'book'
    
    # Default: treat as book search (most common use case)
    logger.info(f"📚 Fallback classified '{query}' as BOOK QUERY (default)")
    return 'book'

def merge_duplicates(results):
    """
    Merge book records strictly when they refer to the exact same book per rules:
    - Merge only if BOTH title and author refer to the same book (with minor author variations allowed like initials)
    - Never merge different authors, even if the title is identical
    - Combine copies/accessions/call numbers; keep publisher/year variations inside the same record

    Args:
        results (list): List of book records (dicts)

    Returns:
        list: Consolidated list with merged entries
    """
    if not results:
        logger.debug("No results to merge")
        return []

    import string
    from collections import defaultdict, Counter

    def normalize_title(s: str) -> str:
        s = (s or "").strip().lower()
        # remove extra spaces and basic punctuation
        table = str.maketrans('', '', string.punctuation)
        s = s.translate(table)
        s = ' '.join(s.split())
        return s

    def canonical_author_key(author_raw: str) -> str:
        """Create an author key like 'lastname|firstinitial'. If not parseable, fall back to normalized string.
        Handles forms: 'First Last', 'Last, First', 'C. Last', 'Last, C.' and ignores extra middle names.
        For multiple authors separated by '|' or ';', use the first author only for grouping.
        """
        a = (author_raw or "").strip()
        if not a:
            return ""
        # pick primary author if multiple
        primary = a.split('|')[0].split(';')[0].strip()

        # Normalize whitespace and punctuation
        table = str.maketrans('', '', string.punctuation.replace("'", ""))
        p = primary.translate(table)
        parts = [t for t in p.split() if t]
        if not parts:
            return ""

        # Try "Last, First" format
        if ',' in primary:
            last = primary.split(',')[0].strip().lower()
            after = primary.split(',')[1].strip()
            first_initial = after[0].lower() if after else ''
            return f"{last}|{first_initial}"

        # Else assume "First Middle Last" or initials then last
        last = parts[-1].lower()
        first = parts[0]
        first_initial = first[0].lower() if first else ''
        return f"{last}|{first_initial}"

    groups: dict[tuple[str, str], dict] = {}
    editions_map: dict[tuple[str, str], set[tuple]] = defaultdict(set)

    for item in results:
        try:
            title = str(item.get("Title", item.get("title", ""))).strip()
            author = str(item.get("Author", item.get("author", ""))).strip()
            isbn = str(item.get("ISBN", item.get("isbn", ""))).strip()
            accession = str(item.get("Barcode", item.get("barcode", ""))).strip()
            call_no = str(item.get("Call No", item.get("itemcallnumber", ""))).strip()
            publisher = item.get("Publisher", item.get("publishercode", ""))
            year = item.get("Year", item.get("copyrightdate", ""))

            if not title:
                logger.warning(f"Skipping item without title: {item}")
                continue

            title_key = normalize_title(title)
            author_key = canonical_author_key(author)

            # Strict rule: do not merge if author missing vs present; keep separate entries
            key = (title_key, author_key)

            if key not in groups:
                groups[key] = {
                    "Title": title,
                    "Author": author,
                    "ISBN": isbn,
                    "Publisher": publisher,
                    "Year": year,
                    "copies": 0,
                    "accessions": [],
                    "call_numbers": [],
                    "editions": []  # list of {Publisher, Year}
                }

            g = groups[key]
            g["copies"] += 1
            if accession and accession not in g["accessions"]:
                g["accessions"].append(accession)
            if call_no and call_no not in g["call_numbers"]:
                g["call_numbers"].append(call_no)

            # Track editions per group (publisher/year combos)
            editions_map[key].add((str(publisher).strip(), str(year).strip()))

            # Prefer keeping an ISBN if currently empty
            if not g.get("ISBN") and isbn:
                g["ISBN"] = isbn

        except Exception as e:
            logger.error(f"Error processing item {item}: {e}")
            continue

    # Finalize editions and choose representative Publisher/Year (most common)
    for key, book in groups.items():
        eds = [
            {"Publisher": pub if pub not in (None, 'nan', 'NaN') else "",
             "Year": yr if yr not in (None, 'nan', 'NaN') else ""}
            for (pub, yr) in sorted(editions_map.get(key, set()))
        ]
        book["editions"] = eds

        # Choose most common non-empty Publisher/Year for top-level fields
        pub_counter = Counter([e["Publisher"] for e in eds if e["Publisher"]])
        yr_counter = Counter([e["Year"] for e in eds if e["Year"]])
        if pub_counter:
            book["Publisher"] = pub_counter.most_common(1)[0][0]
        if yr_counter:
            book["Year"] = yr_counter.most_common(1)[0][0]

    logger.info(f"Merged {len(results)} records into {len(groups)} unique entries (title+author strict)")
    return list(groups.values())

# -------------------------
# Core Query Functions
# -------------------------
def get_library_statistics():
    """Get total number of books and other library statistics."""
    try:
        if not os.path.exists(CATALOGUE_DB):
            logger.error("Catalogue database not found")
            return None
            
        # Use context manager to ensure connection cleanup
        with sqlite3.connect(CATALOGUE_DB) as conn:
            cursor = conn.cursor()
        
        # Get total unique titles (based on ISBN or title)
        cursor.execute("SELECT COUNT(DISTINCT COALESCE(isbn, title)) FROM catalogue WHERE title IS NOT NULL")
        total_books = cursor.fetchone()[0]
        
        # Get total copies
        cursor.execute("SELECT COUNT(*) FROM catalogue")
        total_copies = cursor.fetchone()[0]
        
        # Get unique authors
        cursor.execute("SELECT COUNT(DISTINCT author) FROM catalogue WHERE author IS NOT NULL AND author != ''")
        total_authors = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"📊 Retrieved library statistics: {total_books} titles, {total_copies} copies")
        
        return {
            "intent": "statistics",
            "answer": f"📊 **Library Collection Statistics:**\n\n• **Total Unique Titles:** {total_books:,} books\n• **Total Copies:** {total_copies:,} items\n• **Authors Represented:** {total_authors:,} different authors\n\nOur collection is continuously growing to serve the academic needs of IIT Ropar."
        }
    except Exception as e:
        logger.error(f"Error getting library statistics: {e}")
        return {
            "intent": "statistics",
            "answer": "I apologize, but I'm currently unable to retrieve the exact statistics. Please contact the library help desk for this information."
        }

def extract_query_intent(query: str) -> dict:
    """
    Extract semantic intent from query for better understanding.
    Returns dict with intent type, key entities, and query variations.
    """
    query_lower = query.lower().strip()
    
    intent_data = {
        "original": query,
        "normalized": query_lower,
        "intent_type": None,
        "entities": [],
        "alternatives": []
    }
    
    # Detect question words for conversational understanding
    question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'can', 'is', 'are', 'do', 'does']
    has_question = any(query_lower.startswith(qw) for qw in question_words)
    
    # Generate query alternatives for better matching
    alternatives = [query_lower]
    
    # Remove question words for alternative matching
    if has_question:
        for qw in question_words:
            alt = re.sub(rf'\b{qw}\s+', '', query_lower, count=1)
            if alt != query_lower:
                alternatives.append(alt.strip())
    
    # Remove common filler words
    fillers = ['please', 'tell me', 'i want to know', 'can you', 'could you', 'about', 'the']
    for filler in fillers:
        alt = query_lower.replace(filler, ' ').strip()
        alt = ' '.join(alt.split())  # Normalize whitespace
        if alt and alt != query_lower:
            alternatives.append(alt)
    
    intent_data["alternatives"] = list(set(alternatives))
    return intent_data

def get_general_answer(query):
    """
    Enhanced answer matching with FAISS semantic search + JSON fallback.
    
    Search Strategy (in order):
    1. 🚀 FAISS semantic search (BEST - understands intent)
    2. ✅ Exact match in JSON (for known queries)
    3. 🔍 Fuzzy string matching (for typos)
    4. 📊 Keyword-based matching (last resort)
    
    Returns:
        dict: Answer data with 'intent' and 'answer' keys, or None
    """
    try:
        if not os.path.exists(GENERAL_QUERIES):
            logger.warning("general_queries.json not found")
            return None
            
        with open(GENERAL_QUERIES, 'r', encoding='utf-8') as f:
            general_queries = json.load(f)
        
        # Extract intent and generate query alternatives
        intent_data = extract_query_intent(query)
        query_lower = intent_data["normalized"]
        query_alternatives = intent_data["alternatives"]
        
        # ⚡ STRATEGY 1: FAISS Semantic Search (NEW - BEST)
        logger.info("🔍 Trying FAISS semantic search for general query...")
        faiss_result = semantic_search_general_queries(query, top_k=3, threshold=0.75)
        if faiss_result:
            logger.info("✅ FAISS semantic match found!")
            return faiss_result
        
        # STRATEGY 2: Exact match on original and alternatives
        for alt_query in [query_lower] + query_alternatives:
            if alt_query in general_queries:
                logger.info(f"✅ Exact match found for '{alt_query}'")
                result = general_queries[alt_query]
                if isinstance(result, dict):
                    return result
                return json.loads(result.replace("'", '"'))
        
        # STRATEGY 3: Fuzzy string matching
        for alt_query in query_alternatives:
            matches = get_close_matches(alt_query, general_queries.keys(), n=3, cutoff=0.75)
            if matches:
                logger.info(f"✅ Fuzzy match found: '{alt_query}' → '{matches[0]}'")
                result = general_queries[matches[0]]
                if isinstance(result, dict):
                    return result
                return json.loads(result.replace("'", '"'))
        
        # STRATEGY 4: Advanced semantic matching with expanded synonyms
        query_words = set(query_lower.split())
        
        # Comprehensive synonym mapping
        synonyms = {
            'hours': {'timing', 'timings', 'time', 'schedule', 'open', 'close', 'timing', 'hours'},
            'timing': {'hours', 'timings', 'time', 'schedule', 'open', 'when'},
            'timings': {'hours', 'timing', 'time', 'schedule', 'open', 'when'},
            'open': {'timing', 'hours', 'schedule', 'timings', 'available', 'accessible'},
            'fine': {'penalty', 'charge', 'fee', 'fines', 'late fee', 'overdue'},
            'book': {'books', 'title', 'titles', 'volume', 'publication'},
            'renew': {'renewal', 'extend', 'extension', 'reissue'},
            'issue': {'borrow', 'checkout', 'take', 'get', 'loan'},
            'return': {'submit', 'give back', 'bring back'},
            'search': {'find', 'look', 'locate', 'discover'},
            'find': {'search', 'look', 'locate', 'get'},
            'e-journals': {'ejournal', 'ejournals', 'e-journal', 'journal', 'journals', 'e-resources', 'digital', 'online'},
            'ejournal': {'e-journals', 'ejournals', 'e-journal', 'journals', 'e-resources'},
            'e-resources': {'eresources', 'e-journals', 'ejournals', 'digital', 'online', 'electronic'},
            'help': {'assist', 'support', 'guide', 'information'},
            'access': {'use', 'get', 'obtain', 'available'},
        }
        
        # Expand query words with synonyms
        expanded_query = set(query_words)
        for word in query_words:
            if word in synonyms:
                expanded_query.update(synonyms[word])
        
        # Score-based matching with multiple factors
        best_match = None
        best_score = 0
        match_details = {}
        
        for key in general_queries.keys():
            key_words = set(key.lower().split())
            
            # Factor 1: Direct word overlap
            common_words = expanded_query & key_words
            overlap_score = len(common_words) / max(len(query_words), len(key_words)) if len(common_words) > 0 else 0
            
            # Factor 2: Substring matching (boost score if query contains key or vice versa)
            substring_boost = 0
            if len(query_lower) >= 4 and len(key) >= 4:
                if query_lower in key or key in query_lower:
                    substring_boost = 0.3
                elif any(word in key for word in query_words if len(word) >= 4):
                    substring_boost = 0.2
            
            # Factor 3: Word order similarity (boost if words appear in similar order)
            order_boost = 0
            if overlap_score > 0:
                query_word_list = query_lower.split()
                key_word_list = key.split()
                common_in_order = sum(1 for i, w in enumerate(query_word_list) 
                                     if i < len(key_word_list) and w in key_word_list[max(0, i-1):min(len(key_word_list), i+2)])
                if common_in_order > 0:
                    order_boost = 0.15 * (common_in_order / len(query_word_list))
            
            # Combined score
            total_score = overlap_score + substring_boost + order_boost
            
            if total_score > best_score:
                best_score = total_score
                best_match = key
                match_details = {
                    "overlap": overlap_score,
                    "substring": substring_boost,
                    "order": order_boost,
                    "total": total_score
                }
        
        # Lowered threshold for better recall (0.35 instead of 0.50)
        if best_match and best_score > 0.35:
            logger.info(f"✅ Semantic match: '{query}' → '{best_match}' (score: {best_score:.2f}, details: {match_details})")
            result = general_queries[best_match]
            if isinstance(result, dict):
                return result
            return json.loads(result.replace("'", '"'))
        
        logger.info(f"⚠️ No match found in general queries for '{query}' (best score: {best_score:.2f})")
        return None
        
    except Exception as e:
        logger.error(f"Error in get_general_answer: {e}")
        return None

def expand_book_query(query: str) -> list:
    """
    Generate query variations for better book search recall.
    Returns list of query variations to try.
    """
    variations = [query]
    query_lower = query.lower().strip()
    
    # Remove common prefixes
    prefixes = ['book on', 'books on', 'book about', 'books about', 'textbook on', 'textbook for']
    for prefix in prefixes:
        if query_lower.startswith(prefix):
            clean_query = query_lower.replace(prefix, '').strip()
            if clean_query:
                variations.append(clean_query)
    
    # Extract author names (common patterns)
    author_patterns = [
        r'by\s+([a-z\s]+)',
        r'author[:\s]+([a-z\s]+)',
        r'written\s+by\s+([a-z\s]+)'
    ]
    for pattern in author_patterns:
        match = re.search(pattern, query_lower)
        if match:
            author = match.group(1).strip()
            if author and len(author) > 2:
                variations.append(author)
    
    # Remove stop words for subject searches
    stop_words = ['the', 'a', 'an', 'of', 'for', 'in', 'on', 'at', 'to', 'with']
    words = query_lower.split()
    filtered_words = [w for w in words if w not in stop_words]
    if len(filtered_words) < len(words) and len(filtered_words) > 0:
        variations.append(' '.join(filtered_words))
    
    return list(set(variations))  # Remove duplicates

def search_catalogue(query, limit=10):
    """
    Enhanced catalogue search with query expansion and intelligent ranking.
    Searches across title, author, ISBN, call number with relevance scoring.
    """
    try:
        if not os.path.exists(CATALOGUE_DB):
            logger.error("Catalogue database not found")
            return []
            
        conn = sqlite3.connect(CATALOGUE_DB)
        cursor = conn.cursor()
        
        # Generate query variations
        query_variations = expand_book_query(query)
        all_results = []
        seen_ids = set()
        
        for q_var in query_variations:
            # Multi-field search with relevance scoring
            sql = """
            SELECT *, 
                CASE 
                    WHEN LOWER(title) = LOWER(?) THEN 100
                    WHEN LOWER(title) LIKE LOWER(?) THEN 80
                    WHEN LOWER(author) LIKE LOWER(?) THEN 70
                    WHEN LOWER(isbn) = LOWER(?) THEN 90
                    WHEN LOWER(itemcallnumber) LIKE LOWER(?) THEN 50
                    ELSE 30
                END as relevance_score
            FROM catalogue 
            WHERE LOWER(title) LIKE LOWER(?) 
            OR LOWER(author) LIKE LOWER(?) 
            OR LOWER(isbn) LIKE LOWER(?)
            OR LOWER(itemcallnumber) LIKE LOWER(?)
            ORDER BY relevance_score DESC
            LIMIT ?
            """
            
            exact_match = q_var
            fuzzy_match = f"%{q_var}%"
            
            cursor.execute(sql, [
                exact_match, fuzzy_match, fuzzy_match, exact_match, fuzzy_match,
                fuzzy_match, fuzzy_match, fuzzy_match, fuzzy_match, limit * 2
            ])
            
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # Use a combination of fields as unique ID
                result_id = f"{result.get('title', '')}-{result.get('author', '')}-{result.get('isbn', '')}"
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    all_results.append(result)
                
                if len(all_results) >= limit:
                    break
            
            if len(all_results) >= limit:
                break
        
        # Connection closed automatically by context manager
        # Sort by relevance score
        all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        final_results = all_results[:limit]
        logger.info(f"📚 Found {len(final_results)} results in catalogue (tried {len(query_variations)} variations)")
        return final_results
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

def search_catalogue_author(author_name, limit=20):
    """Search catalogue focusing on author field only.
    Returns list of dict rows like search_catalogue.
    """
    try:
        if not author_name or not os.path.exists(CATALOGUE_DB):
            return []
        sql = """
        SELECT * FROM catalogue
        WHERE author LIKE ?
        LIMIT ?
        """
        term = f"%{author_name}%"
        with sqlite3.connect(CATALOGUE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (term, limit))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        logger.info(f"👤 Author search found {len(results)} results for '{author_name}'")
        return results
    except Exception as e:
        logger.error(f"Author search error: {e}")
        return []

def normalize_book_query(original_query: str, corrected_query: str) -> tuple[str, str]:
    """Detect if query is author-focused and extract author name.
    Returns (clean_query, intent) where intent in {"author", "topic"}.
    """
    cq = (corrected_query or "").strip()
    oq = (original_query or "").strip()
    q_lower = cq.lower()

    # Simple author patterns
    if 'by ' in q_lower or 'author' in q_lower:
        # Extract author name after 'by' or 'author:'
        for prefix in ['books by ', 'by ', 'author: ', 'author ']:
            if prefix in q_lower:
                idx = q_lower.find(prefix)
                author_part = oq[idx + len(prefix):].strip()
                author_clean = re.sub(r'[?.,!]+$', '', author_part).strip()
                return author_clean, "author"
    
    # Default: treat as topic
    return cq, "topic"

def semantic_search_tfidf_fallback(query, top_k=5):
    """
    Lightweight TF-IDF semantic search fallback that is cached in-memory.
    Builds vectorizer+matrix once per process to avoid per-query rebuilds.
    Only used when FAISS index isn't available.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        # Build or reuse cached TF-IDF resources
        global _tfidf_cache
        if '_built' not in _tfidf_cache:
            start = time.time()
            conn = sqlite3.connect(str(CATALOGUE_DB))
            cursor = conn.cursor()
            # Also fetch rowid so we can map back to full records efficiently
            cursor.execute("SELECT rowid, title, author FROM catalogue")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return []

            rowids = [r[0] for r in rows]
            corpus = [f"{r[1] or ''} {r[2] or ''}" for r in rows]
            vectorizer = TfidfVectorizer(max_features=3000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)

            _tfidf_cache['vectorizer'] = vectorizer
            _tfidf_cache['matrix'] = tfidf_matrix
            _tfidf_cache['rowids'] = rowids
            _tfidf_cache['_built'] = True
            logger.info(f"✅ Built TF-IDF cache in {time.time()-start:.2f}s for {len(rowids)} rows")

        vectorizer = _tfidf_cache['vectorizer']
        tfidf_matrix = _tfidf_cache['matrix']
        rowids = _tfidf_cache['rowids']

        query_vec = vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

        # Top-k indices by similarity
        top_indices = np.argsort(similarities)[::-1][:top_k * 2]

        # Fetch corresponding records (apply threshold)
        selected_rowids = [rowids[i] for i in top_indices if similarities[i] > 0.1][:top_k]
        if not selected_rowids:
            return []

        # Retrieve full rows for selected rowids preserving order
        placeholders = ','.join(['?'] * len(selected_rowids))
        # Secure parameterized retrieval (avoid f-string SQL injection vector)
        with sqlite3.connect(str(CATALOGUE_DB)) as conn:
            cursor = conn.cursor()
            sql = f"SELECT rowid, * FROM catalogue WHERE rowid IN ({placeholders})"
            cursor.execute(sql, selected_rowids)  # parameters safely bound
            fetched = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]

        # Map by rowid to keep original top-k order
        by_rowid = {r[0]: dict(zip(col_names, r)) for r in fetched}
        results = [by_rowid[rid] for rid in selected_rowids if rid in by_rowid]
        logger.info(f"🔍 TF-IDF fallback returned {len(results)} results")
        return results
    except Exception as e:
        logger.warning(f"TF-IDF fallback semantic search failed: {e}")
        return []

# ========================
# GLOBAL MODEL LOADING (once at startup)
# ========================
_sentence_transformer_model = None

def _get_sentence_transformer():
    """Get or initialize the SentenceTransformer model (singleton pattern)."""
    global _sentence_transformer_model
    if _sentence_transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_path = str(Path(__file__).parent / "models" / "all-MiniLM-L6-v2")
            logger.info(f"🔄 Loading SentenceTransformer model from {model_path}...")
            start = time.time()
            _sentence_transformer_model = SentenceTransformer(model_path)
            elapsed = time.time() - start
            logger.info(f"✅ SentenceTransformer loaded in {elapsed:.2f}s (will be reused)")
        except Exception as e:
            logger.error(f"❌ Failed to load SentenceTransformer: {e}")
            raise
    return _sentence_transformer_model

# Cache FAISS indices (loaded once, reused for all searches)
_faiss_cache = {}
_tfidf_cache = {}
_faiss_loading = False  # Prevent concurrent loads

def _load_faiss_resources():
    """Load and cache FAISS model, index, and mapping.
    
    PERFORMANCE OPTIMIZED:
    - Lazy loads on first search (not at app startup to avoid timeout)
    - Caches in memory for subsequent queries
    - Thread-safe loading prevention
    """
    global _faiss_loading
    
    # Return cached if available
    if 'model' in _faiss_cache:
        return _faiss_cache['model'], _faiss_cache['index'], _faiss_cache['mapping']
    
    # Prevent concurrent loading
    if _faiss_loading:
        logger.warning("⏳ FAISS already loading in another thread, waiting...")
        # Wait for up to 10 seconds for the other load to complete
        for _ in range(20):
            time.sleep(0.5)
            if 'model' in _faiss_cache:
                return _faiss_cache['model'], _faiss_cache['index'], _faiss_cache['mapping']
        raise Exception("FAISS loading timeout")
    
    _faiss_loading = True
    try:
        import faiss
        
        logger.info("🔄 Loading FAISS catalogue index (first query only)...")
        start = time.time()
        
        # Reuse the global SentenceTransformer model
        model = _get_sentence_transformer()
        index = faiss.read_index(str(INDEX_FILE))
        with open(MAPPING_FILE, "rb") as f:
            mapping = pickle.load(f)
        
        _faiss_cache['model'] = model
        _faiss_cache['index'] = index
        _faiss_cache['mapping'] = mapping
        
        elapsed = time.time() - start
        logger.info(f"✅ FAISS catalogue index loaded and cached in {elapsed:.2f}s")
        
        return model, index, mapping
    finally:
        _faiss_loading = False

# -------------------------
# General Queries FAISS Search
# -------------------------
_general_faiss_cache = {}
_general_faiss_loading = False

def _load_general_faiss_resources():
    """
    Load and cache FAISS resources for general queries semantic search.
    Similar to _load_faiss_resources but for library policy Q&A.
    
    Returns:
        tuple: (model, index, mapping) for general queries
    """
    global _general_faiss_loading
    
    # Return cached if available
    if 'model' in _general_faiss_cache:
        return (_general_faiss_cache['model'], 
                _general_faiss_cache['index'], 
                _general_faiss_cache['mapping'])
    
    # Prevent concurrent loading
    if _general_faiss_loading:
        logger.warning("⏳ General FAISS already loading, waiting...")
        for _ in range(20):
            time.sleep(0.5)
            if 'model' in _general_faiss_cache:
                return (_general_faiss_cache['model'], 
                        _general_faiss_cache['index'], 
                        _general_faiss_cache['mapping'])
        raise Exception("General FAISS loading timeout")
    
    _general_faiss_loading = True
    try:
        import faiss
        
        logger.info("🔄 Loading general queries FAISS index...")
        start = time.time()
        
        # Reuse the global SentenceTransformer model
        model = _get_sentence_transformer()
        index = faiss.read_index(str(GENERAL_QUERIES_INDEX_FILE))
        
        with open(GENERAL_QUERIES_MAPPING_FILE, "rb") as f:
            mapping = pickle.load(f)
        
        _general_faiss_cache['model'] = model
        _general_faiss_cache['index'] = index
        _general_faiss_cache['mapping'] = mapping
        
        elapsed = time.time() - start
        logger.info(f"✅ General FAISS loaded in {elapsed:.2f}s ({len(mapping)} Q&A pairs)")
        
        return model, index, mapping
    finally:
        _general_faiss_loading = False


def semantic_search_general_queries(query: str, top_k: int = 3, threshold: float = 0.75):
    """
    Use FAISS to semantically search general library queries.
    Provides much better matching than exact string matching.
    
    Example:
        User: "what time library open?"
        FAISS: Matches "library timings" with 92% similarity
    
    Args:
        query: User's question
        top_k: Number of top matches to return
        threshold: Similarity threshold (0-1, higher = stricter)
    
    Returns:
        dict: Best matching answer data, or None if no good match
    """
    try:
        # Check if FAISS index exists
        if not GENERAL_QUERIES_INDEX_FILE.exists() or not GENERAL_QUERIES_MAPPING_FILE.exists():
            logger.debug("General queries FAISS index not available, skipping semantic search")
            return None
        
        # Load FAISS resources (cached after first call)
        model, index, mapping = _load_general_faiss_resources()
        
        # Encode query into embedding
        query_embedding = model.encode([query])
        
        # Search using FAISS (L2 distance - lower is better)
        distances, indices = index.search(query_embedding, top_k)
        
        # Convert L2 distance to similarity score (0-1, higher is better)
        # Formula: similarity = 1 / (1 + distance)
        similarities = [1 / (1 + dist) for dist in distances[0]]
        
        # Get best match
        best_idx = indices[0][0]
        best_similarity = similarities[0]
        
        logger.info(f"🔍 FAISS general search: '{query[:50]}...' → similarity={best_similarity:.3f}")
        
        # Log top 3 matches for debugging
        for i, (idx, sim) in enumerate(zip(indices[0][:3], similarities[:3])):
            match_question = mapping[idx]['question'][:60]
            logger.debug(f"  {i+1}. [{sim*100:.1f}%] {match_question}")
        
        # Apply threshold
        if best_similarity >= threshold:
            match = mapping[best_idx]
            logger.info(f"✅ FAISS match: '{match['question'][:60]}' (score: {best_similarity:.3f})")
            return match['answer_data']
        else:
            logger.debug(f"⚠️ Best match below threshold: {best_similarity:.3f} < {threshold}")
            return None
            
    except Exception as e:
        logger.warning(f"FAISS general search failed: {e}")
        return None

def semantic_search(query, top_k=5):
    """Perform FAISS semantic search if available, fallback to TF-IDF."""
    try:
        if not os.path.exists(INDEX_FILE) or not os.path.exists(MAPPING_FILE):
            logger.debug("FAISS index not available, trying TF-IDF fallback")
            return semantic_search_tfidf_fallback(query, top_k)
        
        # Use cached resources instead of loading every time
        model, index, mapping = _load_faiss_resources()
        query_embedding = model.encode([query])
        distances, indices = index.search(query_embedding, top_k)
        results = []
        for idx in indices[0]:
            if idx < len(mapping):
                results.append(mapping[idx])
        logger.info(f"🔍 Found {len(results)} results via FAISS semantic search")
        return results
    except Exception as e:
        logger.warning(f"FAISS semantic search failed: {e}, trying TF-IDF fallback")
        return semantic_search_tfidf_fallback(query, top_k)

def hybrid_book_search(query, intent: str | None = None):
    """Combine catalogue and semantic search, then merge duplicates.
    If intent == 'author', prefer author field in catalogue search.
    """
    all_results = []
    
    # Try catalogue search (author-focused if intent indicates author)
    if intent == "author":
        catalogue_results = search_catalogue_author(query, limit=20)
        if not catalogue_results:
            catalogue_results = search_catalogue(query, limit=20)
    else:
        catalogue_results = search_catalogue(query, limit=20)
    if catalogue_results:
        all_results.extend(catalogue_results)
    
    # Try semantic search
    semantic_results = semantic_search(query, top_k=10)
    if semantic_results:
        all_results.extend(semantic_results)
    
    # Merge and deduplicate
    if all_results:
        merged = merge_duplicates(all_results)
        logger.info(f"✅ Hybrid search returned {len(merged)} unique books")
        return merged
    
    return []

# -------------------------
# Main Query Handler 
# -------------------------
@rate_limit(max_requests=20, window=60)  # 🔒 Rate limiting: 20 requests per minute
def get_nandu_response(q, search_mode: str = "auto", client_ip: str = "default"):
    """
    Main entry point for answering user queries with intelligent classification.
    🔒 SECURITY: Rate limited, input validated, audit logged
    
    Args:
        q: User query string
        search_mode: Search mode filter ('auto', 'books', 'library', 'website')
            - auto: Use intelligent classification (default)
            - books: Force book/catalogue search
            - library: Force library query JSON lookup
            - website: Force website scraping
        client_ip: Client IP for rate limiting (default: "default")
    
    Flow:
    1. ✅ Rate limit check (20 req/min per IP)
    2. ✅ Input validation (length, gibberish detection)
    3. Auto-correct spelling
    4. Check for statistics queries first
    5. If search_mode set, bypass classification and route directly
    6. Otherwise classify query using LLaMA (book vs general)
    7. Handle accordingly with professional formatting
    8. ✅ Audit log query
    9. Return structured response
    """
    start_time = time.time()
    success = True
    response = ""
    
    # SECURITY: Input validation
    if not q or not isinstance(q, str):
        return "Please enter a query."
    
    # SECURITY: Check query length BEFORE processing
    if len(q) > 300:
        logger.warning(f"⚠️ Query too long ({len(q)} chars): {q[:50]}...")
        response = "⚠️ **Query too long.** Please keep your question under 300 characters."
        success = False
        audit_log_query(q[:100], response, client_ip, time.time() - start_time, success)
        return response
        
    original_query = q.strip()
    
    # Validate query is not gibberish
    is_valid, error_msg = is_valid_query(original_query)
    if not is_valid:
        logger.warning(f"❌ Invalid/gibberish query rejected: '{original_query}'")
        response = error_msg
        success = False
        audit_log_query(original_query, response, client_ip, time.time() - start_time, success)
        return response
    
    # Step 1: Auto-correct spelling
    corrected_query = auto_correct_spelling(original_query)
    query = corrected_query.strip()
    
    logger.info(f"🔍 Processing query: '{query}' [mode: {search_mode}]")
    
    try:
        # Step 2: Check for statistics/count queries FIRST (but exclude borrowing limit queries)
        query_lower = query.lower()
        
        # Patterns that indicate LIBRARY COLLECTION statistics
        statistics_patterns = [
            'total books in library', 'number of books in library',
            'how many books in library', 'how many books does library have',
            'how many books library have', 'books in library',
            'library collection', 'collection size', 'total collection',
            'library has how many', 'size of library'
        ]
        
        # Patterns that indicate BORROWING LIMITS (general query, not statistics)
        borrowing_patterns = [
            'students get', 'students borrow', 'students can borrow',
            'students can get', 'students issue', 'students can issue',
            'can i borrow', 'can i get', 'can i issue',
            'allowed to borrow', 'allowed to get', 'borrow limit',
            'issue limit', 'borrowing limit', 'issuing limit',
            'ug students', 'pg students', 'phd students',
            'faculty get', 'staff get', 'professor get'
        ]
        
        # Check if it's a borrowing limit query (should be treated as general)
        is_borrowing_query = any(pattern in query_lower for pattern in borrowing_patterns)
        
        # Only trigger statistics if it's specifically about library collection AND NOT about borrowing
        is_statistics_query = any(pattern in query_lower for pattern in statistics_patterns) and not is_borrowing_query
        
        if is_statistics_query:
            logger.info("📊 Detected library collection statistics query")
            stats = get_library_statistics()
            if stats:
                return f"💡 **Here's what I found:**\n\n{stats['answer']}"
            else:
                return "⚠️ I couldn't retrieve the library statistics at this time. Please try again later."
        
        # Step 3: Determine query type based on search_mode or classification
        if search_mode == "books":
            logger.info("🔒 Forced book search mode")
            query_type = 'book'
        elif search_mode == "library":
            logger.info("🔒 Forced library query mode (JSON)")
            query_type = 'library'
        elif search_mode == "website":
            logger.info("🔒 Forced website search mode")
            query_type = 'website'
        else:  # auto mode
            # Classify query using LLaMA
            query_type = classify_query_with_llama(query)
        
        # Step 4: Handle based on classification or forced mode
        if query_type == 'library':
            # Handle library query (JSON file only)
            try:
                general = get_general_answer(query)
                if general:
                    logger.info("✅ Found answer in library queries JSON")
                    answer = general.get('answer', '')
                    
                    # Add conversational context based on query type
                    query_lower = query.lower()
                    if any(kw in query_lower for kw in ['timing', 'hours', 'open', 'when']):
                        prefix = "⏰ **Library Hours:**\n\n"
                    elif any(kw in query_lower for kw in ['fine', 'penalty', 'fee']):
                        prefix = "� **Fine Policy:**\n\n"
                    elif any(kw in query_lower for kw in ['borrow', 'issue', 'how many']):
                        prefix = "📖 **Borrowing Information:**\n\n"
                    elif any(kw in query_lower for kw in ['search', 'find', 'opac']):
                        prefix = "🔍 **How to Search:**\n\n"
                    else:
                        prefix = "�💡 **Here's what I found:**\n\n"
                    
                    return prefix + answer
                else:
                    logger.info("⚠️ No match in library queries JSON")
                    return "🤔 **I couldn't find specific information about that.**\n\n**Here are some options:**\n• Try rephrasing your question\n• Visit the [official library website](https://www.iitrpr.ac.in/library/)\n• Email the library staff at **libraryhelpdesk@iitrpr.ac.in**\n• Ask me about library hours, borrowing rules, or how to search for books!"
                    
            except Exception as e:
                logger.error(f"Error handling library query: {e}")
                return "⚠️ Sorry, I encountered an error processing your query. Please try again."
        
        elif query_type == 'website':
            # Handle website search only
            try:
                logger.info("🌐 Searching official website only...")
                website_data = fetch_website_content()
                if website_data:
                    website_result = search_website_content(query, website_data)
                    if website_result:
                        logger.info("✅ Found answer from website")
                        return f"💡 {website_result['answer']}"
                
                logger.info("⚠️ No match on website")
                return "🤔 **I couldn't find this information on the website.**\n\nPlease:\n• Try different keywords\n• Visit the [official library website](https://www.iitrpr.ac.in/library/) directly\n• Contact the library staff at **library@iitrpr.ac.in**"
                    
            except Exception as e:
                logger.error(f"Error handling website search: {e}")
                return "⚠️ Sorry, I encountered an error searching the website. Please try again."
        
        elif query_type == 'general':
            # Handle general query (auto mode: try JSON then website)
            try:
                # First, try general_queries.json
                general = get_general_answer(query)
                if general:
                    logger.info("✅ Found answer in general queries")
                    answer = general.get('answer', '')
                    
                    # Conversational prefix based on query context
                    query_lower = query.lower()
                    if any(kw in query_lower for kw in ['timing', 'hours', 'open', 'when', 'schedule']):
                        prefix = "⏰ **Library Hours:**\n\n"
                    elif any(kw in query_lower for kw in ['fine', 'penalty', 'fee', 'late']):
                        prefix = "� **About Fines:**\n\n"
                    elif any(kw in query_lower for kw in ['borrow', 'issue', 'how many', 'limit']):
                        prefix = "📖 **Borrowing Guidelines:**\n\n"
                    elif any(kw in query_lower for kw in ['search', 'find', 'opac', 'catalogue']):
                        prefix = "🔍 **Searching for Books:**\n\n"
                    elif any(kw in query_lower for kw in ['membership', 'join', 'register']):
                        prefix = "🎓 **Membership Information:**\n\n"
                    elif any(kw in query_lower for kw in ['contact', 'email', 'phone', 'reach']):
                        prefix = "📞 **Contact Information:**\n\n"
                    else:
                        prefix = "💡 **Here's the information:**\n\n"
                    
                    return prefix + answer
                
                # If not found in general queries, try fetching from website
                logger.info("🌐 Checking official website for information...")
                website_data = fetch_website_content()
                if website_data:
                    website_result = search_website_content(query, website_data)
                    if website_result:
                        logger.info("✅ Found answer from website")
                        return f"🌐 **From the Library Website:**\n\n{website_result['answer']}"
                
                # Conversational fallback message
                logger.info("⚠️ No match in general queries or website, returning fallback")
                return "🤔 **I don't have specific information about that right now.**\n\n**Here's how I can help you:**\n• Search for books by title, author, or subject\n• Answer questions about library hours and policies\n• Explain borrowing rules and fine policies\n• Guide you on using OPAC and e-resources\n\n**For other questions:**\n• Visit the [official library website](https://www.iitrpr.ac.in/library/)\n• Email **libraryhelpdesk@iitrpr.ac.in**\n• Visit the library helpdesk in person\n\nFeel free to ask me anything about the library!"
                    
            except Exception as e:
                logger.error(f"Error handling general query: {e}")
                return "⚠️ Sorry, I encountered an error processing your query. Please try again."
        
        else:  # query_type == 'book'
            # Handle book query with conversational responses
            try:
                # Normalize phrasing (e.g., "books by X") and detect intent
                clean_q, book_intent = normalize_book_query(original_query, query)
                # Run hybrid search with normalized query and intent
                results = hybrid_book_search(clean_q, intent=book_intent)
                
                if results:
                    # Format book results with conversational intro
                    count = len(results)
                    logger.info(f"✅ Returning {count} book result(s)")
                    
                    # Conversational intro based on context
                    if book_intent == "author":
                        intro = f"📚 **Great! I found {count} book{'s' if count != 1 else ''} by {clean_q} in our library:**\n\n"
                    elif count == 1:
                        intro = f"📚 **Perfect! I found exactly what you're looking for:**\n\n"
                    elif count <= 3:
                        intro = f"📚 **I found {count} books matching '{clean_q}':**\n\n"
                    else:
                        intro = f"📚 **I found {count} books related to '{clean_q}'. Here are the most relevant ones:**\n\n"
                    
                    book_cards = format_results(results[:10])  # Limit to top 10 for better UX
                    
                    # Add helpful footer if many results
                    footer = ""
                    if count > 10:
                        footer = f"\n\n💡 *Showing top 10 results. {count - 10} more books are available. Try refining your search for more specific results.*"
                    
                    return intro + book_cards + footer
                else:
                    # No results found - provide helpful suggestions
                    logger.info("⚠️ No book results found")
                    
                    # More conversational no-results message
                    suggestions = [
                        f"• Try broader keywords (e.g., 'machine learning' instead of 'deep learning transformers')",
                        f"• Check the spelling of author names or book titles",
                        f"• Use the [OPAC system](https://opac.iitrpr.ac.in) for advanced search",
                        f"• Ask library staff for help at **libraryhelpdesk@iitrpr.ac.in**"
                    ]
                    
                    return f"🤔 **I couldn't find any books matching '{clean_q}' in our catalogue.**\n\n**Here's what you can try:**\n" + "\n".join(suggestions)
                    
            except Exception as e:
                logger.error(f"Error handling book query: {e}")
                track_error(e, "get_nandu_response:book_query")
                response = "⚠️ Sorry, I encountered an error searching for books. Please try again or contact the library helpdesk for assistance."
                success = False
                return response
        
    except Exception as e:
        logger.error(f"Critical error in get_nandu_response: {e}")
        track_error(e, "get_nandu_response:critical")
        response = "⚠️ Sorry, I encountered an unexpected error. Please try again or contact support if the problem persists."
        success = False
        return response
    finally:
        # 🔒 SECURITY: Always audit log queries (even on error)
        processing_time = time.time() - start_time
        audit_log_query(
            query=original_query if 'original_query' in locals() else q[:100],
            response=response if response else "no_response",
            client_ip=client_ip,
            processing_time=processing_time,
            success=success
        )


# ========================
# MODULE INITIALIZATION
# ========================
# Pre-load the SentenceTransformer model once at startup
# This prevents multiple loads during runtime
try:
    logger.info("🚀 Initializing Nandu Brain module...")
    _get_sentence_transformer()  # Load model once at startup
    logger.info("✅ Nandu Brain initialization complete")
except Exception as e:
    logger.warning(f"⚠️ Could not pre-load SentenceTransformer at startup: {e}")
    logger.info("Model will be loaded on first query instead")