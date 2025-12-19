"""
Simple proxy to access private Cloud Run service
Opens browser with authenticated access
"""
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import webbrowser
import time
from threading import Timer

# Your Cloud Run URL
CLOUD_RUN_URL = "https://scout-app-634359182056.europe-west1.run.app"
PROXY_PORT = 8888

class ProxyHandler(BaseHTTPRequestHandler):
    """Proxy that forwards requests to Cloud Run with auth token"""
    
    auth_token = None
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"🔄 {self.command} {self.path} -> {args[1]}")
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"📥 Received GET request: {self.path}")
        self._proxy_request()
    
    def do_POST(self):
        """Handle POST requests"""
        print(f"📥 Received POST request: {self.path}")
        self._proxy_request()
    
    def _proxy_request(self):
        """Forward request to Cloud Run with authentication"""
        try:
            # Build target URL
            target_url = CLOUD_RUN_URL + self.path
            print(f"🎯 Target: {target_url}")
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {ProxyHandler.auth_token}',
                'User-Agent': self.headers.get('User-Agent', 'Scout-Proxy/1.0')
            }
            
            # Copy relevant headers from original request
            for header in ['Content-Type', 'Accept']:
                if header in self.headers:
                    headers[header] = self.headers[header]
            
            # Handle POST data
            data = None
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                data = self.rfile.read(content_length)
            
            # Make request to Cloud Run
            req = urllib.request.Request(
                target_url,
                data=data,
                headers=headers,
                method=self.command
            )
            
            print(f"📤 Sending request to Cloud Run...")
            with urllib.request.urlopen(req, timeout=30) as response:
                print(f"✅ Got response: {response.status}")
                # Send response back to client
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                
                self.end_headers()
                
                # Send response body
                body = response.read()
                self.wfile.write(body)
                print(f"✅ Sent {len(body)} bytes to client")
                
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
            try:
                self.send_error(e.code, str(e))
            except:
                pass
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.send_error(500, f"Proxy error: {str(e)}")
            except:
                pass

def get_auth_token():
    """Get GCP identity token using gcloud"""
    print("🔑 Getting authentication token...")
    try:
        # Use gcloud.cmd on Windows
        gcloud_cmd = 'gcloud.cmd' if sys.platform == 'win32' else 'gcloud'
        result = subprocess.run(
            [gcloud_cmd, 'auth', 'print-identity-token'],
            capture_output=True,
            text=True,
            timeout=10,
            shell=True  # Needed on Windows
        )
        
        if result.returncode == 0:
            token = result.stdout.strip()
            print("✅ Token obtained successfully")
            return token
        else:
            print(f"❌ Error getting token: {result.stderr}")
            print("\n💡 Try running: gcloud auth login")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ gcloud not found!")
        print("\n💡 Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def open_browser():
    """Open browser after server starts"""
    time.sleep(1)
    url = f"http://localhost:{PROXY_PORT}"
    print(f"\n🌐 Opening browser: {url}")
    webbrowser.open(url)

def main():
    """Main function"""
    print("🚀 Scout App Proxy - Cloud Run Authentication")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    ProxyHandler.auth_token = token
    
    # Test connection to Cloud Run
    print(f"\n🔗 Testing connection to {CLOUD_RUN_URL}...")
    try:
        req = urllib.request.Request(
            CLOUD_RUN_URL,
            headers={'Authorization': f'Bearer {token}'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"✅ Cloud Run service is accessible (status: {response.status})")
    except Exception as e:
        print(f"⚠️ Warning: Could not verify connection: {e}")
    
    # Start proxy server
    print(f"\n🚀 Starting proxy server on port {PROXY_PORT}...")
    try:
        server = HTTPServer(('localhost', PROXY_PORT), ProxyHandler)
        print(f"✅ Server created successfully")
    except Exception as e:
        print(f"❌ Failed to create server: {e}")
        sys.exit(1)
    
    print(f"\n✨ Proxy is running!")
    print(f"   🌐 Open your browser and go to: http://localhost:{PROXY_PORT}")
    print(f"   🔗 Proxying to: {CLOUD_RUN_URL}")
    print("\n📝 Press Ctrl+C to stop")
    print("📋 Waiting for requests...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Stopping proxy server...")
        server.shutdown()
        print("✅ Proxy stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
