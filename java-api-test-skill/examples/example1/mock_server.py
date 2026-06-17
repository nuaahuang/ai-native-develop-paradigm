import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

MOCK_DATA = {
    "users": {
        "list": {
            "data": [
                {"id": 1, "username": "user1", "email": "user1@example.com"},
                {"id": 2, "username": "user2", "email": "user2@example.com"}
            ],
            "total": 2
        },
        "single": {
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "created_at": "2024-01-01T10:00:00Z"
        },
        "created": {
            "id": 100,
            "username": "new_user",
            "email": "new@example.com"
        }
    },
    "orders": {
        "list": {
            "data": [
                {"id": 1, "status": "pending", "total_amount": 100.00},
                {"id": 2, "status": "completed", "total_amount": 200.00}
            ],
            "total": 2
        },
        "single": {
            "id": 1,
            "items": [
                {"product_id": 1, "quantity": 2, "price": 50.00}
            ],
            "status": "pending",
            "total_amount": 100.00,
            "address_id": 1
        },
        "created": {
            "id": 100,
            "status": "pending",
            "total_amount": 150.00
        }
    }
}


class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        if path.startswith('/api/users'):
            if path == '/api/users':
                response = MOCK_DATA["users"]["list"]
            elif path.startswith('/api/users/'):
                user_id = path.split('/')[-1]
                response = MOCK_DATA["users"]["single"]
                response["id"] = int(user_id)
            else:
                response = {"error": "Not found"}
        
        elif path.startswith('/api/orders'):
            if path == '/api/orders':
                response = MOCK_DATA["orders"]["list"]
            elif path.startswith('/api/orders/'):
                order_id = path.split('/')[-1]
                response = MOCK_DATA["orders"]["single"]
                response["id"] = int(order_id)
            else:
                response = {"error": "Not found"}
        
        else:
            response = {"error": "Route not found"}
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode()
        
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/api/users':
            response = MOCK_DATA["users"]["created"]
            status_code = 201
        elif path == '/api/orders':
            response = MOCK_DATA["orders"]["created"]
            status_code = 201
        elif '/api/orders/' in path and '/cancel' in path:
            parts = path.split('/')
            if len(parts) >= 5 and parts[4] == 'cancel':
                order_id = parts[3]
                response = {"id": int(order_id), "status": "cancelled"}
                status_code = 200
            else:
                response = {"error": "Route not found"}
                status_code = 404
        else:
            response = {"error": "Route not found"}
            status_code = 404
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_PUT(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        parsed = urlparse(self.path)
        
        if parsed.path.startswith('/api/users/'):
            user_id = parsed.path.split('/')[-1]
            response = MOCK_DATA["users"]["single"]
            response["id"] = int(user_id)
            response["username"] = "updated_user"
        elif parsed.path.startswith('/api/orders/'):
            order_id = parsed.path.split('/')[-1]
            response = MOCK_DATA["orders"]["single"]
            response["id"] = int(order_id)
            response["status"] = "updated"
        else:
            response = {"error": "Route not found"}
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_DELETE(self):
        self.send_response(204)
        self.end_headers()
    
    def log_message(self, format, *args):
        pass


def start_server(host='localhost', port=8888):
    server = HTTPServer((host, port), MockHandler)
    print(f"🚀 Mock服务器启动: http://{host}:{port}")
    print("支持的接口:")
    print("  GET    /api/users")
    print("  GET    /api/users/{id}")
    print("  POST   /api/users")
    print("  PUT    /api/users/{id}")
    print("  DELETE /api/users/{id}")
    print("  GET    /api/orders")
    print("  GET    /api/orders/{id}")
    print("  POST   /api/orders")
    print("  PUT    /api/orders/{id}")
    print("  DELETE /api/orders/{id}")
    print("\n按 Ctrl+C 停止服务器")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Mock服务器已停止")
        server.server_close()


if __name__ == '__main__':
    start_server()