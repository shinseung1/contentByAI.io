#!/usr/bin/env python3
"""
데이터베이스 설정 및 모델 정의
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import os

DATABASE_PATH = "data/aiwriter.db"

@dataclass
class TestResult:
    id: Optional[int] = None
    provider: str = ""
    prompt: str = ""
    response: str = ""
    success: bool = True
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    email: Optional[str] = None
    role: str = "user"  # admin, user, validator
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None  # 계정 유효 기간
    last_login: Optional[str] = None
    login_attempts: int = 0
    locked_until: Optional[str] = None

@dataclass
class LoginSession:
    id: Optional[int] = None
    user_id: int = 0
    session_token: str = ""
    expires_at: str = ""
    created_at: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class GenerationJob:
    id: Optional[int] = None
    job_id: str = ""
    provider: str = ""
    topic: str = ""
    tone: str = ""
    word_count: int = 800
    include_images: bool = True
    target_language: str = "ko"
    status: str = "pending"  # pending, in_progress, completed, failed
    progress: int = 0
    content: Optional[str] = None
    html_content: Optional[str] = None
    markdown_content: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass  
class ImageCache:
    id: Optional[int] = None
    url_hash: str = ""  # URL의 해시값
    original_url: str = ""
    alt_text: str = ""
    caption: str = ""
    image_data: bytes = b""  # 이미지 바이너리 데이터
    mime_type: str = ""  # image/jpeg, image/png 등
    file_size: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: Optional[str] = None
    last_accessed: Optional[str] = None
    access_count: int = 0

@dataclass
class Bundle:
    id: Optional[int] = None
    bundle_id: str = ""  # UUID
    title: str = ""
    description: Optional[str] = None
    status: str = "draft"  # draft, published, archived
    post_count: int = 0
    total_views: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    published_at: Optional[str] = None
    metadata: Optional[str] = None  # JSON string for additional data

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT,
                    success BOOLEAN NOT NULL DEFAULT 1,
                    error_message TEXT,
                    token_usage TEXT,  -- JSON string
                    response_time_ms INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    last_login TEXT,
                    login_attempts INTEGER NOT NULL DEFAULT 0,
                    locked_until TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS generation_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    provider TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    tone TEXT NOT NULL DEFAULT 'professional',
                    word_count INTEGER NOT NULL DEFAULT 800,
                    include_images BOOLEAN NOT NULL DEFAULT 1,
                    target_language TEXT NOT NULL DEFAULT 'ko',
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress INTEGER NOT NULL DEFAULT 0,
                    content TEXT,
                    html_content TEXT,
                    markdown_content TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    alt_text TEXT NOT NULL DEFAULT '',
                    caption TEXT NOT NULL DEFAULT '',
                    image_data BLOB NOT NULL,
                    mime_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    width INTEGER,
                    height INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER NOT NULL DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_results_provider 
                ON test_results(provider)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_results_created_at 
                ON test_results(created_at DESC)
            """)
            
            # 인덱스는 테이블 생성 후에 만들어야 함
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generation_jobs_job_id 
                    ON generation_jobs(job_id)
                """)
            except:
                pass  # 테이블이 없으면 무시
            
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generation_jobs_status 
                    ON generation_jobs(status)
                """)
            except:
                pass  # 테이블이 없으면 무시
            
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_image_cache_url_hash 
                    ON image_cache(url_hash)
                """)
            except:
                pass  # 테이블이 없으면 무시
            
            conn.commit()

    def save_test_result(self, result: TestResult) -> int:
        """테스트 결과 저장"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            cursor = conn.execute("""
                INSERT INTO test_results 
                (provider, prompt, response, success, error_message, token_usage, response_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.provider,
                result.prompt,
                result.response,
                result.success,
                result.error_message,
                json.dumps(result.token_usage) if result.token_usage else None,
                result.response_time_ms,
                result.created_at or datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_test_results(self, provider: Optional[str] = None, limit: int = 50) -> List[TestResult]:
        """테스트 결과 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.row_factory = sqlite3.Row
            
            if provider:
                cursor = conn.execute("""
                    SELECT * FROM test_results 
                    WHERE provider = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (provider, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM test_results 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                token_usage = None
                if row['token_usage']:
                    try:
                        token_usage = json.loads(row['token_usage'])
                    except:
                        pass
                
                results.append(TestResult(
                    id=row['id'],
                    provider=row['provider'],
                    prompt=row['prompt'],
                    response=row['response'],
                    success=bool(row['success']),
                    error_message=row['error_message'],
                    token_usage=token_usage,
                    response_time_ms=row['response_time_ms'],
                    created_at=row['created_at']
                ))
            
            return results

    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """제공자별 통계 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_tests,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_tests,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(created_at) as last_test_at
                FROM test_results 
                WHERE provider = ?
            """, (provider,))
            
            row = cursor.fetchone()
            if row:
                total_tests = row[0] or 0
                successful_tests = row[1] or 0
                success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
                
                return {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': total_tests - successful_tests,
                    'success_rate': round(success_rate, 1),
                    'avg_response_time': round(row[2] or 0, 1),
                    'last_test_at': row[3]
                }
            
            return {
                'total_tests': 0,
                'successful_tests': 0,
                'failed_tests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'last_test_at': None
            }

    def save_generation_job(self, job: GenerationJob) -> int:
        """콘텐츠 생성 작업 저장"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            cursor = conn.execute("""
                INSERT OR REPLACE INTO generation_jobs 
                (job_id, provider, topic, tone, word_count, include_images, target_language, 
                 status, progress, content, html_content, markdown_content, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.provider,
                job.topic,
                job.tone,
                job.word_count,
                job.include_images,
                job.target_language,
                job.status,
                job.progress,
                job.content,
                job.html_content,
                job.markdown_content,
                job.error_message,
                job.created_at or datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_generation_job(self, job_id: str) -> Optional[GenerationJob]:
        """콘텐츠 생성 작업 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM generation_jobs WHERE job_id = ?
            """, (job_id,))
            
            row = cursor.fetchone()
            if row:
                return GenerationJob(
                    id=row['id'],
                    job_id=row['job_id'],
                    provider=row['provider'],
                    topic=row['topic'],
                    tone=row['tone'],
                    word_count=row['word_count'],
                    include_images=bool(row['include_images']),
                    target_language=row['target_language'],
                    status=row['status'],
                    progress=row['progress'],
                    content=row['content'],
                    html_content=row['html_content'] if 'html_content' in row.keys() else None,
                    markdown_content=row['markdown_content'] if 'markdown_content' in row.keys() else None,
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None

    def get_generation_jobs(self, provider: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[GenerationJob]:
        """콘텐츠 생성 작업 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM generation_jobs WHERE 1=1"
            params = []
            
            if provider:
                query += " AND provider = ?"
                params.append(provider)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            
            jobs = []
            for row in cursor.fetchall():
                jobs.append(GenerationJob(
                    id=row['id'],
                    job_id=row['job_id'],
                    provider=row['provider'],
                    topic=row['topic'],
                    tone=row['tone'],
                    word_count=row['word_count'],
                    include_images=bool(row['include_images']),
                    target_language=row['target_language'],
                    status=row['status'],
                    progress=row['progress'],
                    content=row['content'],
                    html_content=row['html_content'] if 'html_content' in row.keys() else None,
                    markdown_content=row['markdown_content'] if 'markdown_content' in row.keys() else None,
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            
            return jobs

    def update_generation_job_status(self, job_id: str, status: str, progress: int = 0, 
                                   content: Optional[str] = None, error_message: Optional[str] = None):
        """콘텐츠 생성 작업 상태 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.execute("""
                UPDATE generation_jobs 
                SET status = ?, progress = ?, content = ?, error_message = ?, updated_at = ?
                WHERE job_id = ?
            """, (status, progress, content, error_message, datetime.now().isoformat(), job_id))
            conn.commit()

    def save_image_cache(self, image_cache: ImageCache) -> int:
        """이미지 캐시 저장"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            cursor = conn.execute("""
                INSERT OR REPLACE INTO image_cache 
                (url_hash, original_url, alt_text, caption, image_data, mime_type, 
                 file_size, width, height, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                image_cache.url_hash,
                image_cache.original_url,
                image_cache.alt_text,
                image_cache.caption,
                image_cache.image_data,
                image_cache.mime_type,
                image_cache.file_size,
                image_cache.width,
                image_cache.height,
                image_cache.created_at or datetime.now().isoformat(),
                datetime.now().isoformat(),
                image_cache.access_count
            ))
            conn.commit()
            return cursor.lastrowid

    def get_image_cache(self, url_hash: str) -> Optional[ImageCache]:
        """이미지 캐시 조회 및 액세스 카운트 증가"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.row_factory = sqlite3.Row
            
            # 캐시된 이미지 조회
            cursor = conn.execute("""
                SELECT * FROM image_cache WHERE url_hash = ?
            """, (url_hash,))
            
            row = cursor.fetchone()
            if row:
                # 액세스 카운트 증가
                conn.execute("""
                    UPDATE image_cache 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE url_hash = ?
                """, (datetime.now().isoformat(), url_hash))
                conn.commit()
                
                return ImageCache(
                    id=row['id'],
                    url_hash=row['url_hash'],
                    original_url=row['original_url'],
                    alt_text=row['alt_text'],
                    caption=row['caption'],
                    image_data=row['image_data'],
                    mime_type=row['mime_type'],
                    file_size=row['file_size'],
                    width=row['width'],
                    height=row['height'],
                    created_at=row['created_at'],
                    last_accessed=row['last_accessed'],
                    access_count=row['access_count'] + 1
                )
            return None

    def cleanup_old_images(self, days_old: int = 30, max_size_mb: int = 100):
        """오래된 이미지 캐시 정리"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            from datetime import datetime, timedelta
            
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # 오래된 이미지 삭제
            conn.execute("""
                DELETE FROM image_cache 
                WHERE last_accessed < ? AND access_count < 5
            """, (cutoff_date,))
            
            # 크기 제한 체크 (MB 단위)
            max_size_bytes = max_size_mb * 1024 * 1024
            total_size = conn.execute("""
                SELECT SUM(file_size) as total FROM image_cache
            """).fetchone()[0] or 0
            
            if total_size > max_size_bytes:
                # 액세스가 적은 오래된 이미지부터 삭제
                conn.execute("""
                    DELETE FROM image_cache 
                    WHERE id IN (
                        SELECT id FROM image_cache 
                        ORDER BY access_count ASC, last_accessed ASC 
                        LIMIT (
                            SELECT COUNT(*) / 4 FROM image_cache
                        )
                    )
                """)
            
            conn.commit()

    def create_user(self, username: str, password: str, email: Optional[str] = None, 
                   role: str = "user", expires_at: Optional[str] = None) -> int:
        """사용자 생성"""
        import hashlib
        import secrets
        
        # 비밀번호 해시 생성
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        password_hash_string = salt + ":" + password_hash.hex()
        
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            cursor = conn.execute("""
                INSERT INTO users (username, password_hash, email, role, expires_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                password_hash_string,
                email,
                role,
                expires_at,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def verify_user_password(self, username: str, password: str) -> tuple[bool, Optional[User], str]:
        """사용자 비밀번호 검증 및 상태 확인"""
        import hashlib
        from datetime import datetime
        
        try:
            user = self.get_user_by_username(username)
            if not user:
                return False, None, "등록되지 않은 사용자입니다"
            
            # 계정 잠김 확인
            if user.locked_until:
                lock_time = datetime.fromisoformat(user.locked_until)
                if datetime.now() < lock_time:
                    return False, user, "계정이 잠겨있습니다. 나중에 시도해주세요"
            
            # 계정 활성 상태 확인
            if not user.is_active:
                return False, user, "비활성화된 계정입니다"
            
            # 계정 만료 확인
            if user.expires_at:
                expire_time = datetime.fromisoformat(user.expires_at)
                if datetime.now() > expire_time:
                    return False, user, "유효한 사용자가 아닙니다"
            
            # 비밀번호 검증
            try:
                salt, stored_hash = user.password_hash.split(":", 1)
                password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                
                if password_hash.hex() == stored_hash:
                    # 로그인 성공 - 정보 업데이트
                    self.update_user_login_success(user.id)
                    return True, user, "로그인 성공"
                else:
                    # 비밀번호 틀림 - 실패 횟수 증가
                    self.increment_login_attempts(user.id)
                    return False, user, "아이디 패스워드가 틀립니다"
            except ValueError:
                return False, user, "아이디 패스워드가 틀립니다"
                
        except Exception as e:
            print(f"Login verification error: {e}")
            return False, None, "로그인 처리 중 오류가 발생했습니다"

    def get_user_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM users WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    password_hash=row['password_hash'],
                    email=row['email'],
                    role=row['role'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    expires_at=row['expires_at'],
                    last_login=row['last_login'],
                    login_attempts=row['login_attempts'],
                    locked_until=row['locked_until']
                )
            return None

    def update_user_login_success(self, user_id: int):
        """로그인 성공 시 정보 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.execute("""
                UPDATE users 
                SET last_login = ?, login_attempts = 0, locked_until = NULL, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), datetime.now().isoformat(), user_id))
            conn.commit()

    def increment_login_attempts(self, user_id: int):
        """로그인 실패 횟수 증가 및 계정 잠김 처리"""
        from datetime import timedelta
        
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            # 현재 실패 횟수 조회
            cursor = conn.execute("SELECT login_attempts FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                attempts = row[0] + 1
                
                # 5회 실패 시 30분 잠김
                locked_until = None
                if attempts >= 5:
                    locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                
                conn.execute("""
                    UPDATE users 
                    SET login_attempts = ?, locked_until = ?, updated_at = ?
                    WHERE id = ?
                """, (attempts, locked_until, datetime.now().isoformat(), user_id))
                conn.commit()

    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """로그인 세션 생성"""
        import secrets
        from datetime import timedelta
        
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.execute("""
                INSERT INTO login_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, session_token, expires_at, ip_address, user_agent))
            conn.commit()
            
        return session_token

    def validate_session(self, session_token: str) -> Optional[User]:
        """세션 토큰 검증"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT u.*, s.expires_at as session_expires
                FROM users u
                JOIN login_sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.expires_at > ?
            """, (session_token, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    password_hash=row['password_hash'],
                    email=row['email'],
                    role=row['role'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    expires_at=row['expires_at'],
                    last_login=row['last_login'],
                    login_attempts=row['login_attempts'],
                    locked_until=row['locked_until']
                )
            return None

    def delete_session(self, session_token: str):
        """세션 삭제 (로그아웃)"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.execute("DELETE FROM login_sessions WHERE session_token = ?", (session_token,))
            conn.commit()

    def get_session_by_token(self, session_token: str):
        """토큰으로 세션 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT u.username, s.expires_at
                FROM users u
                JOIN login_sessions s ON u.id = s.user_id
                WHERE s.session_token = ?
            """, (session_token,))
            
            row = cursor.fetchone()
            if row:
                return type('Session', (), {
                    'username': row['username'],
                    'expires_at': row['expires_at']
                })()
            return None

    def reset_failed_attempts(self, username: str):
        """로그인 실패 횟수 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.execute("""
                UPDATE users 
                SET login_attempts = 0, locked_until = NULL, updated_at = ?
                WHERE username = ?
            """, (datetime.now().isoformat(), username))
            conn.commit()

    # Bundle management methods
    def create_bundle(self, bundle_id: str, title: str, description: str = None, metadata: dict = None) -> int:
        """번들 생성"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            # Create bundles table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bundles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bundle_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'draft',
                    post_count INTEGER NOT NULL DEFAULT 0,
                    total_views INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    published_at TEXT,
                    metadata TEXT
                )
            """)
            
            cursor = conn.execute("""
                INSERT INTO bundles (bundle_id, title, description, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                bundle_id,
                title,
                description,
                json.dumps(metadata) if metadata else None,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_bundle(self, bundle_id: str) -> Optional[Bundle]:
        """번들 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM bundles WHERE bundle_id = ?", (bundle_id,))
            row = cursor.fetchone()
            
            if row:
                return Bundle(
                    id=row['id'],
                    bundle_id=row['bundle_id'],
                    title=row['title'],
                    description=row['description'],
                    status=row['status'],
                    post_count=row['post_count'],
                    total_views=row['total_views'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    published_at=row['published_at'],
                    metadata=row['metadata']
                )
            return None

    def list_bundles(self, limit: int = 50, offset: int = 0) -> List[Bundle]:
        """번들 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM bundles 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            bundles = []
            for row in cursor.fetchall():
                bundles.append(Bundle(
                    id=row['id'],
                    bundle_id=row['bundle_id'],
                    title=row['title'],
                    description=row['description'],
                    status=row['status'],
                    post_count=row['post_count'],
                    total_views=row['total_views'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    published_at=row['published_at'],
                    metadata=row['metadata']
                ))
            return bundles

    def update_bundle(self, bundle_id: str, title: str = None, description: str = None, 
                     status: str = None, metadata: dict = None) -> bool:
        """번들 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
            
            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(bundle_id)
                
                query = f"UPDATE bundles SET {', '.join(updates)} WHERE bundle_id = ?"
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            return False

    def delete_bundle(self, bundle_id: str) -> bool:
        """번들 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("DELETE FROM bundles WHERE bundle_id = ?", (bundle_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드용 통계 데이터 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            # 오늘 생성 건수
            today = datetime.now().date().isoformat()
            today_jobs = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE DATE(created_at) = ?
            """, (today,)).fetchone()[0]
            
            # 실패/재시도 건수 (오늘)
            failed_jobs = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE DATE(created_at) = ? AND status = 'failed'
            """, (today,)).fetchone()[0]
            
            # 진행중인 작업 수
            in_progress_jobs = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE status = 'in_progress'
            """, ).fetchone()[0]
            
            # 전체 완료된 작업 수
            completed_jobs = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE status = 'completed'
            """, ).fetchone()[0]
            
            # 활성 사용자 수
            active_users = conn.execute("""
                SELECT COUNT(*) FROM users 
                WHERE is_active = 1
            """, ).fetchone()[0]
            
            # 프로바이더별 통계
            provider_stats = {}
            providers = ['gemini', 'claude', 'openai']
            for provider in providers:
                count = conn.execute("""
                    SELECT COUNT(*) FROM generation_jobs 
                    WHERE provider = ?
                """, (provider,)).fetchone()[0]
                provider_stats[provider] = count
            
            return {
                'today_jobs': today_jobs,
                'failed_jobs': failed_jobs,
                'in_progress_jobs': in_progress_jobs,
                'completed_jobs': completed_jobs,
                'active_users': active_users,
                'provider_stats': provider_stats,
                'estimated_cost': self._calculate_estimated_cost()
            }
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 활동 조회"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT job_id, provider, topic, status, error_message, created_at, updated_at
                FROM generation_jobs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            activities = []
            for row in cursor.fetchall():
                action = "콘텐츠 생성 완료" if row['status'] == 'completed' else \
                        "콘텐츠 생성 실패" if row['status'] == 'failed' else \
                        "콘텐츠 생성 중"
                
                activities.append({
                    'id': row['job_id'],
                    'action': action,
                    'user': 'system',  # 실제 사용자 정보가 있다면 조인해서 가져오기
                    'model': row['provider'],
                    'topic': row['topic'][:50] + '...' if len(row['topic']) > 50 else row['topic'],
                    'status': 'success' if row['status'] == 'completed' else 
                             'error' if row['status'] == 'failed' else 'warning',
                    'timestamp': self._format_timestamp(row['created_at']),
                    'error_message': row['error_message']
                })
            
            return activities
    
    def _calculate_estimated_cost(self) -> float:
        """예상 비용 계산 (대략적)"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            # 간단한 예상 비용 계산 (완료된 작업 수 * 평균 비용)
            completed_count = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE status = 'completed'
            """).fetchone()[0]
            
            # 대략적인 평균 비용 (실제로는 토큰 사용량 기반으로 계산해야 함)
            avg_cost_per_job = 0.05  # $0.05 per job
            
            return completed_count * avg_cost_per_job
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """타임스탬프를 상대적 시간으로 변환"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            diff = now - timestamp
            
            if diff.days > 0:
                return f"{diff.days}일 전"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}시간 전"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}분 전"
            else:
                return "방금 전"
        except:
            return "알 수 없음"

    def get_dashboard_alerts(self) -> List[Dict[str, Any]]:
        """대시보드 알림 생성 (실제 시스템 상태 기반)"""
        alerts = []
        
        with sqlite3.connect(self.db_path) as conn:
            # SQLite default text handling is already Unicode in Python 3
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            today = datetime.now().date().isoformat()
            
            # 1. 최근 실패 작업 확인 (상세 정보 포함)
            failed_jobs = conn.execute("""
                SELECT provider, COUNT(*) as count, 
                       GROUP_CONCAT(DISTINCT error_message) as errors
                FROM generation_jobs 
                WHERE DATE(created_at) = ? AND status = 'failed'
                GROUP BY provider
            """, (today,)).fetchall()
            
            total_failed = sum(row[1] for row in failed_jobs)
            if total_failed > 0:
                error_details = []
                for provider, count, errors in failed_jobs:
                    if errors and '401 Unauthorized' in errors:
                        error_details.append(f"{provider.upper()}: API 키 인증 실패 ({count}건)")
                    elif errors and 'rate limit' in errors.lower():
                        error_details.append(f"{provider.upper()}: 요청 한도 초과 ({count}건)")
                    else:
                        error_details.append(f"{provider.upper()}: {count}건 실패")
                
                alerts.append({
                    'type': 'error',
                    'message': f'오늘 총 {total_failed}건의 콘텐츠 생성 실패',
                    'details': error_details,
                    'action': 'API 설정 확인'
                })
            
            # 2. 토큰 사용량 분석
            total_jobs_today = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE DATE(created_at) = ?
            """, (today,)).fetchone()[0]
            
            estimated_tokens = total_jobs_today * 1500  # 평균 토큰 수 추정
            estimated_cost = self._calculate_estimated_cost()
            
            if estimated_cost > 5.0:  # $5 이상
                alerts.append({
                    'type': 'warning',
                    'message': f'오늘 예상 비용이 ${estimated_cost:.2f}에 도달했습니다',
                    'details': [f'총 {total_jobs_today}건 생성', f'추정 토큰: {estimated_tokens:,}개'],
                    'action': '사용량 조정'
                })
            
            # 3. 프로바이더별 성능 및 할당량 상태
            providers = ['gemini', 'claude', 'openai']
            for provider in providers:
                provider_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_jobs,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                        AVG(CASE WHEN status = 'completed' THEN 1.0 ELSE 0.0 END) * 100 as success_rate
                    FROM generation_jobs 
                    WHERE DATE(created_at) = ? AND provider = ?
                """, (today, provider)).fetchone()
                
                total, completed, failed, success_rate = provider_stats
                
                if total > 0:
                    if success_rate < 70:  # 성공률 70% 미만
                        alerts.append({
                            'type': 'warning',
                            'message': f'{provider.upper()} 프로바이더 성능 저하',
                            'details': [
                                f'성공률: {success_rate:.1f}%',
                                f'완료: {completed}건, 실패: {failed}건'
                            ],
                            'action': 'API 상태 점검'
                        })
                    elif success_rate > 95 and total >= 5:  # 성공률 95% 이상
                        alerts.append({
                            'type': 'success',
                            'message': f'{provider.upper()} 프로바이더 우수한 성능',
                            'details': [
                                f'성공률: {success_rate:.1f}%',
                                f'총 {total}건 처리'
                            ],
                            'action': '계속 사용'
                        })
            
            # 4. 진행중인 작업 모니터링
            in_progress_count = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE status = 'in_progress'
            """, ).fetchone()[0]
            
            if in_progress_count > 5:
                # 진행중인 작업의 시작 시간 확인
                old_jobs = conn.execute("""
                    SELECT COUNT(*) FROM generation_jobs 
                    WHERE status = 'in_progress' AND 
                          datetime(created_at) < datetime('now', '-30 minutes')
                """, ).fetchone()[0]
                
                if old_jobs > 0:
                    alerts.append({
                        'type': 'error',
                        'message': f'{old_jobs}개의 작업이 30분 이상 진행 중입니다',
                        'details': [f'전체 진행중: {in_progress_count}건'],
                        'action': '작업 상태 확인 필요'
                    })
                else:
                    alerts.append({
                        'type': 'info',
                        'message': f'{in_progress_count}개의 작업이 정상적으로 진행 중입니다',
                        'action': '상태 모니터링'
                    })
            
            # 5. 일일 할당량 및 성과 요약
            completed_today = conn.execute("""
                SELECT COUNT(*) FROM generation_jobs 
                WHERE DATE(created_at) = ? AND status = 'completed'
            """, (today,)).fetchone()[0]
            
            if completed_today > 20:  # 높은 생산성
                alerts.append({
                    'type': 'success',
                    'message': f'오늘 {completed_today}건의 고품질 콘텐츠 생성 완료',
                    'details': [
                        f'실패율: {(total_failed/(completed_today+total_failed)*100):.1f}%' if completed_today+total_failed > 0 else '실패율: 0%',
                        f'예상 비용: ${estimated_cost:.2f}'
                    ],
                    'action': '성과 분석'
                })
            
            # 6. 사용자 활동 및 시스템 부하
            active_users = conn.execute("""
                SELECT COUNT(*) FROM users 
                WHERE is_active = 1
            """, ).fetchone()[0]
            
            if active_users == 0:
                alerts.append({
                    'type': 'warning',
                    'message': '활성 사용자가 없습니다',
                    'details': ['시스템 사용률 0%'],
                    'action': '사용자 활성화 필요'
                })
            elif total_jobs_today / max(active_users, 1) > 10:  # 사용자당 10건 이상
                alerts.append({
                    'type': 'info',
                    'message': f'높은 사용률: 사용자당 평균 {total_jobs_today/active_users:.1f}건 생성',
                    'details': [f'활성 사용자: {active_users}명'],
                    'action': '리소스 확장 고려'
                })
        
        # 기본 알림이 없으면 시스템 정상 메시지 추가
        if not alerts:
            alerts.append({
                'type': 'success',
                'message': '모든 시스템이 정상 작동 중입니다',
                'details': ['오류 없음', '정상 성능'],
                'action': '상태 유지'
            })
        
        return alerts


# 전역 데이터베이스 인스턴스
db = DatabaseManager()

if __name__ == "__main__":
    # 테스트 데이터 생성
    print("🗄️  데이터베이스 초기화 중...")
    
    # 샘플 테스트 결과 저장
    sample_results = [
        TestResult(
            provider="gemini",
            prompt="안녕하세요! 간단한 인사말로 답해주세요.",
            response="안녕하세요! 좋은 하루 되세요!",
            success=True,
            token_usage={"promptTokenCount": 10, "candidatesTokenCount": 8, "totalTokenCount": 18},
            response_time_ms=1250,
            created_at=datetime.now().isoformat()
        ),
        TestResult(
            provider="claude",
            prompt="AI의 미래에 대해 설명해주세요.",
            response="AI는 앞으로 더욱 발전하여...",
            success=True,
            token_usage={"input_tokens": 15, "output_tokens": 50, "total_tokens": 65},
            response_time_ms=2100,
            created_at=datetime.now().isoformat()
        )
    ]
    
    for result in sample_results:
        db.save_test_result(result)
    
    print("✅ 데이터베이스 초기화 완료!")
    print(f"📊 저장된 테스트 결과: {len(sample_results)}개")
    
    # 기본 사용자 생성
    from datetime import datetime, timedelta
    
    try:
        # admin 계정 (영구 사용)
        db.create_user(
            username="admin",
            password="admin123!",
            email="admin@aiwriter.com",
            role="admin",
            expires_at=None  # 만료 없음
        )
        print("👤 admin 계정 생성됨")
        
        # validator 계정 (1년 유효)
        validator_expires = (datetime.now() + timedelta(days=365)).isoformat()
        db.create_user(
            username="validator",
            password="validator123",
            email="validator@aiwriter.com",
            role="validator",
            expires_at=validator_expires
        )
        print("👤 validator 계정 생성됨")
        
        # 테스트 계정 (30일 유효)
        test_expires = (datetime.now() + timedelta(days=30)).isoformat()
        db.create_user(
            username="testuser",
            password="test123",
            email="test@aiwriter.com",
            role="user",
            expires_at=test_expires
        )
        print("👤 testuser 계정 생성됨")
        
    except Exception as e:
        print(f"⚠️  사용자 생성 중 오류 (이미 존재할 수 있음): {e}")
    
    print("\n🔑 기본 계정 정보:")
    print("   - admin / admin123! (관리자, 무제한)")
    print("   - validator / validator123 (검증자, 1년)")
    print("   - testuser / test123 (사용자, 30일)")
    
    # 통계 확인
    for provider in ["gemini", "claude", "openai", "grok"]:
        stats = db.get_provider_stats(provider)
        print(f"📈 {provider}: {stats['total_tests']}회 테스트, {stats['success_rate']}% 성공률")