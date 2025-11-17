/**
 * Chatbot Frontend Logic
 * Handles UI interactions and communication with PHP backend
 */

(function() {
    'use strict';
    
    // DOM Elements
    const chatToggle = document.getElementById('chat-toggle');
    const chatClose = document.getElementById('chat-close');
    const chatWindow = document.getElementById('chat-window');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const searchMode = document.getElementById('search-mode');
    
    // State
    let isOpen = false;
    let isProcessing = false;
    let messageCount = 0;
    
    // Initialize
    function init() {
        // Event listeners
        chatToggle.addEventListener('click', toggleChat);
        chatClose.addEventListener('click', toggleChat);
        chatSend.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', handleKeyPress);
        
        // Quick query buttons
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('quick-query-btn')) {
                const query = e.target.getAttribute('data-query');
                if (query) {
                    chatInput.value = query;
                    sendMessage();
                }
            }
        });
        
        // Focus input when chat opens
        chatWindow.addEventListener('transitionend', function() {
            if (isOpen) {
                chatInput.focus();
            }
        });
        
    console.log('Nalanda Library Chatbot initialized');
    }
    
    // Toggle chat window
    function toggleChat() {
        isOpen = !isOpen;
        chatWindow.style.display = isOpen ? 'flex' : 'none';
        
        if (isOpen) {
            chatInput.focus();
            chatToggle.textContent = '✕ Close Chat';
        } else {
            chatToggle.textContent = '💬 Ask Chatbot';
        }
    }
    
    // Handle Enter key press
    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }
    
    // Send message to backend
    async function sendMessage() {
        const query = chatInput.value.trim();
        
        if (!query || isProcessing) return;
        
        // Validate input length
        if (query.length > 300) {
            addMessage('Query too long. Please limit to 300 characters.', 'bot', 'error');
            return;
        }
        
        // Add user message to chat
        addMessage(query, 'user');
        chatInput.value = '';
        messageCount++;
        
        // Show loading indicator
        const loadingId = addMessage('Thinking...', 'bot', 'loading');
        isProcessing = true;
        
        try {
            // Send to PHP backend
            const startTime = performance.now();
            const response = await fetch('api/chat_handler.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    search_mode: searchMode.value
                })
            });
            
            const data = await response.json();
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
            
            // Remove loading message
            removeMessage(loadingId);
            
            if (data.success) {
                // Add bot response
                addMessage(data.response, 'bot');
                
                // Log processing time
                console.log(`Query "${query.substring(0, 30)}..." processed in ${elapsed}s (backend: ${data.processing_time?.toFixed(2) || '?'}s)`);
            } else {
                // Show error
                const errorMsg = data.error || 'Sorry, I encountered an error. Please try again.';
                addMessage(errorMsg, 'bot', 'error');
                
                // Show debug info in console
                if (data.debug) {
                    console.error('Backend error:', data.debug);
                }
            }
            
        } catch (error) {
            console.error('Network error:', error);
            removeMessage(loadingId);
            
            let errorMsg = '❌ Connection error. ';
            if (error.message.includes('Failed to fetch')) {
                errorMsg += 'Please check if the Python backend is running on http://localhost:8000';
            } else {
                errorMsg += error.message;
            }
            
            addMessage(errorMsg, 'bot', 'error');
        } finally {
            isProcessing = false;
        }
    }
    
    // Add message to chat
    function addMessage(text, sender, className = '') {
        const messageDiv = document.createElement('div');
        const messageId = 'msg-' + Date.now() + '-' + Math.random();
        messageDiv.id = messageId;
        messageDiv.className = `message ${sender}-message ${className}`;
        
        if (sender === 'bot') {
            messageDiv.innerHTML = `<strong>Nalanda Library Chatbot:</strong><div class="message-content">${formatBotMessage(text)}</div>`;
        } else {
            messageDiv.innerHTML = `<strong>You:</strong><div class="message-content">${escapeHtml(text)}</div>`;
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Smooth scroll to bottom
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
        
        return messageId;
    }
    
    // Remove message from chat
    function removeMessage(messageId) {
        const msg = document.getElementById(messageId);
        if (msg) {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        }
    }
    
    // Format bot message (handle markdown-like syntax and JSON blocks)
    function formatBotMessage(text) {
        // Check if the message contains a JSON code block
        const jsonMatch = text.match(/```json\s*\n([\s\S]*?)\n```/);
        
        if (jsonMatch) {
            try {
                const jsonData = JSON.parse(jsonMatch[1]);
                
                // Handle both array format and object with books property
                let books = [];
                if (Array.isArray(jsonData)) {
                    books = jsonData;
                } else if (jsonData.books && Array.isArray(jsonData.books)) {
                    books = jsonData.books;
                }
                
                // If we have books data
                if (books.length > 0) {
                    return formatBookResults(books, text);
                }
            } catch (e) {
                console.error('Failed to parse JSON block:', e);
                // Fall through to normal formatting
            }
        }
        
        // Check if text already contains HTML tags (from backend)
        const hasHtmlTags = /<[^>]+>/.test(text);
        
        if (hasHtmlTags) {
            // Text already contains HTML from backend, return as-is
            return text;
        } else {
            // Text is plain text or markdown, process it
            // Escape HTML first
            text = escapeHtml(text);
            
            // Convert **bold** to <strong>
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            // Convert *italic* to <em>
            text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
            
            // Convert [text](url) to links
            text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
            
            // Convert line breaks
            text = text.replace(/\n/g, '<br>');
            
            // Convert bullet points
            text = text.replace(/^[•·●] (.+)$/gm, '<li>$1</li>');
            text = text.replace(/(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/gs, '<ul>$1</ul>');
            
            // Convert numbered lists
            text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
            
            return text;
        }
    }
    
    // Format book results from JSON data
    function formatBookResults(books, originalText) {
        // Extract intro text before JSON block
        const introMatch = originalText.match(/^(.*?)```json/s);
        let html = '';
        
        if (introMatch && introMatch[1].trim()) {
            const intro = escapeHtml(introMatch[1].trim());
            html += `<p>${intro.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}</p>`;
        }

        html += '<div class="book-results">';
        
        // Check if this is progressive disclosure format
        let booksToShow = books;
        let hasMore = false;
        let allBooks = [];
        
        if (books && typeof books === 'object' && books.initial_books) {
            // Progressive disclosure format
            booksToShow = books.initial_books;
            allBooks = books.all_books;
            hasMore = books.has_more;
        } else if (Array.isArray(books)) {
            booksToShow = books;
        }
        
        // Create a table-like layout with availability in separate column
        html += '<div class="book-list" id="initial-books">';
        
        booksToShow.forEach((book, index) => {
            // Get availability status
            const availability = book.availability || {};
            const status = availability.status || 'unknown';
            const available = availability.available_copies || 0;
            const total = availability.total_copies || 0;
            
            let availabilityText = '';
            let availabilityClass = 'unknown';
            
            if (status === 'available') {
                availabilityText = `📚 Available (${available}/${total})`;
                availabilityClass = 'available';
            } else if (status === 'issued') {
                availabilityText = `📖 Issued (${available}/${total})`;
                availabilityClass = 'issued';
            } else {
                availabilityText = '❓ Status Unknown';
                availabilityClass = 'unknown';
            }
            
            const safeTitle = escapeHtml(book.title);
            const safeAuthor = book.author ? escapeHtml(book.author) : '';
            const safeYear = book.year ? escapeHtml(book.year) : '';
            const safeIsbn = book.isbn ? escapeHtml(book.isbn) : '';
            const safeCopies = book.copies ? escapeHtml(book.copies) : '';
            const safeCallNumbers = book.call_numbers && book.call_numbers.length ? escapeHtml(book.call_numbers.join(', ')) : '';
            const safeAccessions = book.accessions && book.accessions.length ? escapeHtml(book.accessions.join(', ')) : '';
            
            html += `
                <div class="book-card">
                    <div class="book-main">
                        <div class="book-info">
                            <div class="book-title">${safeTitle}</div>
                            ${safeAuthor ? `<div class="book-author">by ${safeAuthor}</div>` : ''}
                            <div class="book-meta">
                                ${safeYear ? `<span>📅 ${safeYear}</span>` : ''}
                                ${safeIsbn ? `<span>📖 ISBN: ${safeIsbn}</span>` : ''}
                                ${safeCopies ? `<span>📚 Copies: ${safeCopies}</span>` : ''}
                            </div>
                            ${safeCallNumbers ? `<div class="book-details"><strong>Call Number:</strong> ${safeCallNumbers}</div>` : ''}
                            ${safeAccessions ? `<div class="book-details"><strong>Accession #:</strong> ${safeAccessions}</div>` : ''}
                            
                            ${book.item_details && book.item_details.length ? `
                                <div class="item-details-section">
                                    <div class="item-details-header">📋 Item Details:</div>
                                    ${book.item_details.map(item => {
                                        const safeItemType = escapeHtml(item.item_type);
                                        const safeCollection = item.collection !== 'Unknown' ? escapeHtml(item.collection) : '';
                                        const safeDueDate = item.due_date ? escapeHtml(item.due_date) : '';
                                        const safeBarcode = item.barcode ? escapeHtml(item.barcode) : '';
                                        const statusClass = item.status === 'Available' ? 'available' : item.status === 'Checked out' ? 'checked-out' : 'other';
                                        
                                        return `
                                        <div class="item-detail">
                                            <div class="item-header">
                                                <span class="item-type">${safeItemType} ${safeCollection ? `(${safeCollection})` : ''}</span>
                                                <span class="item-status ${statusClass}">${item.status}</span>
                                            </div>
                                            ${safeDueDate && item.status === 'Checked out' ? `<div class="item-due-date">📅 Due: ${safeDueDate}</div>` : ''}
                                            ${safeBarcode ? `<div class="item-barcode">🏷️ Barcode: ${safeBarcode}</div>` : ''}
                                        </div>`;
                                    }).join('')}
                                </div>
                            ` : ''}
                            
                            ${book.summary ? `<div class="book-summary">${escapeHtml(book.summary)}</div>` : ''}
                        </div>
                        <div class="book-availability">
                            <div class="availability-status ${availabilityClass}">
                                ${availabilityText}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>'; // Close book-list
        
        // Add "Show More" button if there are more books available
        if (hasMore && allBooks && allBooks.length > booksToShow.length) {
            const remainingCount = allBooks.length - booksToShow.length;
            html += `
                <div class="show-more-section" style="text-align: center; margin: 15px 0;">
                    <button class="show-more-btn" onclick="showMoreBooks()" 
                            style="background: #10b981; color: white; border: none; padding: 10px 20px; 
                                   border-radius: 6px; cursor: pointer; font-weight: 500;">
                        📚 Show ${remainingCount} More Books
                    </button>
                </div>
                <div class="additional-books" id="additional-books" style="display: none;">
                    <div class="book-list">
            `;
            
            // Add the additional books (hidden initially)
            const additionalBooks = allBooks.slice(booksToShow.length);
            additionalBooks.forEach((book, index) => {
                // Get availability status
                const availability = book.availability || {};
                const status = availability.status || 'unknown';
                const available = availability.available_copies || 0;
                const total = availability.total_copies || 0;
                
                let availabilityText = '';
                let availabilityClass = 'unknown';
                
                if (status === 'available') {
                    availabilityText = `📚 Available (${available}/${total})`;
                    availabilityClass = 'available';
                } else if (status === 'issued') {
                    availabilityText = `📖 Issued (${available}/${total})`;
                    availabilityClass = 'issued';
                } else {
                    availabilityText = '❓ Status Unknown';
                    availabilityClass = 'unknown';
                }
                
                const safeTitle = escapeHtml(book.title);
                const safeAuthor = book.author ? escapeHtml(book.author) : '';
                const safeYear = book.year ? escapeHtml(book.year) : '';
                const safeIsbn = book.isbn ? escapeHtml(book.isbn) : '';
                const safeCopies = book.copies ? escapeHtml(book.copies) : '';
                const safeCallNumbers = book.call_numbers && book.call_numbers.length ? escapeHtml(book.call_numbers.join(', ')) : '';
                const safeAccessions = book.accessions && book.accessions.length ? escapeHtml(book.accessions.join(', ')) : '';
                
                html += `
                    <div class="book-card">
                        <div class="book-main">
                            <div class="book-info">
                                <div class="book-title">${safeTitle}</div>
                                ${safeAuthor ? `<div class="book-author">by ${safeAuthor}</div>` : ''}
                                <div class="book-meta">
                                    ${safeYear ? `<span>📅 ${safeYear}</span>` : ''}
                                    ${safeIsbn ? `<span>📖 ISBN: ${safeIsbn}</span>` : ''}
                                    ${safeCopies ? `<span>📚 Copies: ${safeCopies}</span>` : ''}
                                </div>
                                ${safeCallNumbers ? `<div class="book-details"><strong>Call Number:</strong> ${safeCallNumbers}</div>` : ''}
                                ${safeAccessions ? `<div class="book-details"><strong>Accession #:</strong> ${safeAccessions}</div>` : ''}
                            </div>
                        </div>
                        <div class="book-availability">
                            <div class="availability-status ${availabilityClass}">
                                ${availabilityText}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>'; // Close additional-books book-list
        }
        
        html += '</div>'; // Close book-results
        
        // Add footer note if present
        const footerMatch = originalText.match(/```\s*\n(.*)$/s);
        if (footerMatch && footerMatch[1].trim()) {
            const footer = escapeHtml(footerMatch[1].trim());
            html += `<p style="margin-top: 10px; font-size: 13px; color: #666;">${footer.replace(/\*\*(.*?)\*\*/g, '<em>$1</em>')}</p>`;
        }

        return html;
    }
    
    // Show more books functionality
    window.showMoreBooks = function() {
        const additionalBooksDiv = document.getElementById('additional-books');
        const showMoreSection = document.querySelector('.show-more-section');
        
        if (additionalBooksDiv && showMoreSection) {
            additionalBooksDiv.style.display = 'block';
            showMoreSection.style.display = 'none';
            
            // Smooth scroll to the additional books
            additionalBooksDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };
    
    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Character counter for input
    chatInput.addEventListener('input', function() {
        const remaining = 300 - this.value.length;
        if (remaining < 50) {
            this.style.borderColor = remaining < 0 ? '#d32f2f' : '#ff9800';
        } else {
            this.style.borderColor = '';
        }
    });
    
    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
