<?php
/**
 * File Download Handler for Admin Panel
 */

session_start();

// Check if user is logged in
if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    http_response_code(403);
    die('Access denied. Please login first.');
}

// File mappings
$files = [
    'general_queries.json' => '../backend/general_queries.json',
    'website_cache.json' => '../backend/cache/website_cache.json',
    'website_analysis.json' => '../backend/cache/website_analysis.json'
];

$filename = $_GET['file'] ?? '';

if (!isset($files[$filename])) {
    http_response_code(404);
    die('File not found.');
}

$filepath = $files[$filename];

if (!file_exists($filepath)) {
    http_response_code(404);
    die('File does not exist on server.');
}

// Set headers for download
header('Content-Type: application/json');
header('Content-Disposition: attachment; filename="' . $filename . '"');
header('Content-Length: ' . filesize($filepath));
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Sat, 26 Jul 1997 05:00:00 GMT');

// Output file
readfile($filepath);
exit;
