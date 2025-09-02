# 🍎 Mac에서 AI Writer 서버 실행 가이드

Mac에서 서버 연결 문제가 발생할 수 있는 원인과 해결 방법입니다.

## 🔍 문제 진단

### 1. 현재 상황 확인
```bash
# 포트 사용 확인
lsof -i :3001
lsof -i :3000

# 실행 중인 Python 프로세스 확인  
ps aux | grep python3
```

### 2. 네트워크 설정 확인
```bash
# localhost 해상도 확인
ping -c 1 localhost
ping -c 1 127.0.0.1

# 방화벽 상태 확인
sudo pfctl -s all
```

## 🚀 해결 방법

### 방법 1: 간단한 내장 서버 사용

```bash
# Python 내장 HTTP 서버로 테스트
cd /Users/sinseungho/contentByAI.io
python3 -m http.server 8001

# 브라우저에서 접속
# http://localhost:8001
```

### 방법 2: 디버그 서버 실행

```bash
# 네트워크 진단 포함 서버 시작
python3 mac_debug.py
```

### 방법 3: 권한으로 해결

```bash
# 관리자 권한으로 실행
sudo python3 test_server.py
```

### 방법 4: 다른 IP 주소 사용

```bash
# 모든 인터페이스에서 접근 허용
python3 -c "
import uvicorn
from test_server import app
uvicorn.run(app, host='0.0.0.0', port=8002)
"
```

## 🔧 Mac 특화 설정

### 1. 방화벽 설정

**시스템 환경설정 → 보안 및 개인정보보호 → 방화벽**

1. 방화벽 끄기 (테스트용)
2. 또는 Python/Terminal 앱에 네트워크 접근 허용

### 2. 네트워크 리셋

```bash
# DNS 캐시 클리어
sudo dscacheutil -flushcache

# 네트워크 인터페이스 리셋
sudo ifconfig lo0 down
sudo ifconfig lo0 up
```

### 3. 호스트 파일 확인

```bash
# /etc/hosts 파일 확인
cat /etc/hosts

# localhost가 다음과 같이 설정되어 있는지 확인:
# 127.0.0.1    localhost
# ::1          localhost
```

## 🧪 단계별 테스트

### 1단계: 가장 간단한 서버

```bash
# 터미널에서 실행
python3 -c "
import http.server
import socketserver

PORT = 8003

Handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(('127.0.0.1', PORT), Handler)

print(f'서버 시작: http://localhost:{PORT}')
print('Ctrl+C로 중지')
httpd.serve_forever()
"
```

### 2단계: FastAPI 서버

서버가 정상 시작되었다면:

```bash
# 새 터미널에서 테스트
curl http://localhost:8003/

# 브라우저에서도 테스트
open http://localhost:8003
```

### 3단계: AI Writer API 서버

```bash
# 최종 서버 실행
python3 test_server.py
```

## 📞 브라우저에서 직접 테스트

Safari나 Chrome에서 다음 URL들을 직접 입력해보세요:

1. **http://localhost:3001/health** 
2. **http://localhost:3001/docs**
3. **http://127.0.0.1:3001/health**

## 🔍 실시간 로그 확인

서버 실행 시 다음과 같은 로그가 나와야 합니다:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:3001 (Press CTRL+C to quit)
```

로그에서 "Started server process"가 보이면 서버는 정상 시작된 것입니다.

## ⚡ 빠른 해결 명령어

```bash
# 1. 모든 Python 프로세스 종료
pkill -f python3

# 2. 포트 정리
sudo lsof -ti:3001 | xargs sudo kill -9
sudo lsof -ti:3000 | xargs sudo kill -9

# 3. 간단한 테스트 서버 시작
python3 test_server.py

# 4. 브라우저에서 확인
open http://localhost:3001/health
```

## 🎯 최종 확인 방법

1. **터미널 1**: `python3 test_server.py` 실행
2. **터미널 2**: `curl http://localhost:3001/health` 테스트
3. **브라우저**: http://localhost:3001/health 접속

셋 중 하나라도 응답이 오면 서버는 정상 작동하는 것입니다!

## 🆘 여전히 안 될 때

Mac 시스템 특성상 다음을 시도해보세요:

```bash
# 1. Xcode Command Line Tools 재설치
xcode-select --install

# 2. Python 재설치 (Homebrew 사용)
brew reinstall python3

# 3. 네트워크 완전 리셋
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

---

이 가이드를 따라하시면 Mac에서도 AI Writer 서버가 정상 작동할 것입니다! 🚀