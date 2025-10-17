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
class WorkflowTemplate:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    steps: str = ""  # JSON string of workflow steps
    version: str = "v1.0"
    status: str = "active"  # active, inactive
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[int] = None

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

@dataclass
class ScheduledPost:
    id: Optional[int] = None
    schedule_id: str = ""  # UUID
    title: str = ""
    topic: Optional[str] = None  # 사용자 지정 주제 (없으면 트렌드 기반)
    topic_source: str = "user"  # user, trend
    schedule_time: str = ""  # ISO datetime
    status: str = "pending"  # pending, completed, failed, paused
    provider: str = "gemini"  # AI 제공자
    workflow_template_id: Optional[int] = None
    repeat_config: Optional[str] = None  # JSON string for repeat settings
    generated_job_id: Optional[str] = None  # 생성된 콘텐츠 작업 ID
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_executed_at: Optional[str] = None

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str  # Ensure UTF-8 text handling
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
                CREATE TABLE IF NOT EXISTS workflow_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    steps TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT 'v1.0',
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    topic TEXT,
                    topic_source TEXT NOT NULL DEFAULT 'user',
                    schedule_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    provider TEXT NOT NULL DEFAULT 'gemini',
                    workflow_template_id INTEGER,
                    repeat_config TEXT,
                    generated_job_id TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_executed_at TEXT,
                    FOREIGN KEY (workflow_template_id) REFERENCES workflow_templates (id),
                    FOREIGN KEY (generated_job_id) REFERENCES generation_jobs (job_id)
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

            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scheduled_posts_schedule_time 
                    ON scheduled_posts(schedule_time)
                """)
            except:
                pass

            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status 
                    ON scheduled_posts(status)
                """)
            except:
                pass
            
            conn.commit()

    def save_test_result(self, result: TestResult) -> int:
        """테스트 결과 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
            conn.execute("PRAGMA encoding = 'UTF-8'")  # Force UTF-8 encoding
            conn.execute("DELETE FROM login_sessions WHERE session_token = ?", (session_token,))
            conn.commit()

    def get_session_by_token(self, session_token: str):
        """토큰으로 세션 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str  # Ensure UTF-8 text handling
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
            conn.text_factory = str
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
            conn.text_factory = str
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
            conn.text_factory = str
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
            conn.text_factory = str
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
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("DELETE FROM bundles WHERE bundle_id = ?", (bundle_id,))
            conn.commit()
            return cursor.rowcount > 0

    # User management methods
    def get_all_users(self) -> List[User]:
        """모든 사용자 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = []
            for row in cursor.fetchall():
                users.append(User(
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
                ))
            return users

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
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

    def create_user_from_object(self, user: User) -> int:
        """새 사용자 생성 (User 객체 버전)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("""
                INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.username,
                user.password_hash,
                user.email,
                user.role,
                user.is_active,
                user.created_at,
                user.updated_at,
                user.expires_at
            ))
            conn.commit()
            return cursor.lastrowid

    def update_user(self, user: User) -> bool:
        """사용자 정보 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("""
                UPDATE users 
                SET username = ?, email = ?, role = ?, is_active = ?, 
                    updated_at = ?, expires_at = ?
                WHERE id = ?
            """, (
                user.username,
                user.email,
                user.role,
                user.is_active,
                user.updated_at,
                user.expires_at,
                user.id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """사용자 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            # 관련 세션도 함께 삭제
            conn.execute("DELETE FROM login_sessions WHERE user_id = ?", (user_id,))
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Workflow template management methods
    def get_all_workflow_templates(self) -> List[WorkflowTemplate]:
        """모든 워크플로우 템플릿 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM workflow_templates ORDER BY created_at DESC")
            templates = []
            for row in cursor.fetchall():
                templates.append(WorkflowTemplate(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    steps=row['steps'],
                    version=row['version'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    created_by=row['created_by']
                ))
            return templates

    def get_workflow_template_by_id(self, template_id: int) -> Optional[WorkflowTemplate]:
        """ID로 워크플로우 템플릿 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM workflow_templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
            
            if row:
                return WorkflowTemplate(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    steps=row['steps'],
                    version=row['version'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    created_by=row['created_by']
                )
            return None

    def create_workflow_template(self, template: WorkflowTemplate) -> int:
        """새 워크플로우 템플릿 생성"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("""
                INSERT INTO workflow_templates (name, description, steps, version, status, created_at, updated_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template.name,
                template.description,
                template.steps,
                template.version,
                template.status,
                template.created_at,
                template.updated_at,
                template.created_by
            ))
            conn.commit()
            return cursor.lastrowid

    def update_workflow_template(self, template: WorkflowTemplate) -> bool:
        """워크플로우 템플릿 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("""
                UPDATE workflow_templates 
                SET name = ?, description = ?, steps = ?, version = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (
                template.name,
                template.description,
                template.steps,
                template.version,
                template.status,
                template.updated_at,
                template.id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_workflow_template(self, template_id: int) -> bool:
        """워크플로우 템플릿 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("DELETE FROM workflow_templates WHERE id = ?", (template_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_active_workflow_templates(self) -> List[WorkflowTemplate]:
        """활성 워크플로우 템플릿만 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM workflow_templates WHERE status = 'active' ORDER BY created_at DESC")
            templates = []
            for row in cursor.fetchall():
                templates.append(WorkflowTemplate(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    steps=row['steps'],
                    version=row['version'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    created_by=row['created_by']
                ))
            return templates

    # Scheduled posts management methods
    def create_scheduled_post(self, scheduled_post: ScheduledPost) -> int:
        """예약 포스트 생성"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("""
                INSERT INTO scheduled_posts 
                (schedule_id, title, topic, topic_source, schedule_time, status, provider, 
                 workflow_template_id, repeat_config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scheduled_post.schedule_id,
                scheduled_post.title,
                scheduled_post.topic,
                scheduled_post.topic_source,
                scheduled_post.schedule_time,
                scheduled_post.status,
                scheduled_post.provider,
                scheduled_post.workflow_template_id,
                scheduled_post.repeat_config,
                scheduled_post.created_at or datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_scheduled_post(self, schedule_id: str) -> Optional[ScheduledPost]:
        """예약 포스트 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM scheduled_posts WHERE schedule_id = ?", (schedule_id,))
            row = cursor.fetchone()
            
            if row:
                return ScheduledPost(
                    id=row['id'],
                    schedule_id=row['schedule_id'],
                    title=row['title'],
                    topic=row['topic'],
                    topic_source=row['topic_source'],
                    schedule_time=row['schedule_time'],
                    status=row['status'],
                    provider=row['provider'],
                    workflow_template_id=row['workflow_template_id'],
                    repeat_config=row['repeat_config'],
                    generated_job_id=row['generated_job_id'],
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_executed_at=row['last_executed_at']
                )
            return None

    def list_scheduled_posts(self, status: Optional[str] = None, limit: int = 50) -> List[ScheduledPost]:
        """예약 포스트 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM scheduled_posts"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY schedule_time ASC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            
            scheduled_posts = []
            for row in cursor.fetchall():
                scheduled_posts.append(ScheduledPost(
                    id=row['id'],
                    schedule_id=row['schedule_id'],
                    title=row['title'],
                    topic=row['topic'],
                    topic_source=row['topic_source'],
                    schedule_time=row['schedule_time'],
                    status=row['status'],
                    provider=row['provider'],
                    workflow_template_id=row['workflow_template_id'],
                    repeat_config=row['repeat_config'],
                    generated_job_id=row['generated_job_id'],
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_executed_at=row['last_executed_at']
                ))
            return scheduled_posts

    def update_scheduled_post(self, scheduled_post: ScheduledPost) -> bool:
        """예약 포스트 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("""
                UPDATE scheduled_posts 
                SET title = ?, topic = ?, topic_source = ?, schedule_time = ?, status = ?, 
                    provider = ?, workflow_template_id = ?, repeat_config = ?, 
                    generated_job_id = ?, error_message = ?, updated_at = ?, last_executed_at = ?
                WHERE schedule_id = ?
            """, (
                scheduled_post.title,
                scheduled_post.topic,
                scheduled_post.topic_source,
                scheduled_post.schedule_time,
                scheduled_post.status,
                scheduled_post.provider,
                scheduled_post.workflow_template_id,
                scheduled_post.repeat_config,
                scheduled_post.generated_job_id,
                scheduled_post.error_message,
                datetime.now().isoformat(),
                scheduled_post.last_executed_at,
                scheduled_post.schedule_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_scheduled_post(self, schedule_id: str) -> bool:
        """예약 포스트 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            
            cursor = conn.execute("DELETE FROM scheduled_posts WHERE schedule_id = ?", (schedule_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_pending_scheduled_posts(self, current_time: str) -> List[ScheduledPost]:
        """실행 대기 중인 예약 포스트 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.text_factory = str
            conn.execute("PRAGMA encoding = 'UTF-8'")
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM scheduled_posts 
                WHERE status = 'pending' AND schedule_time <= ?
                ORDER BY schedule_time ASC
            """, (current_time,))
            
            scheduled_posts = []
            for row in cursor.fetchall():
                scheduled_posts.append(ScheduledPost(
                    id=row['id'],
                    schedule_id=row['schedule_id'],
                    title=row['title'],
                    topic=row['topic'],
                    topic_source=row['topic_source'],
                    schedule_time=row['schedule_time'],
                    status=row['status'],
                    provider=row['provider'],
                    workflow_template_id=row['workflow_template_id'],
                    repeat_config=row['repeat_config'],
                    generated_job_id=row['generated_job_id'],
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_executed_at=row['last_executed_at']
                ))
            return scheduled_posts


# 전역 데이터베이스 인스턴스
db = DatabaseManager()

if __name__ == "__main__":
    # 테스트 데이터 생성
    print("[INFO] 데이터베이스 초기화 중...")
    
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
    
    print("[OK] 데이터베이스 초기화 완료!")
    print(f"[INFO] 저장된 테스트 결과: {len(sample_results)}개")
    
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
        print("[OK] admin 계정 생성됨")
        
        # validator 계정 (1년 유효)
        validator_expires = (datetime.now() + timedelta(days=365)).isoformat()
        db.create_user(
            username="validator",
            password="validator123",
            email="validator@aiwriter.com",
            role="validator",
            expires_at=validator_expires
        )
        print("[OK] validator 계정 생성됨")
        
        # 테스트 계정 (30일 유효)
        test_expires = (datetime.now() + timedelta(days=30)).isoformat()
        db.create_user(
            username="testuser",
            password="test123",
            email="test@aiwriter.com",
            role="user",
            expires_at=test_expires
        )
        print("[OK] testuser 계정 생성됨")
        
    except Exception as e:
        print(f"[WARN] 사용자 생성 중 오류 (이미 존재할 수 있음): {e}")
    
    # 기본 워크플로우 템플릿 생성
    try:
        basic_blog_steps = [
            {
                "name": "기본 블로그 포스트 생성",
                "prompt_template": "다음 주제로 전문적이고 유익한 블로그 포스트를 작성해주세요: {topic}. 독자에게 실용적인 가치를 제공하고, SEO에 최적화된 구조로 작성해주세요.",
                "approver_role": "editor",
                "auto_transition": True
            }
        ]
        
        social_media_steps = [
            {
                "name": "소셜 미디어 포스트",
                "prompt_template": "다음 주제로 소셜 미디어용 매력적이고 간결한 포스트를 작성해주세요: {topic}. 독자의 관심을 끌고 상호작용을 유도하는 내용으로 작성해주세요.",
                "approver_role": "editor", 
                "auto_transition": True
            }
        ]
        
        # 여행 정보전달 템플릿
        travel_steps = [
            {
                "name": "여행 정보 콘텐츠 생성",
                "prompt_template": """다음 여행 주제로 전문적이고 실용적인 여행 가이드를 작성해주세요: {topic}

작성 요구사항:
- 여행자의 실제 경험과 팁 중심으로 작성
- 구체적인 장소, 가격, 시간 정보 포함
- 계절별/시간대별 특징과 추천사항
- 현지 문화와 예절 정보 포함
- 교통편, 숙박, 맛집 등 실용 정보 제공
- 주의사항과 안전 정보 포함
- 예산 가이드라인 제시
- 현지인 추천 명소나 숨은 장소 소개

독자가 실제 여행 계획을 세울 때 바로 활용할 수 있는 구체적이고 유용한 정보로 구성해주세요.""",
                "approver_role": "editor",
                "auto_transition": True
            }
        ]

        # 시사 정보전달 템플릿
        news_steps = [
            {
                "name": "시사 정보 콘텐츠 생성",
                "prompt_template": """다음 시사 주제로 균형잡히고 객관적인 정보 전달 콘텐츠를 작성해주세요: {topic}

작성 요구사항:
- 사실에 기반한 객관적 정보 전달
- 다양한 관점과 의견 균형있게 제시
- 배경 정보와 맥락 상세히 설명
- 관련 통계와 데이터 활용
- 전문가 의견이나 분석 인용
- 일반인이 이해하기 쉬운 설명
- 논란이 있는 부분은 여러 시각 제시
- 향후 전망과 예상 영향 분석
- 관련 법률이나 정책 정보 포함

독자가 해당 시사 이슈를 정확히 이해하고 균형잡힌 시각을 가질 수 있도록 작성해주세요.""",
                "approver_role": "editor",
                "auto_transition": True
            }
        ]

        # 기본 블로그 템플릿
        basic_template = WorkflowTemplate(
            name="기본 블로그 포스트",
            description="일반적인 블로그 포스트 생성을 위한 기본 템플릿",
            steps=json.dumps(basic_blog_steps),
            version="v1.0",
            status="inactive",  # 새로운 전문 템플릿들을 우선 사용하도록 비활성화
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by=1
        )
        
        # 여행 정보전달 템플릿
        travel_template = WorkflowTemplate(
            name="여행 정보전달",
            description="여행 가이드 및 여행 정보 콘텐츠 전문 생성 템플릿",
            steps=json.dumps(travel_steps),
            version="v1.0", 
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by=1
        )

        # 시사 정보전달 템플릿
        news_template = WorkflowTemplate(
            name="시사 정보전달",
            description="시사 이슈 및 뉴스 정보 객관적 전달 템플릿",
            steps=json.dumps(news_steps),
            version="v1.0", 
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by=1
        )
        
        # 소셜 미디어 템플릿
        social_template = WorkflowTemplate(
            name="소셜 미디어 포스트",
            description="SNS용 짧고 매력적인 포스트 생성 템플릿",
            steps=json.dumps(social_media_steps),
            version="v1.0", 
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by=1
        )
        
        db.create_workflow_template(basic_template)
        db.create_workflow_template(travel_template)
        db.create_workflow_template(news_template)
        db.create_workflow_template(social_template)
        print("[OK] 기본 워크플로우 템플릿 생성됨")
        
    except Exception as e:
        print(f"[WARN] 워크플로우 템플릿 생성 중 오류 (이미 존재할 수 있음): {e}")
    
    print("\n[INFO] 기본 계정 정보:")
    print("   - admin / admin123! (관리자, 무제한)")
    print("   - validator / validator123 (검증자, 1년)")
    print("   - testuser / test123 (사용자, 30일)")
    
    # 통계 확인
    for provider in ["gemini", "claude", "openai", "grok"]:
        stats = db.get_provider_stats(provider)
        print(f"[STATS] {provider}: {stats['total_tests']}회 테스트, {stats['success_rate']}% 성공률")