"""
MCP Hello World Server for Vercel
Exposes /api/mcp endpoint that handles MCP protocol over HTTP
"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

# Widget HTML template
WIDGET_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: system-ui; 
            padding: 20px; 
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card { 
            background: white; 
            padding: 32px; 
            border-radius: 12px; 
            box-shadow: 0 8px 16px rgba(0,0,0,0.2); 
            max-width: 400px;
        }
        h1 { color: #333; margin: 0 0 16px 0; font-size: 32px; }
        p { color: #666; margin: 0; font-size: 14px; }
        .emoji { font-size: 48px; margin-bottom: 16px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="emoji">👋</div>
        <h1 id="greeting">Hello!</h1>
        <p id="timestamp"></p>
    </div>
    <script>
        const output = window.openai?.toolOutput || {};
        document.getElementById('greeting').textContent = output.message || 'Hello World!';
        document.getElementById('timestamp').textContent = 'Generated: ' + (output.timestamp || new Date().toLocaleString());
    </script>
</body>
</html>
"""

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle MCP protocol requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            request = json.loads(body)
            method = request.get('method')
            
            if method == 'initialize':
                response = self.handle_initialize(request)
            elif method == 'tools/list':
                response = self.handle_list_tools(request)
            elif method == 'tools/call':
                response = self.handle_call_tool(request)
            elif method == 'resources/list':
                response = self.handle_list_resources(request)
            elif method == 'resources/read':
                response = self.handle_read_resource(request)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_initialize(self, request):
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "hello-world-mcp",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {},
                    "resources": {}
                }
            }
        }
    
    def handle_list_tools(self, request):
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [{
                    "name": "hello_world",
                    "description": "Display a greeting widget",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name to greet"
                            }
                        },
                        "required": ["name"]
                    }
                }]
            }
        }
    
    def handle_call_tool(self, request):
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "hello_world":
            user_name = arguments.get("name", "World")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"Showing greeting for {user_name}"
                    }],
                    "structuredContent": {
                        "message": f"Hello, {user_name}!",
                        "timestamp": datetime.now().isoformat()
                    },
                    "_meta": {
                        "openai/outputTemplate": "ui://widget/hello.html"
                    }
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
        }
    
    def handle_list_resources(self, request):
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "resources": [{
                    "uri": "ui://widget/hello.html",
                    "name": "Hello Widget",
                    "mimeType": "text/html+skybridge"
                }]
            }
        }
    
    def handle_read_resource(self, request):
        params = request.get("params", {})
        uri = params.get("uri")
        
        if uri == "ui://widget/hello.html":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "text/html+skybridge",
                        "text": WIDGET_HTML
                    }]
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32602, "message": f"Unknown resource: {uri}"}
        }
