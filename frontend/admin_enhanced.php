<?php
/**
 * Enhanced Admin Panel for Nalanda Library Chatbot - PHP Integration
 * Full-featured admin interface matching Streamlit UI capabilities
 */

// Configuration
define('ADMIN_USERNAME', 'admin');
define('ADMIN_PASSWORD', 'admin123'); // ⚠️ CRITICAL: CHANGE THIS IN PRODUCTION!
define('GENERAL_QUERIES_FILE', '../backend/general_queries.json');
define('CACHE_DIR', '../backend/cache');
define('CONFIG_FILE', '../backend/.env');
define('MAX_UPLOAD_SIZE', 10 * 1024 * 1024); // 10MB

// Helper function to log admin activity
function logAdminActivity($activity, $details = []) {
    $log_data = json_encode([
        'activity_type' => 'admin_action',
        'activity' => $activity,
        'admin_user' => $_SESSION['admin_user'] ?? 'admin',
        'client_ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
        'timestamp' => date('c'),
        'details' => array_merge($details, ['source' => 'php_admin_panel'])
    ]);
    @file_get_contents('http://localhost:8000/admin/log-activity?data=' . urlencode($log_data));
}

// Helper function to get admin user info
function getAdminInfo() {
    return [
        'admin_user' => $_SESSION['admin_user'] ?? 'admin',
        'client_ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown'
    ];
}

// Function to read OPAC configuration
function getOpacEnabled() {
    if (file_exists(CONFIG_FILE)) {
        $content = file_get_contents(CONFIG_FILE);
        if (preg_match('/NANDU_WEBSCRAPE=([01])/', $content, $matches)) {
            return $matches[1] === '1';
        }
    }
    return false; // Default to disabled
}

// Function to read Book Search configuration
function getBookSearchEnabled() {
    if (file_exists(CONFIG_FILE)) {
        $content = file_get_contents(CONFIG_FILE);
        if (preg_match('/NANDU_BOOK_SEARCH=([01])/', $content, $matches)) {
            return $matches[1] === '1';
        }
    }
    return true; // Default to enabled
}

// Function to set OPAC configuration
function setOpacEnabled($enabled) {
    $envContent = '';
    if (file_exists(CONFIG_FILE)) {
        $envContent = file_get_contents(CONFIG_FILE);
    }
    
    $value = $enabled ? '1' : '0';
    if (preg_match('/NANDU_WEBSCRAPE=/', $envContent)) {
        $envContent = preg_replace('/NANDU_WEBSCRAPE=[01]/', 'NANDU_WEBSCRAPE=' . $value, $envContent);
    } else {
        $envContent .= "\nNANDU_WEBSCRAPE=" . $value . "\n";
    }
    
    return file_put_contents(CONFIG_FILE, $envContent) !== false;
}

// Function to set Book Search configuration
function setBookSearchEnabled($enabled) {
    $envContent = '';
    if (file_exists(CONFIG_FILE)) {
        $envContent = file_get_contents(CONFIG_FILE);
    }
    
    $value = $enabled ? '1' : '0';
    if (preg_match('/NANDU_BOOK_SEARCH=/', $envContent)) {
        $envContent = preg_replace('/NANDU_BOOK_SEARCH=[01]/', 'NANDU_BOOK_SEARCH=' . $value, $envContent);
    } else {
        $envContent .= "\nNANDU_BOOK_SEARCH=" . $value . "\n";
    }
    
    return file_put_contents(CONFIG_FILE, $envContent) !== false;
}

session_start();

// Handle logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: admin_enhanced.php');
    exit;
}

// Handle login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    
    if ($username === ADMIN_USERNAME && $password === ADMIN_PASSWORD) {
        $_SESSION['admin_logged_in'] = true;
        $_SESSION['admin_user'] = $username;
        $_SESSION['login_time'] = time();
    } else {
        $login_error = 'Invalid credentials';
    }
}

// Handle OPAC toggle
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['toggle_opac']) && $_SESSION['admin_logged_in']) {
    $enable_opac = isset($_POST['enable_opac']) && $_POST['enable_opac'] === '1';
    if (setOpacEnabled($enable_opac)) {
        $success_message = 'OPAC search ' . ($enable_opac ? 'enabled' : 'disabled') . ' successfully!';
        
        // Log OPAC configuration change to backend
        logAdminActivity('opac_toggle', [
            'opac_enabled' => $enable_opac,
            'action' => $enable_opac ? 'enabled' : 'disabled'
        ]);
    } else {
        $error_message = 'Failed to update OPAC configuration.';
        
        // Log failed OPAC configuration change
        logAdminActivity('opac_toggle_failed', [
            'attempted_action' => $enable_opac ? 'enable' : 'disable',
            'error' => 'Configuration file write failed'
        ]);
    }
}

// Handle Book Search toggle
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['toggle_book_search']) && $_SESSION['admin_logged_in']) {
    $enable_book_search = isset($_POST['enable_book_search']) && $_POST['enable_book_search'] === '1';
    if (setBookSearchEnabled($enable_book_search)) {
        $success_message = 'Book search ' . ($enable_book_search ? 'enabled' : 'disabled') . ' successfully!';
        
        // Log Book Search configuration change to backend
        logAdminActivity('book_search_toggle', [
            'book_search_enabled' => $enable_book_search,
            'action' => $enable_book_search ? 'enabled' : 'disabled'
        ]);
    } else {
        $error_message = 'Failed to update Book Search configuration.';
        
        // Log failed Book Search configuration change
        logAdminActivity('book_search_toggle_failed', [
            'attempted_action' => $enable_book_search ? 'enable' : 'disable',
            'error' => 'Configuration file write failed'
        ]);
    }
}

