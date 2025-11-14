"""
FastAPI wrapper for Nalanda Library Chatbot - PHP Integration Server
Provides REST API endpoints for PHP frontend integration
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
import sys
from pathlib import Path
import logging
import time
import os
import json
import subprocess
from typing import Optional

# Enable web scraping for OPAC functionality
os.environ['NANDU_WEBSCRAPE'] = '1'

# Add parent directory to path to import nandu_brain
sys.path.insert(0, str(Path(__file__).parent))
import nandu_brain

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nalanda Library Chatbot API - PHP Integration Server",
    description="Library chatbot backend for IIT Ropar - Local Testing",
    version="1.0.0"
)

# CORS - Allow localhost for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    search_mode: str = "auto"

class ChatResponse(BaseModel):
    success: bool
    response: str = ""
    query: str
    processing_time: float
    error: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, data: ChatRequest):
    """
    Main chat endpoint - processes user queries
    
    Request Body:
        {
            "query": "python books",
            "search_mode": "auto"  # auto|books|library|website
        }
    
    Response:
        {
            "success": true,
            "response": "📚 I found 5 books...",
            "query": "python books",
            "processing_time": 1.23
        }
    """
    start_time = time.time()
    
    try:
        # Get client IP from headers (set by PHP or direct access)
        client_ip = request.headers.get('X-Client-IP', 
                     request.headers.get('X-Forwarded-For',
                     request.client.host))
        
        logger.info(f"📥 Query from {client_ip}: '{data.query[:50]}...'")
        
        # Call nandu_brain with rate limiting and audit logging
        response = nandu_brain.get_nandu_response(
            q=data.query,
            search_mode=data.search_mode,
            client_ip=client_ip
        )
        
        # Check if rate limited (returns dict with 'error' key)
        if isinstance(response, dict) and 'error' in response:
            logger.warning(f"⚠️ Rate limit hit for {client_ip}")
            return ChatResponse(
                success=False,
                response="",
                query=data.query,
                processing_time=time.time() - start_time,
                error=response['message']
            )
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Response generated in {processing_time:.2f}s")
        
        # If response looks like raw HTML book cards, transform to plain JSON format
        if isinstance(response, str) and '<div class="book-card"' in response:
            from bs4 import BeautifulSoup  # lightweight parse of our own HTML structure
            import re
            soup = BeautifulSoup(response, 'html.parser')
            cards = soup.select('div.book-card')
            books_raw = []
            
            # First pass: extract all book data
            for card in cards:
                h4 = card.find('h4')
                title = h4.get_text(strip=True) if h4 else ''
                
                # Extract author
                author = ''
                for p in card.find_all('p'):
                    txt = p.get_text(' ', strip=True)
                    if txt.startswith('Author:'):
                        author = txt.replace('Author:', '').strip()
                        break
                
                # Extract year
                year = ''
                for p in card.find_all('p'):
                    txt = p.get_text(' ', strip=True)
                    if txt.startswith('Published:'):
                        m = re.search(r'(19|20)\d{2}', txt)
                        year = m.group(0) if m else ''
                        break
                
                # Extract ISBN
                isbn = ''
                for p in card.find_all('p'):
                    txt = p.get_text(' ', strip=True)
                    if txt.startswith('ISBN:'):
                        isbn = txt.replace('ISBN:', '').strip()
                        break
                
                # Extract copies and call numbers from book-meta div
                copies = 0
                call_numbers = []
                meta_div = card.find('div', class_='book-meta')
                if meta_div:
                    for span in meta_div.find_all('span'):
                        txt = span.get_text(' ', strip=True)
                        if txt.startswith('Copies:'):
                            try:
                                copies = int(txt.replace('Copies:', '').strip())
                            except:
                                copies = 0
                        elif txt.startswith('Call Numbers:'):
                            cn_text = txt.replace('Call Numbers:', '').strip()
                            call_numbers = [cn.strip() for cn in cn_text.split(',')]
                
                # Extract accession numbers
                accessions = []
                accession_div = card.find('div', class_='accession-list')
                if accession_div:
                    acc_text = accession_div.get_text(strip=True)
                    if acc_text:
                        accessions = [a.strip() for a in acc_text.split(',')]
                
                books_raw.append({
                    'title': title,
                    'author': author,
                    'year': year,
                    'isbn': isbn,
                    'copies': copies,
                    'call_numbers': call_numbers,
                    'accessions': accessions
                })
            
            # Second pass: merge duplicates with same title, author, and ISBN
            merged_books = {}
            for book in books_raw:
                # Create a key based on title, author, and ISBN (normalized)
                key = (
                    book['title'].lower().strip(),
                    book['author'].lower().strip(),
                    book['isbn'].strip()
                )
                
                if key in merged_books:
                    # Merge with existing entry
                    merged_books[key]['copies'] += book['copies']
                    # Add unique call numbers
                    for cn in book['call_numbers']:
                        if cn and cn not in merged_books[key]['call_numbers']:
                            merged_books[key]['call_numbers'].append(cn)
                    # Add unique accessions
                    for acc in book['accessions']:
                        if acc and acc not in merged_books[key]['accessions']:
                            merged_books[key]['accessions'].append(acc)
                else:
                    # New entry
                    merged_books[key] = book
            
            # Convert to final format (limit to 6 books)
            books = []
            for book in list(merged_books.values())[:6]:
                summary = f"{book['title']} by {book['author']} ({book['year']})."[:240]
                books.append({
                    'title': book['title'],
                    'author': book['author'],
                    'year': book['year'],
                    'isbn': book['isbn'],
                    'copies': str(book['copies']),
                    'call_numbers': ', '.join(book['call_numbers']),
                    'accessions': ', '.join(book['accessions']) if book['accessions'] else '',
                    'summary': summary
                })
            
            # Wrap in JSON string for frontend, but keep API contract 'response' as string
            import json
            response_payload = json.dumps({ 'books': books }, ensure_ascii=False)
            response = f"```json\n{response_payload}\n```"
        # Ensure response is a string for model contract
        if not isinstance(response, str):
            response = str(response)
        return ChatResponse(
            success=True,
            response=response,
            query=data.query,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {e}")
        return ChatResponse(
            success=False,
            response="",
            query=data.query,
            processing_time=time.time() - start_time,
            error=f"Internal server error: {str(e)}"
        )

# ---------------------------
# Admin helper utilities
# ---------------------------
BASE_DIR = Path(__file__).parent.resolve()

def _run_script(cmd: list[str]) -> tuple[bool, str]:
    """Run a script in backend directory and return (ok, output)."""
    try:
        proc = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, shell=False)
        out = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
        ok = proc.returncode == 0
        return ok, out.strip()
    except Exception as e:
        return False, f"Exception running {' '.join(cmd)}: {e}"

def _save_upload(dest_path: Path, up: UploadFile) -> None:
    with dest_path.open("wb") as f:
        for chunk in iter(lambda: up.file.read(1024 * 1024), b""):
            if not chunk:
                break
            f.write(chunk)

# ---------------------------
# Admin API: Cache, Uploads, Rebuilds, Status
# ---------------------------

@app.post("/admin/clear-cache")
async def admin_clear_cache(request: Request):
    """Clear backend caches and lightweight state."""
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    
    try:
        # Best-effort clears based on available symbols
        cleared = {}
        try:
            if hasattr(nandu_brain, "classification_cache"):
                nandu_brain.classification_cache.clear()
                cleared["classification_cache"] = True
        except Exception:
            cleared["classification_cache"] = False
        try:
            if hasattr(nandu_brain, "_rate_limiter"):
                nandu_brain._rate_limiter.clear()
                cleared["rate_limiter"] = True
        except Exception:
            cleared["rate_limiter"] = False
        
        # Log admin activity
        nandu_brain.audit_log_admin_activity(
            "cache_clear", 
            {"cleared_items": cleared, "processing_time_ms": round((time.time() - start_time) * 1000, 2)},
            admin_user="admin",
            client_ip=client_ip
        )
        
        return {"ok": True, "cleared": cleared}
    except Exception as e:
        logger.exception("Clear cache failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/upload/general-queries")
async def admin_upload_general_queries(
    request: Request,
    file: UploadFile = File(...),
    rebuild: bool = Form(False)
):
    """Upload general_queries.json and optionally rebuild FAISS index."""
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    
    try:
        if file.content_type not in ("application/json", "text/json", "application/octet-stream"):
            raise HTTPException(status_code=400, detail="Invalid content type")
        dest = BASE_DIR / "general_queries.json"
        _save_upload(dest, file)

        # Validate JSON
        try:
            json.loads(dest.read_text(encoding="utf-8"))
        except Exception as ve:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {ve}")

        rebuild_ok = None
        output = ""
        if rebuild:
            rebuild_ok, output = _run_script([sys.executable, "build_general_queries_index.py"])
        
        # Log admin activity
        nandu_brain.audit_log_admin_activity(
            "file_upload", 
            {
                "file_type": "general_queries.json",
                "file_size": dest.stat().st_size,
                "rebuild_requested": rebuild,
                "rebuild_success": rebuild_ok,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            },
            admin_user="admin",
            client_ip=client_ip
        )
        
        return {"ok": True, "rebuild_ok": rebuild_ok, "output": output}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload general queries failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/upload/catalogue-csv")
async def admin_upload_catalogue_csv(
    request: Request,
    file: UploadFile = File(...),
    rebuild: bool = Form(True)
):
    """Upload catalogue.csv and optionally rebuild FAISS index."""
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Please upload a .csv file")
        dest = BASE_DIR / "catalogue.csv"
        _save_upload(dest, file)

        rebuild_ok = None
        output = ""
        if rebuild:
            # Build from CSV
            rebuild_ok, output = _run_script([sys.executable, "catalogue_indexer.py"])
        
        # Log admin activity
        nandu_brain.audit_log_admin_activity(
            "file_upload", 
            {
                "file_type": "catalogue.csv",
                "file_size": dest.stat().st_size,
                "rebuild_requested": rebuild,
                "rebuild_success": rebuild_ok,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            },
            admin_user="admin",
            client_ip=client_ip
        )
        
        return {"ok": True, "rebuild_ok": rebuild_ok, "output": output}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload catalogue CSV failed")
        raise HTTPException(status_code=500, detail=str(e))


class RebuildRequest(BaseModel):
    index: str  # "general" | "catalogue"


@app.post("/admin/rebuild")
async def admin_rebuild(request: Request, req: RebuildRequest):
    """Rebuild FAISS indices on demand."""
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    
    index = req.index.strip().lower()
    if index not in ("general", "catalogue"):
        raise HTTPException(status_code=400, detail="index must be 'general' or 'catalogue'")
    
    if index == "general":
        ok, out = _run_script([sys.executable, "build_general_queries_index.py"])
    else:
        # Ensure CSV exists; if not, try to export from DB first
        csv_path = BASE_DIR / "catalogue.csv"
        if not csv_path.exists():
            _run_script([sys.executable, "export_catalogue_to_csv.py"])  # ignore result; may not exist
        ok, out = _run_script([sys.executable, "catalogue_indexer.py"])
    
    # Log admin activity
    nandu_brain.audit_log_admin_activity(
        "faiss_rebuild", 
        {
            "index_type": index,
            "rebuild_success": ok,
            "output_length": len(out),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        },
        admin_user="admin",
        client_ip=client_ip
    )
    
    return {"ok": ok, "output": out}


@app.get("/admin/log-activity")
async def admin_log_activity(request: Request, data: str = None):
    """Log admin activity from PHP frontend."""
    try:
        if not data:
            return {"ok": False, "error": "No data provided"}
        
        # Parse the JSON data
        activity_data = json.loads(data)
        
        # Extract fields
        activity = activity_data.get("activity", "unknown")
        details = activity_data.get("details", {})
        admin_user = activity_data.get("admin_user", "admin")
        client_ip = activity_data.get("client_ip", request.client.host if request.client else "unknown")
        
        # Log using the backend function
        nandu_brain.audit_log_admin_activity(
            activity, 
            details,
            admin_user=admin_user,
            client_ip=client_ip
        )
        
        return {"ok": True}
    except Exception as e:
        logger.exception("Admin activity logging failed")
        return {"ok": False, "error": str(e)}

@app.get("/admin/index-status")
async def admin_index_status(request: Request):
    """Return presence, size and mtime for FAISS indices and data files."""
    client_ip = request.client.host if request.client else "unknown"
    
    def info(p: Path):
        if not p.exists():
            return {"exists": False}
        return {
            "exists": True,
            "size": p.stat().st_size,
            "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
        }

    payload = {
        "catalogue_index": info(BASE_DIR / "catalogue_index.faiss"),
        "general_index": info(BASE_DIR / "general_queries_index.faiss"),
        "general_queries": info(BASE_DIR / "general_queries.json"),
        "catalogue_csv": info(BASE_DIR / "catalogue.csv"),
        "catalogue_db": info(BASE_DIR / "catalogue.db"),
    }
    
    # Log admin activity (status check)
    nandu_brain.audit_log_admin_activity(
        "status_check", 
        {
            "checked_files": list(payload.keys()),
            "existing_files": [k for k, v in payload.items() if v.get("exists", False)]
        },
        admin_user="admin",
        client_ip=client_ip
    )
    
    return payload

@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring
    
    Response:
        {
            "status": "healthy",
            "checks": {
                "database": true,
                "faiss_index": true,
                "general_queries": true
            }
        }
    """
    try:
        # Simple health check - just verify imports work
        import os
        checks = {
            "database": os.path.exists("catalogue.db"),
            "nandu_brain": True,  # If we got here, import worked
            "api_server": True
        }
        
        return {
            "status": "healthy" if all(checks.values()) else "degraded",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stats")
async def stats():
    """
    Get server statistics
    
    Response:
        {
            "total_clients": 5,
            "error_count": 2,
            "cache_size": 45
        }
    """
    try:
        return {
            "total_clients": len(nandu_brain._rate_limiter),
            "error_count": nandu_brain._error_tracker["count"],
            "classification_cache_size": len(nandu_brain.classification_cache),
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """
    Simple HTML test page for direct API testing
    Access at: http://localhost:8000/test
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Nalanda Library Chatbot API Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #1976d2; }
        .input-group {
            margin: 20px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        input, select, button {
            padding: 10px;
            font-size: 16px;
            margin: 5px;
        }
        #query {
            width: 60%;
        }
        #mode {
            width: 20%;
        }
        button {
            background: #1976d2;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        button:hover {
            background: #1565c0;
        }
        #response {
            margin-top: 20px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            white-space: pre-wrap;
            min-height: 100px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .loading {
            color: #666;
            font-style: italic;
        }
        .error {
            color: #d32f2f;
        }
        .success {
            color: #388e3c;
        }
        .quick-tests {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .quick-tests a {
            display: inline-block;
            margin: 5px;
            padding: 8px 15px;
            background: #e3f2fd;
            color: #1976d2;
            text-decoration: none;
            border-radius: 5px;
        }
        .quick-tests a:hover {
            background: #bbdefb;
        }
    </style>
</head>
<body>
    <h1>🤖 Nalanda Library Chatbot API Test</h1>
    <p>Test the chatbot API directly from your browser</p>
    
    <div class="input-group">
        <input type="text" id="query" placeholder="Enter your query (e.g., python books)..." />
        <select id="mode">
            <option value="auto">Auto</option>
            <option value="books">Books Only</option>
            <option value="library">Library Info</option>
            <option value="website">Website</option>
        </select>
        <button onclick="sendQuery()">Send</button>
    </div>
    
    <div id="response">Response will appear here...</div>
    
    <div class="quick-tests">
        <h3>Quick Test Queries:</h3>
        <a href="#" onclick="testQuery('machine learning books'); return false;">📚 ML Books</a>
        <a href="#" onclick="testQuery('library timings'); return false;">⏰ Library Hours</a>
        <a href="#" onclick="testQuery('books by Stephen Hawking'); return false;">👤 Author Search</a>
        <a href="#" onclick="testQuery('how many books can students borrow'); return false;">❓ Borrowing Rules</a>
        <a href="#" onclick="testQuery('fine policy'); return false;">💵 Fines</a>
    </div>
    
    <script>
        function testQuery(q) {
            document.getElementById('query').value = q;
            sendQuery();
        }
        
        async function sendQuery() {
            const query = document.getElementById('query').value;
            const mode = document.getElementById('mode').value;
            const responseDiv = document.getElementById('response');
            
            if (!query.trim()) {
                responseDiv.innerHTML = '<span class="error">Please enter a query</span>';
                return;
            }
            
            responseDiv.innerHTML = '<span class="loading">⏳ Processing...</span>';
            
            try {
                const startTime = performance.now();
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: query,
                        search_mode: mode
                    })
                });
                
                const data = await response.json();
                const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
                
                if (data.success) {
                    responseDiv.innerHTML = 
                        '<span class="success">✅ Success (' + elapsed + 's)</span>\\n\\n' +
                        data.response;
                } else {
                    responseDiv.innerHTML = 
                        '<span class="error">❌ Error</span>\\n\\n' +
                        (data.error || 'Unknown error');
                }
                
            } catch (error) {
                responseDiv.innerHTML = 
                    '<span class="error">❌ Connection Error</span>\\n\\n' +
                    error.message;
            }
        }
        
        // Allow Enter key to send
        document.getElementById('query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendQuery();
        });
    </script>
</body>
</html>
    """

@app.get("/")
async def root():
    """API documentation homepage"""
    return {
    "name": "Nalanda Library Chatbot API - PHP Integration",
        "version": "1.0.0",
        "description": "Library chatbot backend for IIT Ropar",
        "endpoints": {
            "/chat": "POST - Main chat endpoint (send queries here)",
            "/health": "GET - Health check",
            "/stats": "GET - Server statistics",
            "/test": "GET - HTML test page",
            "/admin/clear-cache": "POST - Clear backend caches",
            "/admin/upload/general-queries": "POST (multipart) - Upload general_queries.json and optionally rebuild",
            "/admin/upload/catalogue-csv": "POST (multipart) - Upload catalogue.csv and optionally rebuild",
            "/admin/rebuild": "POST - Rebuild indices (general|catalogue)",
            "/admin/index-status": "GET - Index and data files status",
            "/docs": "GET - Interactive API documentation (Swagger UI)"
        },
        "status": "running",
        "test_url": "http://localhost:8000/test",
        "note": "This is a local testing server for PHP frontend integration"
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Starting Nalanda Library Chatbot API Server - PHP Integration")
    print("=" * 60)
    print("API Docs: http://localhost:8000/docs")
    print("Test Page: http://localhost:8000/test")
    print("Health Check: http://localhost:8000/health")
    print("=" * 60)
    print("WARNING: Make sure to copy required files from main project:")
    print("   - nandu_brain.py")
    print("   - formatters.py")
    print("   - catalogue.db")
    print("   - general_queries.json")
    print("   - models/ folder")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
