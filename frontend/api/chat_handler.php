<?php
// Strictly JSON API: suppress HTML notices/warnings and ensure clean JSON output
ini_set('display_errors', '0');
error_reporting(0);
// Ensure UTF-8
if (!headers_sent()) {
    header('Content-Type: application/json; charset=utf-8');
}
/**
 * PHP Backend Handler - Bridges PHP frontend to Python API
 * Handles user queries and forwards them to Python FastAPI server
 * 
 * Local Testing Configuration:
 * Python API URL: http://localhost:8000/chat
 */
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Method not allowed']);
    exit;
}

// Get JSON input
$input = json_decode(file_get_contents('php://input'), true);

// Validate input
if (!isset($input['query']) || empty(trim($input['query']))) {
    echo json_encode([
        'success' => false,
        'error' => 'Query is required'
    ]);
    exit;
}

$query = trim($input['query']);
$search_mode = isset($input['search_mode']) ? $input['search_mode'] : 'auto';

// Validate search mode
$valid_modes = ['auto', 'books', 'library', 'website'];
if (!in_array($search_mode, $valid_modes)) {
    $search_mode = 'auto';
}

// Input length validation (max 300 characters)
if (strlen($query) > 300) {
    echo json_encode([
        'success' => false,
        'error' => 'Query too long. Maximum 300 characters allowed.'
    ]);
    exit;
}

// Prepare data for Python API
$data = [
    'query' => $query,
    'search_mode' => $search_mode
];

// Python API endpoint (local testing - change for production)
$python_api_url = 'http://localhost:8000/chat';

// Initialize cURL
// Verify cURL availability
if (!function_exists('curl_init')) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'PHP cURL extension is not enabled. Please enable extension=curl in php.ini.',
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

$ch = curl_init($python_api_url);

// Set cURL options
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($data),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'X-Client-IP: ' . get_client_ip()  // Pass client IP for rate limiting
    ],
    CURLOPT_TIMEOUT => 30,  // 30 second timeout
    CURLOPT_CONNECTTIMEOUT => 5  // 5 second connection timeout
]);

// Execute request
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

// Handle Python API response
if ($http_code == 200 && $response) {
    $result = json_decode($response, true);
    
    // Check if Python API returned success
    if (isset($result['success']) && $result['success']) {
        echo json_encode([
            'success' => true,
            'response' => $result['response'],
            'query' => $result['query'],
            'processing_time' => $result['processing_time']
        ]);
    } elseif (isset($result['error'])) {
        // Rate limit or other error from Python API
        echo json_encode([
            'success' => false,
            'error' => $result['error']
        ]);
    } else {
        echo json_encode([
            'success' => false,
            'error' => 'Unexpected response from chatbot service'
        ]);
    }
} else {
    // Python API connection error
    $error_msg = 'Chatbot service unavailable';
    
    // More specific error messages for debugging
    if ($http_code === 0) {
        $error_msg = 'Cannot connect to Python backend. Please ensure the Python API server is running on http://localhost:8000';
    } elseif ($http_code >= 500) {
        $error_msg = 'Python backend internal error';
    } elseif ($curl_error) {
        $error_msg .= ': ' . $curl_error;
    }
    
    echo json_encode([
        'success' => false,
        'error' => $error_msg,
        'debug' => [
            'http_code' => $http_code,
            'curl_error' => $curl_error,
            'api_url' => $python_api_url
        ]
    ], JSON_UNESCAPED_UNICODE);
}

/**
 * Get client IP address (handles proxy/load balancer scenarios)
 * 
 * @return string Client IP address
 */
function get_client_ip() {
    $ip_keys = [
        'HTTP_CLIENT_IP',
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR'
    ];
    
    foreach ($ip_keys as $key) {
        if (array_key_exists($key, $_SERVER)) {
            $ip_list = explode(',', $_SERVER[$key]);
            $ip = trim($ip_list[0]);
            
            // Validate IP address
            if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
                return $ip;
            }
        }
    }
    
    return $_SERVER['REMOTE_ADDR'] ?? 'unknown';
}

/**
 * Log query for analytics (optional)
 * 
 * @param string $query User query
 * @param bool $success Whether request was successful
 */
function log_query($query, $success) {
    // Optional: Log queries to file for analytics
    $log_file = __DIR__ . '/../../backend/logs/php_queries.log';
    $log_entry = date('Y-m-d H:i:s') . ' | ' . 
                 get_client_ip() . ' | ' . 
                 ($success ? 'SUCCESS' : 'FAIL') . ' | ' . 
                 substr($query, 0, 100) . PHP_EOL;
    
    @file_put_contents($log_file, $log_entry, FILE_APPEND);
}

