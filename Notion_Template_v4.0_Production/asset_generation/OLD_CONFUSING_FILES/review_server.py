#!/usr/bin/env python3
"""
Review Server for Asset Generation
Provides web interface on port 4500 for reviewing and approving generated assets
"""

import os
import json
import time
import socket
import asyncio
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

class ReviewRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler for the review server"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.path = '/review.html'
        elif self.path == '/status':
            self.send_json_response(self.get_status())
            return
        elif self.path == '/manifest':
            self.send_manifest()
            return
        
        # Serve static files
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/approve':
            self.handle_approval()
        elif self.path == '/reject':
            self.handle_rejection()
        elif self.path == '/save-prompt':
            self.handle_save_prompt()
        elif self.path == '/regenerate':
            self.handle_regenerate()
        else:
            self.send_error(404)
    
    def get_status(self):
        """Get current review status"""
        manifest_path = Path(self.server.directory) / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                return {
                    'status': 'ready',
                    'samples': len(manifest.get('samples', [])),
                    'total_cost': manifest.get('total_cost', 0),
                    'errors': len(manifest.get('errors', [])),
                    'timestamp': manifest.get('timestamp', '')
                }
        return {'status': 'waiting', 'message': 'No samples generated yet'}
    
    def send_manifest(self):
        """Send the manifest.json file"""
        manifest_path = Path(self.server.directory) / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                data = json.load(f)
                self.send_json_response(data)
        else:
            self.send_error(404, "Manifest not found")
    
    def send_json_response(self, data):
        """Send JSON response"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)
    
    def handle_approval(self):
        """Handle approval POST request"""
        # Create approval file
        approval_file = Path("APPROVED.txt")
        with open(approval_file, 'w') as f:
            f.write(f"Samples approved at {datetime.now().isoformat()}\n")
            f.write(f"Reviewed via web interface on port {self.server.server_port}\n")
        
        self.send_json_response({'status': 'approved', 'message': 'Samples approved successfully'})
        print(f"{Fore.GREEN}✅ Samples APPROVED via web interface{Style.RESET_ALL}")
    
    def handle_rejection(self):
        """Handle rejection POST request"""
        # Create rejection file
        rejection_file = Path("REJECTED.txt")
        with open(rejection_file, 'w') as f:
            f.write(f"Samples rejected at {datetime.now().isoformat()}\n")
            f.write(f"Reviewed via web interface on port {self.server.server_port}\n")
        
        self.send_json_response({'status': 'rejected', 'message': 'Samples rejected'})
        print(f"{Fore.YELLOW}⚠️ Samples REJECTED via web interface{Style.RESET_ALL}")
    
    def handle_save_prompt(self):
        """Handle saving edited prompts"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        # Load prompts.json
        prompts_path = Path("../prompts.json")
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                prompts_data = json.load(f)
            
            # Update the prompt
            asset_type = data.get('type')
            page_title = data.get('page_title')
            new_prompt = data.get('prompt')
            
            if asset_type in prompts_data['prompts']:
                if page_title in prompts_data['prompts'][asset_type]:
                    # Store edit history
                    old_prompt = prompts_data['prompts'][asset_type][page_title]['current']
                    prompts_data['prompts'][asset_type][page_title]['current'] = new_prompt
                    prompts_data['prompts'][asset_type][page_title]['metadata']['prompt_history'].append(new_prompt)
                    
                    # Add to edited prompts
                    if asset_type not in prompts_data['edited_prompts']:
                        prompts_data['edited_prompts'][asset_type] = {}
                    prompts_data['edited_prompts'][asset_type][page_title] = {
                        'old': old_prompt,
                        'new': new_prompt,
                        'edited_at': datetime.now().isoformat()
                    }
                    
                    # Update statistics
                    prompts_data['statistics']['total_prompts_edited'] += 1
                    prompts_data['statistics']['last_updated'] = datetime.now().isoformat()
            
            # Save updated prompts
            with open(prompts_path, 'w') as f:
                json.dump(prompts_data, f, indent=2)
            
            self.send_json_response({'status': 'saved', 'message': 'Prompt updated successfully'})
            print(f"{Fore.GREEN}✅ Prompt updated for {page_title}{Style.RESET_ALL}")
        else:
            self.send_json_response({'status': 'error', 'message': 'prompts.json not found'})
    
    def handle_regenerate(self):
        """Handle regeneration request for specific asset"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        # Add to regeneration queue in prompts.json
        prompts_path = Path("../prompts.json")
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                prompts_data = json.load(f)
            
            prompts_data['regeneration_queue'].append({
                'type': data.get('type'),
                'page_title': data.get('page_title'),
                'filename': data.get('filename'),
                'prompt': data.get('prompt'),
                'requested_at': datetime.now().isoformat()
            })
            
            with open(prompts_path, 'w') as f:
                json.dump(prompts_data, f, indent=2)
            
            self.send_json_response({'status': 'queued', 'message': 'Asset queued for regeneration'})
            print(f"{Fore.CYAN}🔄 Asset queued for regeneration: {data.get('filename')}{Style.RESET_ALL}")
        else:
            self.send_json_response({'status': 'error', 'message': 'prompts.json not found'})
    
    def log_message(self, format, *args):
        """Override to suppress default logging"""
        pass  # Suppress default HTTP logging

class ReviewServer:
    """HTTP server for reviewing generated samples"""
    
    def __init__(self, port=4500, directory="output/samples", auto_open=True):
        """Initialize review server"""
        self.port = port
        self.directory = Path(directory)
        self.auto_open = auto_open
        self.server = None
        self.thread = None
        
        # Load config if exists
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                self.port = config.get("review", {}).get("port", 4500)
                self.auto_open = config.get("review", {}).get("auto_open", True)
        
        # Create review HTML if it doesn't exist
        self.create_review_html()
    
    def create_review_html(self):
        """Create the review HTML interface"""
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estate Planning Asset Review - Port 4500</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #4A7C74 0%, #527B84 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .status-bar {
            background: #f8f9fa;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e9ecef;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-item .label {
            color: #6c757d;
            font-size: 0.9em;
        }
        .status-item .value {
            font-size: 1.2em;
            font-weight: bold;
            color: #212529;
        }
        .cost { color: #28a745; }
        .error-count { color: #dc3545; }
        .assets-grid {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .asset-card {
            border: 2px solid #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .asset-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }
        .asset-preview {
            height: 200px;
            background: #f8f9fa;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
            color: #dee2e6;
        }
        .asset-info {
            padding: 15px;
            background: white;
        }
        .asset-type {
            display: inline-block;
            padding: 3px 8px;
            background: #007bff;
            color: white;
            border-radius: 3px;
            font-size: 0.8em;
            margin-bottom: 8px;
        }
        .asset-prompt {
            color: #495057;
            font-size: 0.9em;
            line-height: 1.4;
        }
        .prompt-editor {
            width: 100%;
            min-height: 60px;
            padding: 8px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 0.85em;
            font-family: monospace;
            resize: vertical;
            margin-top: 8px;
        }
        .prompt-editor:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0,123,255,0.1);
        }
        .prompt-actions {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }
        .btn-small {
            padding: 5px 10px;
            font-size: 0.85em;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-save-prompt {
            background: #28a745;
            color: white;
        }
        .btn-save-prompt:hover {
            background: #218838;
        }
        .btn-regenerate {
            background: #17a2b8;
            color: white;
        }
        .btn-regenerate:hover {
            background: #138496;
        }
        .metadata-info {
            font-size: 0.75em;
            color: #6c757d;
            margin-top: 5px;
        }
        .asset-cost {
            margin-top: 8px;
            color: #28a745;
            font-weight: bold;
        }
        .action-bar {
            padding: 30px;
            background: #f8f9fa;
            display: flex;
            justify-content: center;
            gap: 20px;
            border-top: 2px solid #e9ecef;
        }
        .btn {
            padding: 15px 40px;
            font-size: 1.1em;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn-approve {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        .btn-approve:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(40, 167, 69, 0.3);
        }
        .btn-reject {
            background: white;
            color: #dc3545;
            border: 2px solid #dc3545;
        }
        .btn-reject:hover {
            background: #dc3545;
            color: white;
        }
        .loading {
            text-align: center;
            padding: 50px;
            color: #6c757d;
        }
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Estate Planning Asset Review</h1>
            <p>Review generated samples before mass production</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <span class="label">Samples Generated:</span>
                <span class="value" id="sample-count">0</span>
            </div>
            <div class="status-item">
                <span class="label">Total Cost:</span>
                <span class="value cost" id="total-cost">$0.00</span>
            </div>
            <div class="status-item">
                <span class="label">Errors:</span>
                <span class="value error-count" id="error-count">0</span>
            </div>
            <div class="status-item">
                <span class="label">Port:</span>
                <span class="value">4500</span>
            </div>
        </div>
        
        <div id="assets-container" class="assets-grid">
            <div class="loading">
                <div class="loading-spinner"></div>
                <p>Loading samples...</p>
            </div>
        </div>
        
        <div class="action-bar">
            <button class="btn btn-reject" onclick="rejectSamples()">
                ❌ Reject & Refine
            </button>
            <button class="btn btn-approve" onclick="approveSamples()">
                ✅ Approve for Production
            </button>
        </div>
    </div>
    
    <script>
        // Load manifest and display assets
        async function loadManifest() {
            try {
                const response = await fetch('/manifest');
                const data = await response.json();
                
                // Update status
                document.getElementById('sample-count').textContent = data.samples.length;
                document.getElementById('total-cost').textContent = `$${data.total_cost.toFixed(3)}`;
                document.getElementById('error-count').textContent = data.errors.length;
                
                // Display assets
                const container = document.getElementById('assets-container');
                container.innerHTML = '';
                
                data.samples.forEach((asset, index) => {
                    const card = document.createElement('div');
                    card.className = 'asset-card';
                    
                    const typeColors = {
                        'icons': '#007bff',
                        'covers': '#28a745',
                        'textures': '#ffc107'
                    };
                    
                    // Extract metadata
                    const metadata = asset.metadata || {};
                    const pageTitle = metadata.page_title || 'Unknown';
                    const pageDesc = metadata.page_description || '';
                    
                    card.innerHTML = `
                        <div class="asset-preview">
                            ${asset.type === 'icons' ? '⚙️' : asset.type === 'covers' ? '📐' : '🎨'}
                        </div>
                        <div class="asset-info">
                            <span class="asset-type" style="background: ${typeColors[asset.type]}">
                                ${asset.type.toUpperCase()}
                            </span>
                            <div class="metadata-info">
                                <strong>${pageTitle}</strong>
                                ${pageDesc ? `<br><small>${pageDesc}</small>` : ''}
                            </div>
                            <textarea class="prompt-editor" id="prompt-${index}" 
                                      data-type="${asset.type}" 
                                      data-page="${pageTitle}"
                                      data-filename="${asset.filename}">${asset.prompt}</textarea>
                            <div class="prompt-actions">
                                <button class="btn-small btn-save-prompt" onclick="savePrompt(${index})">
                                    💾 Save
                                </button>
                                <button class="btn-small btn-regenerate" onclick="regenerateAsset(${index})">
                                    🔄 Regenerate
                                </button>
                            </div>
                            <div class="asset-cost">Cost: $${asset.cost.toFixed(3)}</div>
                        </div>
                    `;
                    
                    container.appendChild(card);
                });
            } catch (error) {
                console.error('Failed to load manifest:', error);
            }
        }
        
        async function approveSamples() {
            if (confirm('Approve these samples for mass production?')) {
                const response = await fetch('/approve', { method: 'POST' });
                const result = await response.json();
                alert('✅ ' + result.message);
                setTimeout(() => window.close(), 2000);
            }
        }
        
        async function rejectSamples() {
            if (confirm('Reject these samples and refine prompts?')) {
                const response = await fetch('/reject', { method: 'POST' });
                const result = await response.json();
                alert('⚠️ ' + result.message);
                setTimeout(() => window.close(), 2000);
            }
        }
        
        async function savePrompt(index) {
            const textarea = document.getElementById(`prompt-${index}`);
            const data = {
                type: textarea.dataset.type,
                page_title: textarea.dataset.page,
                prompt: textarea.value
            };
            
            try {
                const response = await fetch('/save-prompt', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.status === 'saved') {
                    // Visual feedback
                    textarea.style.borderColor = '#28a745';
                    setTimeout(() => {
                        textarea.style.borderColor = '#dee2e6';
                    }, 2000);
                }
            } catch (error) {
                console.error('Failed to save prompt:', error);
                alert('Failed to save prompt');
            }
        }
        
        async function regenerateAsset(index) {
            const textarea = document.getElementById(`prompt-${index}`);
            const data = {
                type: textarea.dataset.type,
                page_title: textarea.dataset.page,
                filename: textarea.dataset.filename,
                prompt: textarea.value
            };
            
            if (confirm(`Queue ${data.filename} for regeneration with new prompt?`)) {
                try {
                    const response = await fetch('/regenerate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    
                    if (result.status === 'queued') {
                        alert('✅ Asset queued for regeneration');
                    }
                } catch (error) {
                    console.error('Failed to queue regeneration:', error);
                    alert('Failed to queue regeneration');
                }
            }
        }
        
        // Load on page load
        window.onload = loadManifest;
        
        // Refresh every 5 seconds (disabled for now to avoid losing edits)
        // setInterval(loadManifest, 5000);
    </script>
</body>
</html>'''
        
        html_path = self.directory / "review.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, 'w') as f:
            f.write(html_content)
    
    def check_port(self, port):
        """Check if port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except:
                return False
    
    def find_available_port(self, start_port=4500):
        """Find next available port starting from start_port"""
        for port in range(start_port, start_port + 10):
            if self.check_port(port):
                return port
        return None
    
    def start(self):
        """Start the review server"""
        # Check if port is available
        if not self.check_port(self.port):
            print(f"{Fore.YELLOW}⚠️ Port {self.port} is in use, finding alternative...{Style.RESET_ALL}")
            self.port = self.find_available_port(self.port)
            if not self.port:
                raise RuntimeError("No available ports found")
            print(f"{Fore.GREEN}✓ Using port {self.port}{Style.RESET_ALL}")
        
        # Create server
        os.chdir(self.directory)
        handler = ReviewRequestHandler
        handler.directory = self.directory
        self.server = HTTPServer(('localhost', self.port), handler)
        self.server.directory = self.directory
        
        # Start server in thread
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        
        url = f"http://localhost:{self.port}/review.html"
        print(f"\n{Fore.GREEN}✅ Review server started{Style.RESET_ALL}")
        print(f"📍 URL: {Fore.CYAN}{url}{Style.RESET_ALL}")
        
        # Auto-open browser if configured
        if self.auto_open:
            time.sleep(1)
            print(f"{Fore.GREEN}🌐 Opening browser automatically...{Style.RESET_ALL}")
            webbrowser.open(url)
    
    def stop(self):
        """Stop the review server"""
        if self.server:
            self.server.shutdown()
            print(f"{Fore.YELLOW}Review server stopped{Style.RESET_ALL}")
    
    async def wait_for_approval(self, approval_file, timeout=600):
        """Wait for approval file to be created"""
        start_time = time.time()
        approval_path = Path(approval_file)
        rejection_path = Path("REJECTED.txt")
        
        print(f"\n{Fore.YELLOW}⏳ Waiting for review decision...{Style.RESET_ALL}")
        print(f"   • To approve: Click 'Approve for Production' in browser")
        print(f"   • To reject: Click 'Reject & Refine' in browser")
        print(f"   • Or create {approval_file} manually to approve")
        
        while time.time() - start_time < timeout:
            if approval_path.exists():
                return True
            if rejection_path.exists():
                return False
            await asyncio.sleep(1)
        
        print(f"{Fore.RED}⏰ Review timeout after {timeout} seconds{Style.RESET_ALL}")
        return False

def launch_review_after_generation():
    """Launch review server after sample generation"""
    server = ReviewServer()
    server.start()
    
    # Wait for user input
    print(f"\n{Fore.CYAN}Press Enter to stop the review server...{Style.RESET_ALL}")
    input()
    
    server.stop()
    
    # Check for approval
    if Path("APPROVED.txt").exists():
        return True
    return False

if __name__ == "__main__":
    # Test the review server
    server = ReviewServer()
    server.start()
    
    try:
        print(f"\n{Fore.CYAN}Review server running. Press Ctrl+C to stop.{Style.RESET_ALL}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()