// Handle general queries save
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['save_queries']) && $_SESSION['admin_logged_in']) {
    $queries_data = $_POST['queries_json'] ?? '{}';
    try {
        $decoded = json_decode($queries_data, true);
        if ($decoded !== null) {
            file_put_contents(GENERAL_QUERIES_FILE, json_encode($decoded, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

            // Rebuild FAISS index after saving
            $backend_path = realpath(__DIR__ . '/../backend');
            $python_cmd = "cd \"$backend_path\" && python build_general_queries_index.py 2>&1";
            $rebuild_output = shell_exec($python_cmd);

            if (strpos($rebuild_output, 'successfully') !== false || strpos($rebuild_output, 'complete') !== false) {
                $success_message = 'General queries updated and FAISS index rebuilt successfully!';

                // Log successful rebuild
                logAdminActivity('faiss_rebuild_php', [
                    'index_type' => 'general',
                    'rebuild_success' => true,
                    'output_length' => strlen($rebuild_output)
                ]);
            } else {
                $success_message = 'General queries updated but FAISS index rebuild may have failed. Check system logs.';

                // Log failed rebuild
                logAdminActivity('faiss_rebuild_php', [
                    'index_type' => 'general',
                    'rebuild_success' => false,
                    'error_output' => substr($rebuild_output, 0, 500)
                ]);
            }
        } else {
            $error_message = 'Invalid JSON format';
        }
    } catch (Exception $e) {
        $error_message = 'Error saving queries: ' . $e->getMessage();
    }
}

// Handle cache clear
if (isset($_GET['clear_cache']) && $_SESSION['admin_logged_in']) {
    // Call backend API to clear cache
    $clear_result = @file_get_contents('http://localhost:8000/admin/clear-cache');
    if ($clear_result) {
        $success_message = 'Cache cleared successfully!';
        
        // Log admin activity
        logAdminActivity('cache_clear_php');
    } else {
        $error_message = 'Failed to clear cache';
    }
}

// Handle JSON file upload
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['json_file']) && $_SESSION['admin_logged_in']) {
    $json_type = $_POST['json_type'] ?? $_POST['upload_target'] ?? '';
    $file = $_FILES['json_file'];
    $rebuild_after = isset($_POST['rebuild_after_upload']);
    
    if ($file['error'] === UPLOAD_ERR_OK) {
        if ($file['size'] > MAX_UPLOAD_SIZE) {
            $error_message = 'File too large. Maximum size is 10MB.';
        } else {
            $content = file_get_contents($file['tmp_name']);
            $decoded = json_decode($content, true);
            
            if ($decoded !== null) {
                // PHP 7+ compatible switch replacement (avoid match expression)
                $target_path = null;
                if ($json_type === 'general_queries') {
                    $target_path = GENERAL_QUERIES_FILE;
                } elseif ($json_type === 'website_cache') {
                    $target_path = CACHE_DIR . '/website_cache.json';
                } elseif ($json_type === 'website_analysis') {
                    $target_path = CACHE_DIR . '/website_analysis.json';
                } elseif ($json_type === 'catalogue') {
                    $target_path = '../backend/catalogue.json';
                }
                
                if ($target_path && file_put_contents($target_path, $content)) {
                    $success_message = 'File uploaded successfully!';
                    
                    // Log admin activity for file upload
                    logAdminActivity('file_upload_php', [
                        'file_type' => $json_type,
                        'file_size' => strlen($content),
                        'target_path' => $target_path,
                        'rebuild_requested' => $rebuild_after
                    ]);
                    
                    // Trigger FAISS rebuild if requested
                    if ($rebuild_after) {
                        $backend_path = realpath(__DIR__ . '/../backend');
                        
                        if ($json_type === 'catalogue') {
                            // For catalogue, we don't upload JSON - the database is the source
                            // This upload is for the database file itself
                            $python_cmd = "cd \"$backend_path\" && python export_catalogue_to_csv.py && python catalogue_indexer.py 2>&1";
                        } elseif ($json_type === 'general_queries') {
                            $python_cmd = "cd \"$backend_path\" && python build_general_queries_index.py 2>&1";
                        }
                        
                        if (isset($python_cmd)) {
                            $output = shell_exec($python_cmd);
                            if (stripos($output, 'successfully') !== false || stripos($output, 'complete') !== false) {
                                $success_message .= ' FAISS index rebuilt successfully!';
                                
                                // Log rebuild activity
                                logAdminActivity('faiss_rebuild_php', [
                                    'index_type' => $json_type,
                                    'triggered_by' => 'file_upload',
                                    'rebuild_success' => true
                                ]);
                            } else {
                                $success_message .= ' File uploaded but index rebuild may have failed. Check system logs.';
                                
                                // Log failed rebuild
                                logAdminActivity('faiss_rebuild_php', [
                                    'index_type' => $json_type,
                                    'triggered_by' => 'file_upload',
                                    'rebuild_success' => false,
                                    'error_output' => substr($output, 0, 500)
                                ]);
                            }
                        }
                    }
                } else {
                    $error_message = 'Failed to save file';
                }
            } else {
                $error_message = 'Invalid JSON format';
            }
        }
    } else {
        $error_message = 'File upload error';
    }
}

