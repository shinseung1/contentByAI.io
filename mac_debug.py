#!/usr/bin/env python3
"""
Mac 네트워크 디버깅 및 서버 시작
"""

import socket
import subprocess
import sys

def check_network():
    """네트워크 설정 확인"""
    print("🔍 Mac 네트워크 설정 확인:")
    
    # localhost 해상도 확인
    try:
        ip = socket.gethostbyname('localhost')
        print(f"✅ localhost → {ip}")
    except Exception as e:
        print(f"❌ localhost 해상도 실패: {e}")
    
    # 127.0.0.1 연결 테스트
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 22))  # SSH 포트 테스트
        if result == 0:
            print("✅ 127.0.0.1 연결 가능")
        else:
            print(f"⚠️  127.0.0.1 연결 문제: {result}")
        sock.close()
    except Exception as e:
        print(f"❌ 127.0.0.1 테스트 실패: {e}")
    
    # 사용 가능한 포트 찾기
    for port in [3000, 3001, 3002, 3003]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('127.0.0.1', port))
            sock.close()
            print(f"✅ 포트 {port} 사용 가능")
            return port
        except Exception as e:
            print(f"❌ 포트 {port} 사용 불가: {e}")
    
    return None

def start_simple_server(port):
    """간단한 HTTP 서버 시작"""
    print(f"\n🚀 포트 {port}에서 간단한 서버 시작:")
    
    try:
        # Python 내장 HTTP 서버 사용
        import http.server
        import socketserver
        from functools import partial
        
        class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response = '{"status": "healthy", "message": "Mac 서버 작동 중"}'
                    self.wfile.write(response.encode())
                elif self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    html = '''
                    <html>
                    <body>
                        <h1>🍎 AI Writer Mac 서버</h1>
                        <p>서버가 정상적으로 실행되고 있습니다!</p>
                        <ul>
                            <li><a href="/health">/health</a> - 상태 확인</li>
                        </ul>
                    </body>
                    </html>
                    '''
                    self.wfile.write(html.encode())
                else:
                    super().do_GET()
        
        with socketserver.TCPServer(("127.0.0.1", port), MyHTTPRequestHandler) as httpd:
            print(f"📍 서버 주소: http://127.0.0.1:{port}")
            print(f"📍 서버 주소: http://localhost:{port}")
            print(f"🌐 브라우저에서 접속해보세요!")
            print(f"🛑 서버 중지: Ctrl+C")
            print("=" * 50)
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 서버 중지됨")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")

if __name__ == "__main__":
    print("🍎 Mac AI Writer 서버 디버깅")
    print("=" * 50)
    
    # 네트워크 확인
    available_port = check_network()
    
    if available_port:
        start_simple_server(available_port)
    else:
        print("❌ 사용 가능한 포트를 찾을 수 없습니다.")
        
        # macOS 방화벽 확인 제안
        print("\n🔧 해결 방법:")
        print("1. 시스템 환경설정 → 보안 및 개인정보보호 → 방화벽")
        print("2. Terminal/Python에 대한 접근 허용 확인")
        print("3. 또는 sudo를 사용해보세요:")
        print("   sudo python3 mac_debug.py")