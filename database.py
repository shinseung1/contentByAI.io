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
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
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
                    error_message TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
            
            conn.commit()

    def save_test_result(self, result: TestResult) -> int:
        """테스트 결과 저장"""
        with sqlite3.connect(self.db_path) as conn:
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
            cursor = conn.execute("""
                INSERT OR REPLACE INTO generation_jobs 
                (job_id, provider, topic, tone, word_count, include_images, target_language, 
                 status, progress, content, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                job.error_message,
                job.created_at or datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_generation_job(self, job_id: str) -> Optional[GenerationJob]:
        """콘텐츠 생성 작업 조회"""
        with sqlite3.connect(self.db_path) as conn:
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
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None

    def get_generation_jobs(self, provider: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[GenerationJob]:
        """콘텐츠 생성 작업 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
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
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            
            return jobs

    def update_generation_job_status(self, job_id: str, status: str, progress: int = 0, 
                                   content: Optional[str] = None, error_message: Optional[str] = None):
        """콘텐츠 생성 작업 상태 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE generation_jobs 
                SET status = ?, progress = ?, content = ?, error_message = ?, updated_at = ?
                WHERE job_id = ?
            """, (status, progress, content, error_message, datetime.now().isoformat(), job_id))
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
            conn.execute("""
                INSERT INTO login_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, session_token, expires_at, ip_address, user_agent))
            conn.commit()
            
        return session_token

    def validate_session(self, session_token: str) -> Optional[User]:
        """세션 토큰 검증"""
        with sqlite3.connect(self.db_path) as conn:
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
            conn.execute("DELETE FROM login_sessions WHERE session_token = ?", (session_token,))
            conn.commit()

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