// Handle FAISS index rebuild
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['rebuild_faiss']) && $_SESSION['admin_logged_in']) {
    $index_type = $_POST['index_type'] ?? '';
    
    // Call Python script to rebuild FAISS index
    $backend_path = realpath(__DIR__ . '/../backend');
    $python_cmd = '';
    
    if ($index_type === 'catalogue') {
        // Export database to CSV first, then build index
        $python_cmd = "cd \"$backend_path\" && python export_catalogue_to_csv.py && python catalogue_indexer.py 2>&1";
    } elseif ($index_type === 'general') {
        $python_cmd = "cd \"$backend_path\" && python build_general_queries_index.py 2>&1";
    }
    
    if ($python_cmd) {
        $output = shell_exec($python_cmd);
        if (strpos($output, 'successfully') !== false || strpos($output, 'complete') !== false) {
            $success_message = ucfirst($index_type) . ' FAISS index rebuilt successfully!';
            
            // Log successful rebuild
            logAdminActivity('faiss_rebuild_php', [
                'index_type' => $index_type,
                'rebuild_success' => true,
                'output_length' => strlen($output)
            ]);
        } else {
            $error_message = 'Failed to rebuild index. Error: ' . htmlspecialchars($output);
            
            // Log failed rebuild
            logAdminActivity('faiss_rebuild_php', [
                'index_type' => $index_type,
                'rebuild_success' => false,
                'error_output' => substr($output, 0, 500)
            ]);
        }
    } else {
        $error_message = 'Invalid index type';
    }
}

$isLoggedIn = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;

// Helper functions
function getApiStats() {
    try {
        $response = @file_get_contents('http://localhost:8000/stats');
        return $response ? json_decode($response, true) : null;
    } catch (Exception $e) {
        return null;
    }
}

function getHealthStatus() {
    try {
        $response = @file_get_contents('http://localhost:8000/health');
        return $response ? json_decode($response, true) : null;
    } catch (Exception $e) {
        return null;
    }
}

function loadGeneralQueries() {
    if (file_exists(GENERAL_QUERIES_FILE)) {
        $content = file_get_contents(GENERAL_QUERIES_FILE);
        return json_decode($content, true) ?? [];
    }
    return [];
}

function formatBytes($bytes) {
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    }
    return $bytes . ' bytes';
}

