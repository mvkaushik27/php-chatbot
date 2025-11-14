<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IIT Ropar Library - Nalanda Library Chatbot</title>
    <link rel="stylesheet" href="assets/css/chatbot.css">
</head>
<body>
    <div class="container">
        <header>
            <h1><img src="assets/iit_ropar_logo.png" alt="IIT Ropar" style="height: 40px; vertical-align: middle; margin-right: 12px;"> IIT Ropar Library</h1>
            <p>Welcome to the Nalanda Library Assistance System</p>
        </header>
        
        <main>
            <div class="library-info">
                <h2>Library Information</h2>
                <p>The Central Library at IIT Ropar provides access to thousands of books, journals, and digital resources for students, faculty, and researchers.</p>
                
                <div class="quick-links">
                    <a href="https://opac.iitrpr.ac.in" target="_blank">📖 OPAC</a>
                    <a href="https://www.iitrpr.ac.in/library/" target="_blank">🌐 Library Website</a>
                    <a href="mailto:libraryhelpdesk@iitrpr.ac.in">✉️ Contact Us</a>
                </div>
                
                <div class="features">
                    <h3>Library Features</h3>
                    <ul>
                        <li>🔍 Extensive collection of books, journals, and e-resources</li>
                        <li>📱 24/7 access to digital library</li>
                        <li>💻 Online catalogue (OPAC) for searching books</li>
                        <li>🎓 Study spaces and reading rooms</li>
                        <li>🔬 Access to research databases (Scopus, IEEE, ACM, etc.)</li>
                    </ul>
                </div>
            </div>
            
            <!-- Chatbot Widget -->
            <div class="chatbot-widget">
                <button id="chat-toggle" class="chat-toggle-btn" aria-label="Open chat">
                    💬 Chat with Nalanda Library Chatbot
                </button>
                
                <div id="chat-window" class="chat-window" style="display: none;">
                    <div class="chat-header">
                        <h3><img src="assets/iit_ropar_logo.png" alt="IIT Ropar" style="height: 24px; vertical-align: middle; margin-right: 8px;"> Nalanda Library Chatbot</h3>
                        <button id="chat-close" class="chat-close-btn" aria-label="Close chat">×</button>
                    </div>
                    
                    <div class="chat-messages" id="chat-messages">
                        <div class="message bot-message">
                            <strong>Nalanda Library Chatbot:</strong>
                            <p>Hello! I'm your library assistant. I can help you:</p>
                            <ul>
                                <li>🔍 Search for books by title, author, or subject</li>
                                <li>⏰ Check library hours and policies</li>
                                <li>📖 Learn about borrowing rules and fine policies</li>
                                <li>💡 Answer questions about library services</li>
                            </ul>
                            <p>Try these quick queries:</p>
                            <div class="quick-queries">
                                <button class="quick-query-btn" data-query="library hours">Library Hours</button>
                                <button class="quick-query-btn" data-query="reading facilities">Reading Facilities</button>
                                <button class="quick-query-btn" data-query="technobooth">Technobooth</button>
                                <button class="quick-query-btn" data-query="fine policy">Fine Policy</button>
                                <button class="quick-query-btn" data-query="issue books">Issue Books</button>
                                <button class="quick-query-btn" data-query="e resources">E-Resources</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chat-input-container">
                        <select id="search-mode" class="search-mode-select" aria-label="Search mode">
                            <option value="auto">Auto</option>
                            <option value="books">Books Only</option>
                            <option value="library">Library Info</option>
                        </select>
                        <input 
                            type="text" 
                            id="chat-input" 
                            class="chat-input" 
                            placeholder="Ask about books, policies, or library services..."
                            maxlength="300"
                            aria-label="Chat message"
                        />
                        <button id="chat-send" class="chat-send-btn" aria-label="Send message">Send</button>
                    </div>
                </div>
            </div>
        </main>
        
        <footer>
            <p>&copy; 2025 IIT Ropar Library | Powered by Nalanda Library Chatbot</p>
            <p class="server-info">Local Testing Mode - PHP Frontend + Python Backend</p>
        </footer>
    </div>
    
    <script src="assets/js/chatbot.js"></script>
</body>
</html>

