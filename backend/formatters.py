"""
Enhanced formatters for Nandu Library Assistant
Handles book results and general queries with improved layout
"""

import html
import requests
import logging
import os
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Load CSS dynamically
STATIC_DIR = Path(__file__).parent / "static"
CSS_FILE = STATIC_DIR / "styles.css"

def get_css():
    """Load custom CSS styles from /static/styles.css"""
    if CSS_FILE.exists():
        with open(CSS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def safe_str(value, default=""):
    """Convert value to string safely."""
    if value is None:
        return default
    try:
        # Handle scientific notation for ISBNs
        if isinstance(value, (int, float)):
            return f"{value:.0f}"  # Convert to regular number without scientific notation
        s = str(value).strip()
        if 'e' in s.lower():  # Handle string containing scientific notation
            try:
                return f"{float(s):.0f}"
            except ValueError:
                pass
        return s if s and s.lower() not in ('nan', 'none', '') else default
    except Exception:
        return default

def get_cover_url(isbn):
    """Get book cover URL with caching and fallback."""
    if not isbn or str(isbn).lower() in ('nan', 'none', '', '0'):
        return "https://via.placeholder.com/128x180/cccccc/666666?text=No+Cover"

    # Handle scientific notation in ISBN
    try:
        if 'e' in str(isbn).lower():
            isbn = f"{float(isbn):.0f}"  # Convert scientific notation to regular number
        isbn = ''.join(c for c in str(isbn) if c.isdigit())
    except Exception as e:
        logger.warning(f"Failed to process ISBN {isbn}: {e}")
        return "https://via.placeholder.com/128x180/cccccc/666666?text=No+Cover"

    # First check bundled assets (assets/covers) which in this repo use ISBN filenames
    # Support common image extensions
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        assets_file = Path("assets") / "covers" / f"{isbn}{ext}"
        if assets_file.exists():
            logger.debug(f"Using bundled asset cover for ISBN {isbn} ({ext})")
            try:
                import base64
                with open(assets_file, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else ("image/png" if ext == ".png" else "image/webp")
                    return f"data:{mime};base64,{img_data}"
            except Exception as e:
                logger.warning(f"Failed to encode asset image {isbn}{ext}: {e}")

    # Check if cover image is already cached - convert to base64 for Streamlit HTML
    cache_dir = Path("cache/covers")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{isbn}.jpg"

    if cache_file.exists():
        logger.debug(f"Using cached cover for ISBN {isbn}")
        try:
            import base64
            with open(cache_file, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
                return f"data:image/jpeg;base64,{img_data}"
        except Exception as e:
            logger.warning(f"Failed to encode cached image {isbn}: {e}")

    # Try to get cover from OpenLibrary (optimized: skip HEAD request, just return URL)
    # OpenLibrary will return a 1x1 placeholder if cover doesn't exist, which is acceptable
    # This avoids slow network requests that block rendering (3s timeout per book!)
    url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
    logger.debug(f"Using OpenLibrary URL for ISBN {isbn}")
    return url

def render_error_card(message):
    """Render an error card with a custom message."""
    return ''.join([
        '<div class="book-card error">',
        '<div class="book-info">',
        '<h4>Error displaying book</h4>',
        f'<p>{html.escape(message)}</p>',
        '</div>',
        '</div>'
    ])

def render_book_card(book):
    """Render a book card with error handling and validation."""
    if not isinstance(book, dict):
        logger.error(f"Invalid book data type: {type(book)}")
        return render_error_card("Invalid book data format")
    
    try:
        # Process fields with validation
        data = {}
        
        # Text fields
        text_fields = {
            'title': ('Title', 'title', 'Untitled'),
            'author': ('Author', 'author', 'Unknown Author'),
            'publisher': ('Publisher', 'publishercode', ''),
            'year': ('Year', 'copyrightdate', ''),
            'isbn': ('ISBN', 'isbn', '')
        }
        
        for key, (primary, fallback, default) in text_fields.items():
            data[key] = safe_str(book.get(primary, book.get(fallback)), default)
        
        # Numeric fields with validation
        try:
            data['copies'] = max(1, int(book.get('copies', 1)))
        except (ValueError, TypeError) as e:
            logger.warning(f"Error in copies field: {e}")
            data['copies'] = 1
        
        # List fields with validation
        for field in ['call_numbers', 'accessions']:
            value = book.get(field, [])
            if not isinstance(value, list):
                value = [value]
            data[field] = [safe_str(x) for x in value if x]
            data[f'{field}_display'] = ', '.join(data[field]) or 'N/A'
        
        # Get cover URL with validation
        try:
            data['cover_url'] = get_cover_url(data['isbn'])
            if not data['cover_url']:
                raise ValueError("Empty cover URL returned")
        except Exception as e:
            logger.warning(f"Cover fetch failed for {data['isbn']}: {e}")
            data['cover_url'] = "uploads/no_cover.jpg"
        
        # Build HTML
        html_parts = []
        
        # Base card structure
        html_parts.extend([
            '<div class="book-card">',
            '<div class="book-cover">',
            f'<img src="{data["cover_url"]}" alt="Book cover for {html.escape(data["title"])}">',
            '</div>',
            '<div class="book-info">',
            f'<h4>{html.escape(data["title"])}</h4>',
            f'<p><b>Author:</b> {html.escape(data["author"])}</p>'
        ])
        
        # Published info (if available)
        if data['publisher'] or data['year']:
            pub_parts = []
            if data['publisher']:
                pub_parts.append(html.escape(data['publisher']))
            if data['year']:
                pub_parts.append(f"({html.escape(data['year'])})")
            html_parts.append(f'<p><b>Published:</b> {" ".join(pub_parts)}</p>')
        
        # ISBN (if available)
        if data['isbn']:
            html_parts.append(f'<p><b>ISBN:</b> {html.escape(data["isbn"])}</p>')
        
        # Metadata section
        html_parts.append('<div class="book-meta">')
        
        # Display copies count
        html_parts.append(f'<span><b>Copies:</b> {data["copies"]}</span>')
        
        # Display OPAC availability (real-time from library system)
        opac_availability = book.get('opac_availability')
        if opac_availability:
            status = opac_availability.get('status', 'unknown')
            available = opac_availability.get('available_copies', 0)
            total = opac_availability.get('total_copies', 0)
            
            if status == 'available':
                status_html = f'<span class="availability available">📚 Available ({available}/{total})</span>'
            elif status == 'issued':
                status_html = f'<span class="availability issued">📖 Issued ({available}/{total})</span>'
                
                # Add due date information for issued books
                details = opac_availability.get('details', [])
                due_dates = []
                for detail in details:
                    items = detail.get('items', [])
                    for item in items:
                        if item.get('status', '').lower() in ['checked out', 'issued'] and item.get('due_date'):
                            due_dates.append(item['due_date'])
                
                if due_dates:
                    # Remove duplicates and sort
                    unique_due_dates = sorted(list(set(due_dates)))
                    if len(unique_due_dates) == 1:
                        status_html += f'<br><span class="due-date" style="font-size: 11px; color: #dc3545;">📅 Due: {html.escape(unique_due_dates[0])}</span>'
                    else:
                        status_html += f'<br><span class="due-date" style="font-size: 11px; color: #dc3545;">📅 Due: {html.escape(", ".join(unique_due_dates[:2]))}</span>'
                        if len(unique_due_dates) > 2:
                            status_html += f'<span style="font-size: 11px; color: #6c757d;"> +{len(unique_due_dates)-2} more</span>'
            else:
                status_html = f'<span class="availability unknown">❓ Status Unknown</span>'
            
            html_parts.append(status_html)
        else:
            # Show that we're checking real-time availability
            html_parts.append('<span class="availability checking">🔄 Checking OPAC availability...</span>')
        
        # Display call numbers (already limited to 2 + ... from merge_duplicates)
        if data.get('call_numbers'):
            call_numbers_display = ', '.join(html.escape(cn) for cn in data['call_numbers'])
            html_parts.append(f'<span><b>Call Numbers:</b> {call_numbers_display}</span>')
        
        html_parts.append('</div>')
        
        # Display detailed accession-level availability information
        if opac_availability and opac_availability.get('details'):
            html_parts.append('<div class="item-details-section" style="margin-top: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px; border: 1px solid #e0e0e0;">')
            html_parts.append('<p style="margin: 0 0 8px 0; font-weight: bold; color: #333;"><b>📋 Accession-Level Status:</b></p>')
            
            for book_detail in opac_availability['details']:
                # Check if this book has detailed item information
                items = book_detail.get('items', [])
                
                if items:
                    # Display each accession with its specific status
                    for item in items:
                        accession = item.get('accession_number', 'Unknown')
                        item_status = item.get('status', 'Unknown')
                        due_date = item.get('due_date', '')
                        
                        # Status styling
                        if item_status.lower() in ['available', 'on shelf']:
                            status_class = 'item-available'
                            status_icon = '🟢'
                            status_style = 'color: #28a745; font-weight: bold;'
                        elif item_status.lower() in ['checked out', 'issued']:
                            status_class = 'item-issued'
                            status_icon = '🔴'
                            status_style = 'color: #dc3545; font-weight: bold;'
                        else:
                            status_class = 'item-unknown'
                            status_icon = '❓'
                            status_style = 'color: #6c757d; font-weight: bold;'
                        
                        html_parts.append('<div class="accession-detail-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding: 6px; background: white; border-radius: 3px; border: 1px solid #e0e0e0;">')
                        html_parts.append(f'<span class="accession-info" style="flex: 1; font-size: 13px; color: #555;"><b>Accession:</b> {html.escape(accession)}</span>')
                        html_parts.append(f'<span class="item-status {status_class}" style="{status_style} font-size: 12px;">{status_icon} {html.escape(item_status)}</span>')
                        html_parts.append('</div>')
                        
                        # Show due date if item is checked out
                        if due_date and item_status.lower() in ['checked out', 'issued']:
                            html_parts.append('<div style="margin-left: 10px; margin-bottom: 8px; font-size: 11px; color: #dc3545; font-weight: bold;">')
                            html_parts.append(f'📅 Due Date: {html.escape(due_date)}')
                            html_parts.append('</div>')
                else:
                    # Fallback to general status display
                    item_type = book_detail.get('item_type', 'Unknown')
                    collection = book_detail.get('collection', 'Unknown')
                    item_status = book_detail.get('status', 'Unknown')
                    barcode = book_detail.get('barcode', '')
                    due_date = book_detail.get('due_date', '')
                    
                    # Status styling
                    if item_status == 'Available':
                        status_class = 'item-available'
                        status_icon = '🟢'
                        status_style = 'color: #28a745; font-weight: bold;'
                    elif item_status == 'Checked out':
                        status_class = 'item-issued'
                        status_icon = '🔴'
                        status_style = 'color: #dc3545; font-weight: bold;'
                    else:
                        status_class = 'item-unknown'
                        status_icon = '❓'
                        status_style = 'color: #6c757d; font-weight: bold;'
                    
                    html_parts.append('<div class="item-detail-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; padding: 4px; background: white; border-radius: 3px; border: 1px solid #e0e0e0;">')
                    html_parts.append(f'<span class="item-info" style="flex: 1; font-size: 13px; color: #555;">{html.escape(item_type)} ({html.escape(collection)})</span>')
                    html_parts.append(f'<span class="item-status {status_class}" style="{status_style} font-size: 12px;">{status_icon} {html.escape(item_status)}</span>')
                    html_parts.append('</div>')
                    
                    # Additional details row
                    if barcode or (due_date and item_status == 'Checked out'):
                        html_parts.append('<div style="margin-left: 10px; font-size: 11px; color: #666; margin-bottom: 6px;">')
                        if barcode:
                            html_parts.append(f'📋 Barcode: {html.escape(barcode)}')
                        if due_date and item_status == 'Checked out':
                            html_parts.append(f' 📅 Due: {html.escape(due_date)}')
                        html_parts.append('</div>')
            
            html_parts.append('</div>')
        
        # Accession numbers (if available)
        if data['accessions']:
            html_parts.extend([
                '<p><b>Accession Numbers:</b></p>',
                f'<div class="accession-list">{html.escape(data["accessions_display"])}</div>'
            ])
        
        # Close card
        html_parts.extend(['</div>', '</div>'])
        
        # Return joined HTML
        return ''.join(html_parts)
        
    except Exception as e:
        logger.error(f"Error rendering book card: {e}")
        return render_error_card(str(e))

def format_answer_structured(answer_dict):
    """Format general query responses with styled layout."""
    if not isinstance(answer_dict, dict):
        if isinstance(answer_dict, str):
            if not answer_dict.strip():
                return ""
            answer_dict = {"Response": answer_dict}
        else:
            return str(answer_dict)

    formatted = '<div class="query-response">'

    for key, value in answer_dict.items():
        if key.lower() in ["intent", "type"]:
            continue

        formatted += f'<div class="query-section">'
        formatted += f'<h4 class="query-header">{html.escape(str(key))}</h4>'

        if isinstance(value, list):
            for item in value:
                formatted += f'<div class="query-point">{html.escape(str(item))}</div>'
        else:
            lines = str(value).split("\n")
            for line in lines:
                if line.strip():
                    formatted += f'<div class="query-point">{html.escape(line.strip())}</div>'

        formatted += "</div>"

    formatted += "</div>"
    return formatted

def format_results(results):
    """
    Format search results into styled HTML cards.
    Shows all results without truncation and properly handles multiple copies.
    """
    if not results:
        return "<p>⚠️ No matching books found.</p>"
        
    logger.info(f"Formatting {len(results)} book results for display")
    
    # Start with result count
    output = ['<div class="search-results">']
    output.append(f'<p class="results-count">📚 Found {len(results)} matching titles</p>')
    
    # Track successful renders
    rendered_count = 0
    for book in results:
        try:
            card_html = render_book_card(book)
            if card_html:
                output.append(card_html)
                rendered_count += 1
        except Exception as e:
            logger.error(f"Error rendering book card: {e}")
            continue
            
    output.append('</div>')
    
    logger.info(f"Successfully rendered {rendered_count} of {len(results)} book cards")
    return "\n".join(output)