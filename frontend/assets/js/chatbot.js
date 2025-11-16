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
        console.log('formatBotMessage called, JSON match found:', !!jsonMatch);
        
        if (jsonMatch) {
            try {
                const jsonData = JSON.parse(jsonMatch[1]);
                console.log('Parsed JSON data:', jsonData);
                
                // Handle both array format and object with books property
                let books = [];
                if (Array.isArray(jsonData)) {
                    books = jsonData;
                    console.log('Found books as array:', books.length);
                } else if (jsonData.books && Array.isArray(jsonData.books)) {
                    books = jsonData.books;
                    console.log('Found books in jsonData.books:', books.length);
                }
                
                // If we have books data
                if (books.length > 0) {
                    console.log('Calling formatBookResults with', books.length, 'books');
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

        html += '<div style="margin-top: 10px;">';
        
        // Create a table-like layout with availability in separate column
        html += '<div style="display: flex; flex-direction: column; gap: 12px;">';
        
        books.forEach((book, index) => {
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
            
            html += `
                <div style="background: #f8f9fa; border-left: 3px solid #ff4b4b; padding: 12px; border-radius: 4px;">
                    <div style="display: flex; gap: 15px; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #262730; margin-bottom: 4px;">${escapeHtml(book.title)}</div>
                            ${book.author ? `<div style="color: #808495; font-size: 14px;">by ${escapeHtml(book.author)}</div>` : ''}
                            <div style="display: flex; gap: 15px; margin-top: 6px; font-size: 13px; color: #666; flex-wrap: wrap;">
                                ${book.year ? `<span>📅 ${escapeHtml(book.year)}</span>` : ''}
                                ${book.isbn ? `<span>📖 ISBN: ${escapeHtml(book.isbn)}</span>` : ''}
                                ${book.copies ? `<span>📚 Copies: ${escapeHtml(book.copies)}</span>` : ''}
                            </div>
                            ${book.call_numbers && book.call_numbers.length ? `<div style="margin-top: 6px; font-size: 13px; color: #555;"><strong>Call Number:</strong> ${escapeHtml(book.call_numbers.join(', '))}</div>` : ''}
                            ${book.accessions && book.accessions.length ? `<div style="margin-top: 4px; font-size: 13px; color: #555;"><strong>Accession #:</strong> ${escapeHtml(book.accessions.join(', '))}</div>` : ''}
                            
                            ${book.item_details && book.item_details.length ? `
                                <div style="margin-top: 8px; padding: 8px; background: #f0f2f6; border-radius: 4px;">
                                    <div style="font-size: 12px; font-weight: 600; color: #262730; margin-bottom: 4px;">📋 Item Details:</div>
                                    ${book.item_details.map(item => `
                                        <div style="font-size: 12px; color: #555; margin-bottom: 4px; padding: 4px; background: #fff; border-radius: 3px; border: 1px solid #e0e0e0;">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                                                <span style="font-weight: 500;">${escapeHtml(item.item_type)} ${item.collection !== 'Unknown' ? `(${escapeHtml(item.collection)})` : ''}</span>
                                                <span style="${item.status === 'Available' ? 'color: #28a745;' : item.status === 'Checked out' ? 'color: #dc3545;' : 'color: #6c757d;'} font-weight: 600;">
                                                    ${item.status}
                                                </span>
                                            </div>
                                            ${item.due_date && item.status === 'Checked out' ? `<div style="font-size: 11px; color: #dc3545; margin-top: 2px;">📅 Due: ${escapeHtml(item.due_date)}</div>` : ''}
                                            ${item.barcode ? `<div style="font-size: 10px; color: #666; font-family: monospace; margin-top: 2px;">🏷️ Barcode: ${escapeHtml(item.barcode)}</div>` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                            
                            ${book.summary ? `<div style="margin-top: 6px; font-size: 13px; color: #666; font-style: italic;">${escapeHtml(book.summary)}</div>` : ''}
                        </div>
                        <div style="flex-shrink: 0; min-width: 140px;">
                            <div class="availability-status ${availabilityClass}" style="
                                padding: 8px 12px;
                                border-radius: 6px;
                                font-weight: 600;
                                font-size: 14px;
                                text-align: center;
                                white-space: nowrap;
                                ${availabilityClass === 'available' ? 'background: #d4edda; color: #155724; border: 1px solid #c3e6cb;' : ''}
                                ${availabilityClass === 'issued' ? 'background: #fff3cd; color: #856404; border: 1px solid #ffeaa7;' : ''}
                                ${availabilityClass === 'unknown' ? 'background: #e2e3e5; color: #383d41; border: 1px solid #d6d8db;' : ''}
                            ">
                                ${availabilityText}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
        
        // Add footer note if present
        const footerMatch = originalText.match(/```\s*\n(.*)$/s);
        if (footerMatch && footerMatch[1].trim()) {
            const footer = escapeHtml(footerMatch[1].trim());
            html += `<p style="margin-top: 10px; font-size: 13px; color: #666;">${footer.replace(/\*\*(.*?)\*\*/g, '<em>$1</em>')}</p>`;
        }

        return html;
    }
    
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