$stats = getApiStats();
$health = getHealthStatus();
$queries = loadGeneralQueries();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Admin Panel - Nalanda Library Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #262730;
        }
        
        /* Login Styles */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(90deg, #059669, #0d9488);
        }
        
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 420px;
        }
        
        .logo-container {
            text-align: center;
            margin-bottom: 25px;
        }
        
        .logo-container img {
            height: 70px;
        }
        
        .login-box h2 {
            text-align: center;
            margin-bottom: 30px;
            color: #262730;
            font-size: 24px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }
        
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(90deg, #10b981, #0f766e);
            color: white;
            border: none;
        }
        
        .btn-primary:hover {
            background: linear-gradient(90deg, #059669, #0d9488);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }
        
        .btn-danger {
            background: #ff4b4b;
            color: white;
        }
        
        .btn-danger:hover {
            background: #e33e3e;
        }
        
        .btn-success {
            background: #4caf50;
            color: white;
        }
        
        .btn-success:hover {
            background: #45a049;
        }
        
        .btn-full {
            width: 100%;
        }
        
        /* Toggle Switch Styles */
        .config-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #dee2e6;
        }
        
        .toggle-container {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .toggle-label {
            display: flex;
            align-items: center;
            cursor: pointer;
            font-size: 16px;
        }
        
        .toggle-label input[type="checkbox"] {
            display: none;
        }
        
        .toggle-slider {
            position: relative;
            width: 60px;
            height: 30px;
            background: #ccc;
            border-radius: 30px;
            margin-right: 15px;
            transition: background 0.3s;
        }
        
        .toggle-slider:before {
            content: '';
            position: absolute;
            width: 26px;
            height: 26px;
            background: white;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: transform 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .toggle-label input[type="checkbox"]:checked + .toggle-slider {
            background: #28a745;
        }
        
        .toggle-label input[type="checkbox"]:checked + .toggle-slider:before {
            transform: translateX(30px);
        }
        
        .toggle-text {
            color: #333;
        }
        
        .config-description {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
            padding: 10px;
            background: #fff;
            border-radius: 4px;
            border-left: 4px solid #17a2b8;
        }
        
        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-error {
            background: #ffebee;
            color: #c62828;
            border-left: 4px solid #c62828;
        }
        
        .alert-success {
            background: #e8f5e9;
            color: #2e7d32;
            border-left: 4px solid #2e7d32;
        }
        
        /* Admin Dashboard */
        .admin-header {
            background: white;
            padding: 20px 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .admin-header h1 {
            font-size: 24px;
            color: #262730;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .admin-header h1 img {
            height: 36px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        /* Tabs */
        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 30px;
            background: white;
            padding: 8px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .tab {
            padding: 12px 24px;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            transition: all 0.3s;
        }
        
        .tab:hover {
            background: #f5f7fa;
            color: #262730;
        }
        
        .tab.active {
            background: #667eea;
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }
        
        .stat-card h3 {
            font-size: 13px;
            color: #808495;
            margin-bottom: 12px;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        
        .stat-card .value {
            font-size: 36px;
            font-weight: 700;
            color: #262730;
        }
        
        .stat-card.healthy { border-left: 5px solid #4caf50; }
        .stat-card.warning { border-left: 5px solid #ff9800; }
        .stat-card.error { border-left: 5px solid #f44336; }
        
        /* Section */
        .section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            margin-bottom: 24px;
        }
        
        .section h2 {
            margin-bottom: 20px;
            color: #262730;
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 14px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .info-row:last-child {
            border-bottom: none;
        }
        
        .info-label {
            font-weight: 600;
            color: #555;
        }
        
        .info-value {
            color: #262730;
        }
        
        .status-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-badge.healthy { background: #e8f5e9; color: #2e7d32; }
        .status-badge.degraded { background: #fff3e0; color: #f57c00; }
        .status-badge.unhealthy { background: #ffebee; color: #c62828; }
        .status-badge.enabled { background: #e8f5e9; color: #2e7d32; }
        .status-badge.disabled { background: #ffebee; color: #c62828; }
        
        /* Query Editor */
        .query-editor {
            margin: 20px 0;
        }
        
        .query-item {
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 12px;
            border: 2px solid #e0e0e0;
        }
        
        .query-item:hover {
            border-color: #667eea;
        }
        
        .query-header {
            font-weight: 600;
            color: #262730;
            margin-bottom: 8px;
        }
        
        .query-answer {
            color: #555;
            font-size: 14px;
            line-height: 1.6;
        }
        
        /* Table */
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f5f7fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #e0e0e0;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        /* Code block */
        code {
            background: #f5f7fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        
        pre {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
        }
        
        textarea {
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <?php if (!$isLoggedIn): ?>
        <!-- Login Screen -->
        <div class="login-container">
            <div class="login-box">
                <div class="logo-container">
                    <img src="assets/iit_ropar_logo.png" alt="IIT Ropar" style="height:70px" onerror="logoFallback(this)">
                </div>
                <h2>🔐 Admin Login</h2>
                <?php if (isset($login_error)): ?>
                    <div class="alert alert-error"><?= htmlspecialchars($login_error) ?></div>
                <?php endif; ?>
                <form method="POST">
                    <div class="form-group">
                        <label for="username">👤 Username</label>
                        <input type="text" id="username" name="username" required autofocus>
                    </div>
                    <div class="form-group">
                        <label for="password">🔒 Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" name="login" class="btn btn-primary btn-full">Login</button>
                </form>
                <p style="margin-top: 24px; text-align: center; color: #999; font-size: 12px;">
                    Nalanda Library Chatbot Enhanced Admin Panel
                </p>
            </div>
        </div>
    <?php else: ?>
        <!-- Admin Dashboard -->
        <div class="admin-header">
            <h1>
                <img src="assets/iit_ropar_logo.png" alt="IIT Ropar" style="height:36px" onerror="logoFallback(this)">
                📊 Enhanced Admin Dashboard
            </h1>
            <div class="user-info">
                <span style="color: #666;">👤 <?= htmlspecialchars($_SESSION['admin_user']) ?></span>
                <span style="color: #999; font-size: 13px;">Session: <?= gmdate('H:i:s', time() - $_SESSION['login_time']) ?></span>
                <a href="?logout=1" class="btn btn-danger">Logout</a>
            </div>
        </div>
        
        <div class="dashboard-container">
            <?php if (isset($success_message)): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success_message) ?></div>
            <?php endif; ?>
            
            <?php if (isset($error_message)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error_message) ?></div>
            <?php endif; ?>
            
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab active" onclick="switchTab(event, 'overview')">📊 Overview</button>
                <button class="tab" onclick="switchTab(event, 'queries')">📝 General Queries</button>
                <button class="tab" onclick="switchTab(event, 'files')">📄 File Manager</button>
                <button class="tab" onclick="switchTab(event, 'faiss')">🔍 FAISS Indices</button>
                <button class="tab" onclick="switchTab(event, 'analytics')">📈 Analytics</button>
                <button class="tab" onclick="switchTab(event, 'system')">⚙️ System</button>
            </div>
            
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="stats-grid">
                    <div class="stat-card <?= $health ? 'healthy' : 'error' ?>">
                        <h3>System Status</h3>
                        <div class="value">
                            <?php if ($health): ?>
                                <?= $health['status'] === 'healthy' ? '✅' : ($health['status'] === 'degraded' ? '⚠️' : '❌') ?>
                            <?php else: ?>
                                ❌
                            <?php endif; ?>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Active Clients</h3>
                        <div class="value"><?= $stats['total_clients'] ?? '0' ?></div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Cache Size</h3>
                        <div class="value"><?= $stats['classification_cache_size'] ?? '0' ?></div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Error Count</h3>
                        <div class="value"><?= $stats['error_count'] ?? '0' ?></div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🏥 System Health</h2>
                    <?php if ($health): ?>
                        <div class="info-row">
                            <span class="info-label">Status</span>
                            <span class="status-badge <?= $health['status'] ?>">
                                <?= strtoupper($health['status']) ?>
                            </span>
                        </div>
                        <?php if (isset($health['checks'])): ?>
                            <?php foreach ($health['checks'] as $check => $status): ?>
                                <div class="info-row">
                                    <span class="info-label"><?= htmlspecialchars(ucfirst(str_replace('_', ' ', $check))) ?></span>
                                    <span class="info-value"><?= $status ? '✅ OK' : '❌ Failed' ?></span>
                                </div>
                            <?php endforeach; ?>
                        <?php endif; ?>
                        <div class="info-row">
                            <span class="info-label">Last Check</span>
                            <span class="info-value"><?= $health['timestamp'] ?? 'N/A' ?></span>
                        </div>
                    <?php else: ?>
                        <p style="color: #c33;">⚠️ Unable to connect to backend API</p>
                    <?php endif; ?>
                </div>
                
                <div class="section">
                    <h2>🔌 API Endpoints</h2>
                    <div class="info-row">
                        <span class="info-label">Chat Endpoint</span>
                        <span class="info-value"><code>POST /chat</code></span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Health Check</span>
                        <span class="info-value"><code>GET /health</code></span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Statistics</span>
                        <span class="info-value"><code>GET /stats</code></span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">API Documentation</span>
                        <span class="info-value">
                            <a href="http://localhost:8000/docs" target="_blank" style="color: #667eea;">http://localhost:8000/docs</a>
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- General Queries Tab -->
            <div id="queries" class="tab-content">
                <div class="section">
                    <h2>📝 General Queries Editor</h2>
                    <p style="margin-bottom: 20px; color: #666;">
                        Edit the general queries and answers that the chatbot uses to respond to common questions.
                    </p>
                    
                    <form method="POST">
                        <div class="form-group">
                            <label for="queries_json">JSON Data (Pretty Format)</label>
                            <textarea name="queries_json" id="queries_json" rows="20" style="font-family: 'Courier New', monospace;"><?= htmlspecialchars(json_encode($queries, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) ?></textarea>
                        </div>
                        <button type="submit" name="save_queries" class="btn btn-success">💾 Save Queries</button>
                        <button type="button" onclick="validateJSON()" class="btn btn-primary" style="margin-left: 10px;">✓ Validate JSON</button>
                        <button type="button" onclick="apiSaveGeneralQueries()" class="btn btn-primary" style="margin-left: 10px;">🌐 Save via API (+ Rebuild)</button>
                    </form>
                    
                    <div style="margin-top: 20px;">
                        <h3 style="margin-bottom: 10px;">Current Queries (<?= count($queries) ?>)</h3>
                        <div class="query-editor">
                            <?php foreach ($queries as $question => $answer): ?>
                                <?php
                                    // Normalize answer to string safely (handles array/object answers)
                                    if (is_array($answer)) {
                                        // Flatten simple arrays; if associative keep JSON
                                        $isAssoc = array_keys($answer) !== range(0, count($answer) - 1);
                                        if ($isAssoc) {
                                            $answer_str = json_encode($answer, JSON_UNESCAPED_UNICODE);
                                        } else {
                                            $answer_str = implode('; ', array_map(function($v){
                                                return is_string($v) ? $v : json_encode($v, JSON_UNESCAPED_UNICODE);
                                            }, $answer));
                                        }
                                    } elseif (is_object($answer)) {
                                        $answer_str = json_encode($answer, JSON_UNESCAPED_UNICODE);
                                    } elseif (is_string($answer)) {
                                        $answer_str = $answer;
                                    } else {
                                        $answer_str = strval($answer);
                                    }
                                    $answer_str = trim($answer_str);
                                    $truncated = strlen($answer_str) > 200 ? substr($answer_str, 0, 200) . '...' : $answer_str;
                                ?>
                                <div class="query-item">
                                    <div class="query-header">Q: <?= htmlspecialchars($question) ?></div>
                                    <div class="query-answer">A: <?= htmlspecialchars($truncated) ?></div>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- File Manager Tab -->
            <div id="files" class="tab-content">
                <div class="section">
                    <h2>📄 JSON File Manager</h2>
                    
                    <h3 style="margin: 20px 0 10px;">📥 Download Files</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                        <?php
                        $files = [
                            'general_queries.json' => GENERAL_QUERIES_FILE,
                            'website_cache.json' => CACHE_DIR . '/website_cache.json',
                            'website_analysis.json' => CACHE_DIR . '/website_analysis.json'
                        ];
                        
                        foreach ($files as $name => $path):
                            if (file_exists($path)):
                                $size = filesize($path);
                        ?>
                            <div class="query-item">
                                <div class="query-header"><?= $name ?></div>
                                <div class="query-answer">
                                    Size: <?= formatBytes($size) ?><br>
                                    Modified: <?= date('Y-m-d H:i:s', filemtime($path)) ?>
                                </div>
                                <a href="download.php?file=<?= urlencode($name) ?>" class="btn btn-primary" style="margin-top: 10px;">⬇️ Download</a>
                            </div>
                        <?php 
                            else:
                        ?>
                            <div class="query-item">
                                <div class="query-header"><?= $name ?></div>
                                <div class="query-answer" style="color: #999;">File not found</div>
                            </div>
                        <?php
                            endif;
                        endforeach;
                        ?>
                    </div>
                    
                    <h3 style="margin: 30px 0 10px;">📤 Upload JSON File</h3>
                    <form method="POST" enctype="multipart/form-data">
                        <div class="form-group">
                            <label for="upload_target">Target File</label>
                            <select name="upload_target" id="upload_target">
                                <option value="general_queries">general_queries.json</option>
                                <option value="website_cache">website_cache.json</option>
                                <option value="website_analysis">website_analysis.json</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="json_file">Choose JSON File (Max 10MB)</label>
                            <input type="file" name="json_file" id="json_file" accept=".json" required>
                        </div>
                        <button type="submit" class="btn btn-success">📤 Upload File</button>
                    </form>
                </div>
            </div>
            
            <!-- Analytics Tab -->
            <div id="analytics" class="tab-content">
                <div class="section">
                    <h2>📈 Classification Analytics</h2>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Cache Hits</h3>
                            <div class="value" style="font-size: 28px;">N/A</div>
                            <p style="color: #999; font-size: 13px; margin-top: 8px;">Track query cache performance</p>
                        </div>
                        
                        <div class="stat-card">
                            <h3>API Status</h3>
                            <div class="value" style="font-size: 28px;">
                                <?= $health ? '🟢' : '🔴' ?>
                            </div>
                            <p style="color: #999; font-size: 13px; margin-top: 8px;">Backend connection</p>
                        </div>
                        
                        <div class="stat-card">
                            <h3>Total Queries</h3>
                            <div class="value" style="font-size: 28px;"><?= count($queries) ?></div>
                            <p style="color: #999; font-size: 13px; margin-top: 8px;">Configured responses</p>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <h3>ℹ️ Analytics Information</h3>
                        <p style="color: #666; line-height: 1.6;">
                            Advanced analytics features like cache hit rates, query performance metrics, and detailed logs 
                            are available through the Python backend's statistics endpoint. For real-time monitoring, 
                            visit the API test page at <a href="http://localhost:8000/test" target="_blank">http://localhost:8000/test</a>.
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- FAISS Indices Tab -->
            <div id="faiss" class="tab-content">
                <div class="section">
                    <h2>🔍 FAISS Index Management</h2>
                    <p>Manage and rebuild FAISS vector indices for semantic search functionality.</p>
                    
                    <?php
                    // Get index file information
                    $backend_path = realpath(__DIR__ . '/../backend');
                    $catalogue_index = $backend_path . '/catalogue_index.faiss';
                    $general_index = $backend_path . '/general_queries_index.faiss';
                    
                    $catalogue_exists = file_exists($catalogue_index);
                    $general_exists = file_exists($general_index);
                    
                    $catalogue_info = $catalogue_exists ? [
                        'size' => round(filesize($catalogue_index) / 1024, 2) . ' KB',
                        'modified' => date('Y-m-d H:i:s', filemtime($catalogue_index))
                    ] : null;
                    
                    $general_info = $general_exists ? [
                        'size' => round(filesize($general_index) / 1024, 2) . ' KB',
                        'modified' => date('Y-m-d H:i:s', filemtime($general_index))
                    ] : null;
                    ?>
                    
                    <h3>Index Status</h3>
                    <table>
                        <tr>
                            <th>Index Name</th>
                            <th>Status</th>
                            <th>File Size</th>
                            <th>Last Modified</th>
                            <th>Actions</th>
                        </tr>
                        <tr>
                            <td><strong>Catalogue Index</strong><br><small>Book search & recommendations</small></td>
                            <td>
                                <?php if ($catalogue_exists): ?>
                                    <span class="status-badge" style="background: #10b981; color: white; padding: 4px 8px; border-radius: 4px;">✅ Active</span>
                                <?php else: ?>
                                    <span class="status-badge" style="background: #ef4444; color: white; padding: 4px 8px; border-radius: 4px;">❌ Missing</span>
                                <?php endif; ?>
                            </td>
                            <td><?= $catalogue_info ? $catalogue_info['size'] : 'N/A' ?></td>
                            <td><?= $catalogue_info ? $catalogue_info['modified'] : 'N/A' ?></td>
                            <td>
                                <form method="POST" style="display: inline;" onsubmit="return confirm('Rebuild catalogue index? This may take a few minutes.');">
                                    <input type="hidden" name="rebuild_faiss" value="1">
                                    <input type="hidden" name="index_type" value="catalogue">
                                    <button type="submit" class="btn btn-primary" style="padding: 6px 12px;">🔄 Rebuild</button>
                                </form>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>General Queries Index</strong><br><small>Library Q&A knowledge base</small></td>
                            <td>
                                <?php if ($general_exists): ?>
                                    <span class="status-badge" style="background: #10b981; color: white; padding: 4px 8px; border-radius: 4px;">✅ Active</span>
                                <?php else: ?>
                                    <span class="status-badge" style="background: #ef4444; color: white; padding: 4px 8px; border-radius: 4px;">❌ Missing</span>
                                <?php endif; ?>
                            </td>
                            <td><?= $general_info ? $general_info['size'] : 'N/A' ?></td>
                            <td><?= $general_info ? $general_info['modified'] : 'N/A' ?></td>
                            <td>
                                <form method="POST" style="display: inline;" onsubmit="return confirm('Rebuild general queries index? This may take a few minutes.');">
                                    <input type="hidden" name="rebuild_faiss" value="1">
                                    <input type="hidden" name="index_type" value="general">
                                    <button type="submit" class="btn btn-primary" style="padding: 6px 12px;">🔄 Rebuild</button>
                                </form>
                            </td>
                        </tr>
                    </table>
                    <div style="margin-top:20px; padding:16px; background:#f8f9fa; border:1px solid #e5e7eb; border-radius:8px;">
                        <h3 style="margin-bottom:10px;">⚡ Live Index Status (API)</h3>
                        <button class="btn btn-primary" onclick="refreshIndexStatus()" style="margin-bottom:10px;">🔄 Refresh via API</button>
                        <pre id="live-index-status" style="min-height:80px;">(click Refresh to load)</pre>
                        <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;">
                            <button class="btn btn-success" onclick="apiRebuild('general')">Rebuild General (API)</button>
                            <button class="btn btn-success" onclick="apiRebuild('catalogue')">Rebuild Catalogue (API)</button>
                            <button class="btn btn-danger" onclick="apiClearCache()">Clear Cache (API)</button>
                        </div>
                        <p style="color:#666; font-size:12px; margin-top:8px;">Uses FastAPI endpoints on port 8000 instead of local shell execution.</p>
                        <div style="margin-top:14px; display:grid; grid-template-columns:1fr; gap:10px;">
                            <div style="background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:12px;">
                                <strong>Upload Catalogue CSV (API)</strong>
                                <div style="display:flex; gap:8px; margin-top:8px; align-items:center;">
                                    <input type="file" id="csvFile" accept=".csv">
                                    <button class="btn btn-primary" onclick="apiUploadCatalogueCsv()">📤 Upload + Rebuild</button>
                                </div>
                                <small>Expected columns should match the indexer; rebuild runs automatically.</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📤 Upload & Rebuild</h2>
                    <p>Upload updated JSON files and rebuild FAISS indices.</p>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                        <!-- Catalogue Upload & Rebuild -->
                        <div style="padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
                            <h3>📚 Catalogue Data</h3>
                            <p style="font-size: 14px; color: #6b7280;">Upload catalogue.json and rebuild the book search index.</p>
                            
                            <form method="POST" enctype="multipart/form-data" onsubmit="return confirm('Upload catalogue.json and rebuild index?');">
                                <input type="hidden" name="upload_json" value="1">
                                <input type="hidden" name="json_type" value="catalogue">
                                
                                <div style="margin: 15px 0;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Select catalogue.json:</label>
                                    <input type="file" name="json_file" accept=".json" required style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                                </div>
                                
                                <div style="margin: 15px 0;">
                                    <label style="display: flex; align-items: center; gap: 8px;">
                                        <input type="checkbox" name="rebuild_after_upload" value="1" checked>
                                        <span>Rebuild FAISS index after upload</span>
                                    </label>
                                </div>
                                
                                <button type="submit" class="btn btn-primary" style="width: 100%;">📤 Upload & Rebuild</button>
                            </form>
                        </div>
                        
                        <!-- General Queries Upload & Rebuild -->
                        <div style="padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
                            <h3>❓ General Queries</h3>
                            <p style="font-size: 14px; color: #6b7280;">Upload general_queries.json and rebuild the Q&A index.</p>
                            
                            <form method="POST" enctype="multipart/form-data" onsubmit="return confirm('Upload general_queries.json and rebuild index?');">
                                <input type="hidden" name="upload_json" value="1">
                                <input type="hidden" name="json_type" value="general_queries">
                                
                                <div style="margin: 15px 0;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Select general_queries.json:</label>
                                    <input type="file" name="json_file" accept=".json" required style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                                </div>
                                
                                <div style="margin: 15px 0;">
                                    <label style="display: flex; align-items: center; gap: 8px;">
                                        <input type="checkbox" name="rebuild_after_upload" value="1" checked>
                                        <span>Rebuild FAISS index after upload</span>
                                    </label>
                                </div>
                                
                                <button type="submit" class="btn btn-primary" style="width: 100%;">📤 Upload & Rebuild</button>
                            </form>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>ℹ️ About FAISS Indices</h2>
                    <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; font-size: 14px;">
                        <p><strong>What are FAISS Indices?</strong></p>
                        <p>FAISS (Facebook AI Similarity Search) indices enable fast semantic search across large datasets. The chatbot uses two indices:</p>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li><strong>Catalogue Index:</strong> Powers book search and recommendations using book metadata</li>
                            <li><strong>General Queries Index:</strong> Enables FAQ matching and library information retrieval</li>
                        </ul>
                        <p><strong>When to rebuild:</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>After updating book catalogue data</li>
                            <li>After modifying general queries/FAQs</li>
                            <li>If search results seem outdated or incorrect</li>
                        </ul>
                        <p style="margin-top: 10px;"><em>Note: Index rebuilding may take 1-5 minutes depending on dataset size.</em></p>
                    </div>
                </div>
            </div>
            
            <!-- System Tab -->
            <div id="system" class="tab-content">
                <div class="section">
                    <h2>⚙️ System Configuration</h2>
                    
                    <div class="config-section">
                        <h3>📖 Book Search Settings</h3>
                        <form method="POST" style="margin-bottom: 20px;">
                            <div class="toggle-container">
                                <label class="toggle-label">
                                    <input type="checkbox" name="enable_book_search" value="1" <?= getBookSearchEnabled() ? 'checked' : '' ?> onchange="this.form.submit()">
                                    <span class="toggle-slider"></span>
                                    <span class="toggle-text">
                                        Book Catalogue Search: 
                                        <strong><?= getBookSearchEnabled() ? 'Enabled' : 'Disabled' ?></strong>
                                    </span>
                                </label>
                                <input type="hidden" name="toggle_book_search" value="1">
                            </div>
                            <p class="config-description">
                                📚 When enabled, chatbot will search the book catalogue for specific book queries. 
                                When disabled, only general queries will be handled (policies, services, etc.).
                            </p>
                        </form>
                    </div>
                    
                    <div class="config-section">
                        <h3>🔍 OPAC Search Settings</h3>
                        <form method="POST" style="margin-bottom: 20px;">
                            <div class="toggle-container">
                                <label class="toggle-label">
                                    <input type="checkbox" name="enable_opac" value="1" <?= getOpacEnabled() ? 'checked' : '' ?> onchange="this.form.submit()">
                                    <span class="toggle-slider"></span>
                                    <span class="toggle-text">
                                        OPAC Real-time Search: 
                                        <strong><?= getOpacEnabled() ? 'Enabled' : 'Disabled' ?></strong>
                                    </span>
                                </label>
                                <input type="hidden" name="toggle_opac" value="1">
                            </div>
                            <p class="config-description">
                                🌐 When enabled, book searches will include real-time availability data from the OPAC system, 
                                showing current status and due dates for each item. (Requires Book Search to be enabled)
                            </p>
                        </form>
                    </div>
                    
                    <h3>System Configuration Status</h3>
                    <table>
                        <tr>
                            <th>Feature</th>
                            <th>Status</th>
                        </tr>
                        <tr>
                            <td>📖 Book Catalogue Search</td>
                            <td><span class="status-badge <?= getBookSearchEnabled() ? 'enabled' : 'disabled' ?>">
                                <?= getBookSearchEnabled() ? '✅ Enabled' : '❌ Disabled' ?>
                            </span></td>
                        </tr>
                        <tr>
                            <td>🔍 OPAC Real-time Search</td>
                            <td><span class="status-badge <?= getOpacEnabled() ? 'enabled' : 'disabled' ?>">
                                <?= getOpacEnabled() ? '✅ Enabled' : '❌ Disabled' ?>
                            </span></td>
                        </tr>
                    </table>
                    
                    <h3>Environment Information</h3>
                    <table>
                        <tr>
                            <th>Setting</th>
                            <th>Value</th>
                        </tr>
                        <tr>
                            <td>PHP Version</td>
                            <td><?= phpversion() ?></td>
                        </tr>
                        <tr>
                            <td>Server Software</td>
                            <td><?= $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown' ?></td>
                        </tr>
                        <tr>
                            <td>Upload Max Size</td>
                            <td><?= ini_get('upload_max_filesize') ?></td>
                        </tr>
                        <tr>
                            <td>Memory Limit</td>
                            <td><?= ini_get('memory_limit') ?></td>
                        </tr>
                        <tr>
                            <td>Session ID</td>
                            <td><code><?= session_id() ?></code></td>
                        </tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>⚡ Quick Actions</h2>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn btn-primary" onclick="window.location.reload()">🔄 Refresh Dashboard</button>
                        <button class="btn btn-primary" onclick="window.open('http://localhost:8000/test', '_blank')">🧪 Test API</button>
                        <button class="btn btn-primary" onclick="window.open('http://localhost:8000/docs', '_blank')">📚 API Docs</button>
                        <button class="btn btn-primary" onclick="window.open('/', '_blank')">🌐 View Chatbot</button>
                        <a href="?clear_cache=1" class="btn btn-danger" onclick="return confirm('Clear classification cache?')">🗑️ Clear Cache</a>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function switchTab(ev, tabName) {
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Remove active class from all tabs
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked tab
                if (ev && ev.currentTarget) {
                    ev.currentTarget.classList.add('active');
                }
            }
            
            function validateJSON() {
                const textarea = document.getElementById('queries_json');
                try {
                    JSON.parse(textarea.value);
                    alert('✅ JSON is valid!');
                } catch (e) {
                    alert('❌ Invalid JSON: ' + e.message);
                }
            }
            
            // Auto-refresh stats every 30 seconds
            setInterval(() => {
                if (document.getElementById('overview').classList.contains('active')) {
                    window.location.reload();
                }
            }, 30000);

            const API_BASE = 'http://localhost:8000';
            async function refreshIndexStatus() {
                const el = document.getElementById('live-index-status');
                el.textContent = '⏳ Loading...';
                try {
                    const res = await fetch(API_BASE + '/admin/index-status');
                    const data = await res.json();
                    el.textContent = JSON.stringify(data, null, 2);
                } catch (e) {
                    el.textContent = '❌ Failed to load: ' + e;
                }
            }
            async function apiRebuild(which) {
                if(!confirm('Rebuild ' + which + ' index via API?')) return;
                const el = document.getElementById('live-index-status');
                el.textContent = '🔨 Rebuilding ' + which + '...';
                try {
                    const res = await fetch(API_BASE + '/admin/rebuild', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({index: which})
                    });
                    const data = await res.json();
                    el.textContent = 'Rebuild result:\n' + JSON.stringify(data, null, 2);
                } catch (e) {
                    el.textContent = '❌ Rebuild failed: ' + e;
                }
            }
            async function apiClearCache() {
                if(!confirm('Clear backend caches via API?')) return;
                const el = document.getElementById('live-index-status');
                el.textContent = '🧹 Clearing cache...';
                try {
                    const res = await fetch(API_BASE + '/admin/clear-cache', {method: 'POST'});
                    const data = await res.json();
                    el.textContent = 'Cache clear result:\n' + JSON.stringify(data, null, 2);
                } catch (e) {
                    el.textContent = '❌ Clear failed: ' + e;
                }
            }

            async function apiSaveGeneralQueries() {
                const ta = document.getElementById('queries_json');
                try {
                    JSON.parse(ta.value);
                } catch (e) {
                    alert('Invalid JSON: ' + e.message);
                    return;
                }
                if(!confirm('Save general_queries.json via API and rebuild index?')) return;
                const fd = new FormData();
                const blob = new Blob([ta.value], {type: 'application/json'});
                fd.append('file', blob, 'general_queries.json');
                fd.append('rebuild', 'true');
                try {
                    const res = await fetch(API_BASE + '/admin/upload/general-queries', {method: 'POST', body: fd});
                    const data = await res.json();
                    alert((data.ok ? '✅ Saved' : '❌ Failed') + (data.rebuild_ok===false? ' (rebuild failed)' : ''));
                    refreshIndexStatus();
                } catch (e) {
                    alert('Upload failed: ' + e);
                }
            }

            async function apiUploadCatalogueCsv() {
                const input = document.getElementById('csvFile');
                if (!input.files || !input.files[0]) {
                    alert('Please choose a CSV file');
                    return;
                }
                if (!input.files[0].name.toLowerCase().endsWith('.csv')) {
                    alert('Please select a .csv file');
                    return;
                }
                const fd = new FormData();
                fd.append('file', input.files[0]);
                fd.append('rebuild', 'true');
                const el = document.getElementById('live-index-status');
                el.textContent = '📤 Uploading CSV and rebuilding...';
                try {
                    const res = await fetch(API_BASE + '/admin/upload/catalogue-csv', {method: 'POST', body: fd});
                    const data = await res.json();
                    el.textContent = 'Upload result:\n' + JSON.stringify(data, null, 2);
                    refreshIndexStatus();
                } catch (e) {
                    el.textContent = '❌ Upload failed: ' + e;
                }
            }

            // Graceful logo fallback: try alternate relative paths, then show emoji
            function logoFallback(img){
                try{
                    const candidates = [
                        'assets/iit_ropar_logo.png',
                        'assets/images/iit_ropar_logo.png',
                        '../assets/iit_ropar_logo.png',
                        '../assets/images/iit_ropar_logo.png'
                    ];
                    const triedJson = img.getAttribute('data-tried') || '[]';
                    const tried = JSON.parse(triedJson);
                    const next = candidates.find(p => !tried.includes(p));
                    if(next){
                        tried.push(next);
                        img.setAttribute('data-tried', JSON.stringify(tried));
                        img.src = next + '?v=' + Math.floor(Math.random()*100000);
                    }else{
                        img.outerHTML = '<span style="font-size: 32px; line-height:1;">📚</span>';
                    }
                }catch(e){
                    // final fallback
                    img.outerHTML = '<span style="font-size: 32px; line-height:1;">📚</span>';
                }
            }
        </script>
    <?php endif; ?>
</body>
</html>
