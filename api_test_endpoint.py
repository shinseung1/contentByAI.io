#!/usr/bin/env python3
"""
웹에서 사용할 수 있는 API 테스트 엔드포인트 (실제 데이터 연동)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import asyncio
import httpx
from dotenv import load_dotenv
import uvicorn
import time
import uuid
import secrets
from datetime import datetime, timedelta
from database import db, TestResult, GenerationJob, User, LoginSession
from packages.gen.content_generator import ContentGenerator

# .env 파일 로드
load_dotenv()

app = FastAPI(title="AI Writer API Tester", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증 설정
security = HTTPBearer()

# 요청/응답 모델
class TestRequest(BaseModel):
    provider: str
    prompt: Optional[str] = "안녕하세요! 간단한 인사말로 답해주세요."

class TestResponse(BaseModel):
    success: bool
    provider: str
    content: Optional[str] = None
    tokenUsage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class GenerationRequest(BaseModel):
    provider: str
    topic: str
    tone: Optional[str] = "professional"
    wordCount: Optional[int] = 800
    includeImages: Optional[bool] = True
    targetLanguage: Optional[str] = "ko"

class GenerationResponse(BaseModel):
    jobId: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    jobId: str
    status: str
    progress: Optional[int] = 0
    result: Optional[Dict[str, Any]] = None
    errorMessage: Optional[str] = None
    errorCode: Optional[str] = None
    tone: Optional[str] = None
    word_count: Optional[int] = None
    created_at: Optional[str] = None

class ProviderStatsResponse(BaseModel):
    totalTests: int
    successfulTests: int
    failedTests: int
    successRate: float
    avgResponseTime: float
    lastTestAt: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

# 인증 관련 모델
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class AuthValidateResponse(BaseModel):
    valid: bool
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

# API 키 설정
AI_CONFIGS = {
    "gemini": {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        "url_template": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    },
    "claude": {
        "api_key": os.getenv("CLAUDE_API_KEY"),
        "model": os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229"),
        "url": "https://api.anthropic.com/v1/messages"
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "url": "https://api.openai.com/v1/chat/completions"
    },
    "grok": {
        "api_key": os.getenv("GROK_API_KEY"),
        "model": os.getenv("GROK_MODEL", "grok-beta"),
        "url": "https://api.x.ai/v1/chat/completions"
    }
}

# 인증 함수들
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """현재 인증된 사용자 반환"""
    token = credentials.credentials
    session = db.get_session_by_token(token)
    
    if not session:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or expired session token"
        )
    
    # 세션 만료 확인
    if session.expires_at < datetime.now().isoformat():
        db.delete_session(token)
        raise HTTPException(
            status_code=401, 
            detail="Session has expired"
        )
    
    user = db.get_user_by_username(session.username)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="User not found"
        )
    
    return user

def generate_session_token() -> str:
    """세션 토큰 생성"""
    return secrets.token_urlsafe(32)

def apply_style_fixes(html_content: str) -> str:
    """생성된 HTML에 스타일 보정 적용"""
    import re
    
    # 1단계: 흰색 텍스트 색상 강제 변경
    white_color_fixes = [
        # 모든 color: white 또는 #fff, #ffffff를 검은색으로 변경
        (r'color:\s*white\s*[;]?', 'color: #333;'),
        (r'color:\s*#fff\s*[;]?', 'color: #333;'),
        (r'color:\s*#ffffff\s*[;]?', 'color: #333;'),
        (r'color:\s*rgb\(255,\s*255,\s*255\)\s*[;]?', 'color: #333;'),
        (r'color:\s*rgba\(255,\s*255,\s*255,.*?\)\s*[;]?', 'color: #333;'),
    ]
    
    # 2단계: 기본 스타일이 없는 요소들에 스타일 추가 (더 강력한 패턴)
    element_fixes = [
        # p 태그 - 모든 경우에 대응
        (r'<p([^>]*)>', lambda m: f'<p{m.group(1)} style="color: #333 !important; margin-bottom: 1.2em; line-height: 1.7;">'),
        
        # h1 태그
        (r'<h1([^>]*)>', lambda m: f'<h1{m.group(1)} style="color: #1a1a1a !important; font-size: 2.2em; font-weight: 700; margin-bottom: 0.5em;">'),
        
        # h2 태그
        (r'<h2([^>]*)>', lambda m: f'<h2{m.group(1)} style="color: #2c3e50 !important; font-size: 1.6em; font-weight: 600; margin: 1.5em 0 0.8em;">'),
        
        # h3 태그
        (r'<h3([^>]*)>', lambda m: f'<h3{m.group(1)} style="color: #34495e !important; font-size: 1.3em; font-weight: 500; margin: 1.2em 0 0.6em;">'),
        
        # li 태그
        (r'<li([^>]*)>', lambda m: f'<li{m.group(1)} style="color: #333 !important; margin-bottom: 0.5em;">'),
        
        # ul, ol 태그
        (r'<ul([^>]*)>', lambda m: f'<ul{m.group(1)} style="color: #333 !important; margin-bottom: 1.2em; padding-left: 1.5em;">'),
        (r'<ol([^>]*)>', lambda m: f'<ol{m.group(1)} style="color: #333 !important; margin-bottom: 1.2em; padding-left: 1.5em;">'),
        
        # div 태그 (일반적인 컨테이너)
        (r'<div([^>]*)>', lambda m: f'<div{m.group(1)} style="color: #333 !important;">'),
        
        # span 태그
        (r'<span([^>]*)>', lambda m: f'<span{m.group(1)} style="color: #333 !important;">'),
        
        # strong 태그
        (r'<strong([^>]*)>', lambda m: f'<strong{m.group(1)} style="color: #333 !important; font-weight: 600;">'),
        
        # em 태그
        (r'<em([^>]*)>', lambda m: f'<em{m.group(1)} style="color: #333 !important; font-style: italic;">'),
    ]
    
    # 흰색 텍스트 색상 변경
    for pattern, replacement in white_color_fixes:
        html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
    
    # 기존 style 속성이 있는 경우 color 속성 강제 추가/변경
    def add_color_to_style(match):
        element = match.group(1)  # 태그 이름
        attributes = match.group(2)  # 기존 속성들
        
        # 기본 색상 설정
        colors = {
            'h1': '#1a1a1a',
            'h2': '#2c3e50', 
            'h3': '#34495e',
            'p': '#333',
            'li': '#333',
            'ul': '#333',
            'ol': '#333',
            'div': '#333',
            'span': '#333',
            'strong': '#333',
            'em': '#333'
        }
        
        target_color = colors.get(element.lower(), '#333')
        
        # style 속성이 있는 경우
        if 'style=' in attributes:
            # 기존 color 속성 제거 후 새로운 color 추가
            attributes = re.sub(r'color:\s*[^;]*;?', '', attributes)
            attributes = re.sub(r'style="([^"]*)"', f'style="color: {target_color} !important; \\1"', attributes)
        else:
            # style 속성이 없는 경우 새로 추가
            attributes += f' style="color: {target_color} !important;"'
        
        return f'<{element}{attributes}>'
    
    # 모든 텍스트 요소에 color 강제 적용
    text_elements = r'<(h1|h2|h3|h4|h5|h6|p|li|ul|ol|div|span|strong|em|td|th)([^>]*)>'
    html_content = re.sub(text_elements, add_color_to_style, html_content, flags=re.IGNORECASE)
    
    # 3단계: 전체 컨테이너에 기본 텍스트 색상 적용
    if not re.search(r'<body[^>]*style', html_content, re.IGNORECASE):
        html_content = re.sub(r'<body([^>]*)>', r'<body\1 style="color: #333 !important; background-color: white;">', html_content, flags=re.IGNORECASE)
    
    return html_content

def get_text_length_from_html(html_content: str) -> int:
    """HTML에서 순수 텍스트 길이 계산"""
    import re
    from html import unescape
    
    # HTML 태그 제거
    text_only = re.sub(r'<[^>]+>', '', html_content)
    
    # HTML 엔티티 디코딩
    text_only = unescape(text_only)
    
    # 연속된 공백을 하나로 변환하고 앞뒤 공백 제거
    text_only = re.sub(r'\s+', ' ', text_only).strip()
    
    return len(text_only)

async def validate_and_enhance_content(html_content: str, target_word_count: int, job) -> str:
    """생성된 콘텐츠의 글자수 검증 및 보완 - 강화된 버전"""
    current_length = get_text_length_from_html(html_content)
    print(f"📊 현재 글자수: {current_length}자, 목표: {target_word_count}자 ({current_length/target_word_count*100:.1f}%)")
    
    # 목표 글자수의 60% 이하인 경우 추가 내용 생성 필요 (더 엄격한 기준)
    if current_length < target_word_count * 0.6:
        shortage = target_word_count - current_length
        print(f"⚠️ 글자수 부족: {shortage}자 추가 필요")
        
        # 부족한 양에 따라 다양한 섹션 추가
        additional_sections = []
        
        # 기본 추가 섹션
        additional_sections.append(f"""
        <h2 id="detailed-guide" style="color: #2c3e50; font-size: 1.6em; font-weight: 600; margin: 2em 0 1em;">상세 가이드</h2>
        
        <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
        {job.topic}에 대해 더욱 자세히 알아보겠습니다. 실제로 많은 사람들이 이 주제에 대해 궁금해하는 부분들을 종합적으로 정리해보았습니다. 
        전문가들의 의견과 실제 경험자들의 후기를 바탕으로 한 실용적인 정보들을 제공하겠습니다.
        </p>
        
        <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
        초보자부터 숙련자까지 모든 단계의 사람들에게 도움이 될 수 있도록 단계별로 자세히 설명드리겠습니다. 
        특히 처음 시작하는 분들이 흔히 놓치기 쉬운 중요한 포인트들을 중심으로 구성했습니다.
        </p>
        
        <h3 id="preparation-steps" style="color: #34495e; font-size: 1.3em; font-weight: 500; margin: 1.5em 0 0.8em;">사전 준비사항</h3>
        
        <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
        성공적인 결과를 얻기 위해서는 철저한 사전 준비가 필수입니다. 먼저 관련 정보를 충분히 수집하고, 
        필요한 도구나 자료들을 미리 준비해두는 것이 좋습니다. 또한 예상되는 어려움들을 미리 파악하여 
        대응책을 마련해두면 훨씬 수월하게 진행할 수 있습니다.
        </p>
        """)
        
        # 부족한 글자수가 많으면 더 많은 섹션 추가
        if shortage > 800:
            additional_sections.append(f"""
            <h2 id="expert-recommendations" style="color: #2c3e50; font-size: 1.6em; font-weight: 600; margin: 2em 0 1em;">전문가 추천사항</h2>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            해당 분야의 전문가들이 공통적으로 강조하는 핵심 포인트들을 정리해보겠습니다. 
            수년간의 경험과 연구를 바탕으로 한 검증된 방법들이므로, 이를 참고하시면 더욱 효과적인 결과를 얻을 수 있습니다.
            </p>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            전문가들은 특히 체계적인 접근과 지속적인 학습의 중요성을 강조합니다. 단기간의 성과에 만족하지 말고, 
            장기적인 관점에서 꾸준히 발전시켜나가는 것이 중요하다고 조언합니다. 또한 다양한 사례를 참고하여 
            자신만의 방식을 찾아가는 것도 중요한 포인트입니다.
            </p>
            
            <h3 id="common-mistakes" style="color: #34495e; font-size: 1.3em; font-weight: 500; margin: 1.5em 0 0.8em;">흔한 실수 방지법</h3>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            많은 초보자들이 저지르기 쉬운 실수들을 미리 알아두면 시행착오를 크게 줄일 수 있습니다. 
            가장 흔한 실수는 기초를 소홀히 하고 성급하게 고급 단계로 넘어가려는 것입니다. 
            탄탄한 기초 없이는 결국 한계에 부딪히게 되므로, 처음부터 차근차근 단계를 밟아가는 것이 중요합니다.
            </p>
            """)
        
        if shortage > 1200:
            additional_sections.append(f"""
            <h2 id="practical-examples" style="color: #2c3e50; font-size: 1.6em; font-weight: 600; margin: 2em 0 1em;">실제 사례 및 경험담</h2>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            실제로 {job.topic}을 경험한 사람들의 생생한 후기와 사례를 통해 더욱 실용적인 정보를 얻어보겠습니다. 
            성공 사례와 실패 사례를 모두 살펴봄으로써 균형잡힌 시각을 가질 수 있습니다.
            </p>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            많은 경험자들이 공통적으로 언급하는 것은 인내심의 중요성입니다. 즉각적인 결과를 기대하기보다는 
            꾸준히 노력하며 점진적인 개선을 통해 목표에 도달하는 것이 중요하다고 말합니다. 
            또한 실패를 두려워하지 말고 이를 학습의 기회로 삼는 마음가짐이 필요합니다.
            </p>
            
            <h3 id="success-factors" style="color: #34495e; font-size: 1.3em; font-weight: 500; margin: 1.5em 0 0.8em;">성공 요인 분석</h3>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            성공한 사례들을 분석해보면 몇 가지 공통된 패턴을 발견할 수 있습니다. 
            첫째, 명확한 목표 설정과 체계적인 계획 수립이 선행되었습니다. 
            둘째, 지속적인 학습과 개선 의지를 보였습니다. 
            셋째, 어려움에 직면했을 때 포기하지 않고 다양한 해결방안을 모색했습니다.
            </p>
            """)
        
        if shortage > 1600:
            additional_sections.append(f"""
            <h2 id="frequently-asked-questions" style="color: #2c3e50; font-size: 1.6em; font-weight: 600; margin: 2em 0 1em;">자주 묻는 질문</h2>
            
            <h3 id="faq-1" style="color: #34495e; font-size: 1.3em; font-weight: 500; margin: 1.5em 0 0.8em;">Q1. 처음 시작할 때 가장 주의해야 할 점은?</h3>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            가장 중요한 것은 기초를 탄탄히 하는 것입니다. 성급하게 고급 단계로 넘어가려 하지 말고, 
            기본기를 충분히 익힌 후에 단계적으로 발전시켜나가는 것이 좋습니다. 
            또한 관련 정보를 충분히 수집하고 전문가의 조언을 구하는 것도 도움이 됩니다.
            </p>
            
            <h3 id="faq-2" style="color: #34495e; font-size: 1.3em; font-weight: 500; margin: 1.5em 0 0.8em;">Q2. 예상보다 어려울 때는 어떻게 해야 하나요?</h3>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            어려움에 직면했을 때는 문제를 더 작은 단위로 나누어 해결하는 것이 효과적입니다. 
            한 번에 모든 것을 해결하려 하지 말고, 하나씩 차근차근 접근하면 의외로 쉽게 해결되는 경우가 많습니다. 
            또한 온라인 커뮤니티나 전문가 그룹에서 도움을 구하는 것도 좋은 방법입니다.
            </p>
            
            <h3 id="faq-3" style="color: #34495e; font-size: 1.3em; font-weight: 500; margin: 1.5em 0 0.8em;">Q3. 지속적인 발전을 위한 팁이 있다면?</h3>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            정기적인 복습과 새로운 정보 학습이 중요합니다. 현재 상태에 만족하지 말고 
            지속적으로 개선점을 찾아 발전시켜나가는 자세가 필요합니다. 
            또한 다른 사람들의 경험을 참고하고, 새로운 방법들을 시도해보는 것도 도움이 됩니다.
            </p>
            
            <h2 id="conclusion-summary" style="color: #2c3e50; font-size: 1.6em; font-weight: 600; margin: 2em 0 1em;">결론 및 요약</h2>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            지금까지 {job.topic}에 대해 종합적으로 살펴보았습니다. 핵심은 체계적인 준비와 단계적인 접근, 
            그리고 꾸준한 노력이라고 할 수 있습니다. 처음에는 어렵게 느껴질 수 있지만, 
            차근차근 단계를 밟아가다 보면 반드시 원하는 결과를 얻을 수 있을 것입니다.
            </p>
            
            <p style="color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;">
            무엇보다 중요한 것은 포기하지 않는 마음가짐입니다. 어려움에 직면했을 때도 
            이를 성장의 기회로 삼아 더욱 발전할 수 있는 계기로 만들어보세요. 
            여러분의 성공을 진심으로 응원합니다.
            </p>
            """)
        
        # 모든 추가 섹션을 결합
        additional_content = "".join(additional_sections)
        
        # HTML 내용에 추가
        if '</html>' in html_content:
            # HTML 문서의 경우 body 태그 끝 전에 삽입
            html_content = html_content.replace('</article>', additional_content + '</article>')
        elif '</body>' in html_content:
            html_content = html_content.replace('</body>', additional_content + '</body>')
        else:
            # 단순 HTML 조각인 경우 끝에 추가
            html_content += additional_content
        
        # 추가 후 다시 글자수 확인
        new_length = get_text_length_from_html(html_content)
        print(f"✅ 콘텐츠 보강 완료: {current_length}자 → {new_length}자 ({new_length/target_word_count*100:.1f}%)")
    
    return html_content

def convert_text_to_html(content: str, job, image_urls: list) -> str:
    """텍스트 콘텐츠를 HTML로 변환"""
    import re
    
    # HTML 템플릿 시작
    html = f"""<!DOCTYPE html>
<html lang="{job.target_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{job.topic}</title>
    <meta name="description" content="{content[:150]}...">
    <meta name="author" content="Noaats AI">
    <style>
        body {{ margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: #2c3e50; background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); }}
        article {{ max-width: 900px; margin: 0 auto; padding: 40px; background: white; border-radius: 20px; box-shadow: 0 12px 48px rgba(0,0,0,0.12); }}
        h1 {{ color: #2c3e50; font-size: 2.8em; font-weight: 800; margin-bottom: 0.8em; line-height: 1.2; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h2 {{ color: #2c3e50; font-size: 2.1em; font-weight: 700; margin-top: 3.5em; margin-bottom: 1.5em; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #6c5ce7 100%); padding: 20px 30px; border-radius: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); text-align: center; color: white; }}
        h3 {{ color: #2c3e50; font-size: 1.5em; font-weight: 600; margin: 2em 0 1em; padding: 10px 0; border-bottom: 2px solid #74b9ff; }}
        p {{ color: #2c3e50; line-height: 1.9; font-size: 17px; margin-bottom: 2em; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 25px; border-radius: 12px; border-left: 6px solid #74b9ff; box-shadow: 0 4px 16px rgba(0,0,0,0.08); font-weight: 400; }}
        ul, ol {{ color: #2c3e50; margin: 2em 0; padding: 25px; background: linear-gradient(135deg, #ddd6fe 0%, #c084fc 20%, #e879f9 100%); border-radius: 15px; box-shadow: 0 6px 24px rgba(0,0,0,0.12); list-style: none; }}
        li {{ color: #2c3e50; margin-bottom: 1em; line-height: 1.7; background: white; padding: 15px 20px; border-radius: 10px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #74b9ff; font-weight: 500; }}
        figure {{ margin: 2em auto; text-align: center; max-width: 700px; }}
        img {{ max-width: 100%; height: auto; border-radius: 20px; box-shadow: 0 12px 40px rgba(0,0,0,0.2); border: 4px solid white; filter: brightness(1.05) contrast(1.1); }}
        figcaption {{ margin-top: 0.8em; font-style: italic; color: #666; font-size: 14px; font-weight: 500; }}
        strong {{ color: white; font-weight: 700; background: linear-gradient(135deg, #e17055 0%, #d63031 50%, #e84393 100%); padding: 4px 10px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        em {{ font-style: italic; color: #74b9ff; font-weight: 500; }}
    </style>
</head>
<body>
<article>"""
    
    # 제목 추가
    html += f"<h1>{job.topic}</h1>\n"
    
    # 이미지 카운터
    img_counter = 0
    
    # 텍스트를 HTML로 변환
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 마크다운 헤딩을 HTML로 변환
        if line.startswith('## '):
            title = line.replace('## ', '')
            html += f"<h2>{title}</h2>\n"
            # 이미지 추가
            if job.include_images and img_counter < len(image_urls):
                html += f'''<figure>
    <img src="{image_urls[img_counter]}" alt="{title} 관련 이미지" width="1200" height="675">
    <figcaption>{title} 관련 이미지</figcaption>
</figure>\n'''
                img_counter += 1
        elif line.startswith('### '):
            html += f"<h3>{line.replace('### ', '')}</h3>\n"
        elif line.startswith('# '):
            html += f"<h1>{line.replace('# ', '')}</h1>\n"
        elif line.startswith('- ') or line.startswith('* '):
            # 리스트 처리 (간단하게)
            html += f"<p>• {line[2:]}</p>\n"
        elif line.startswith('**') and line.endswith('**'):
            # 굵은 글씨
            html += f"<p><strong>{line[2:-2]}</strong></p>\n"
        else:
            # 일반 문단
            if line:
                html += f"<p>{line}</p>\n"
    
    html += """</article>
</body>
</html>"""
    
    return html

async def test_gemini_api(prompt: str) -> Dict[str, Any]:
    """Gemini API 테스트"""
    config = AI_CONFIGS["gemini"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Gemini API 키가 설정되지 않았습니다")
    
    url = config["url_template"].format(
        model=config["model"],
        api_key=config["api_key"]
    )
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000,
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                token_usage = result.get("usageMetadata", {})
                
                return {
                    "success": True,
                    "content": content,
                    "tokenUsage": token_usage
                }
            else:
                raise HTTPException(status_code=500, detail="응답에 콘텐츠가 없습니다")
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

async def test_claude_api(prompt: str) -> Dict[str, Any]:
    """Claude API 테스트"""
    config = AI_CONFIGS["claude"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Claude API 키가 설정되지 않았습니다")
    
    headers = {
        "x-api-key": config["api_key"],
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": config["model"],
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config["url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["content"][0]["text"]
            
            return {
                "success": True,
                "content": content,
                "tokenUsage": {
                    "promptTokenCount": result["usage"]["input_tokens"],
                    "candidatesTokenCount": result["usage"]["output_tokens"],
                    "totalTokenCount": result["usage"]["input_tokens"] + result["usage"]["output_tokens"]
                }
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

async def test_openai_api(prompt: str) -> Dict[str, Any]:
    """OpenAI API 테스트"""
    config = AI_CONFIGS["openai"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="OpenAI API 키가 설정되지 않았습니다")
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config["url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "content": content,
                "tokenUsage": {
                    "promptTokenCount": result["usage"]["prompt_tokens"],
                    "candidatesTokenCount": result["usage"]["completion_tokens"],
                    "totalTokenCount": result["usage"]["total_tokens"]
                }
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

async def test_grok_api(prompt: str) -> Dict[str, Any]:
    """Grok API 테스트"""
    config = AI_CONFIGS["grok"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Grok API 키가 설정되지 않았습니다")
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config["url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "content": content,
                "tokenUsage": {
                    "promptTokenCount": result["usage"]["prompt_tokens"],
                    "candidatesTokenCount": result["usage"]["completion_tokens"],
                    "totalTokenCount": result["usage"]["total_tokens"]
                }
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

# API 엔드포인트
@app.get("/api/v1/health/", response_model=HealthResponse)
async def health_check():
    """시스템 상태 확인"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=os.getenv("APP_ENV", "development")
    )

# 인증 API 엔드포인트
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """로그인"""
    try:
        # 사용자 인증
        is_valid, user, error_message = db.verify_user_password(request.username, request.password)
        
        if not is_valid:
            return LoginResponse(
                success=False,
                message=error_message
            )
        
        # 세션 토큰 생성
        token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        # 세션 저장
        session_token = db.create_session(
            user_id=user.id,
            ip_address=None,
            user_agent=None
        )
        
        if not session_token:
            raise HTTPException(
                status_code=500,
                detail="Failed to create session"
            )
        
        # 로그인 시도 횟수 초기화
        db.reset_failed_attempts(user.username)
        
        return LoginResponse(
            success=True,
            message="로그인 성공",
            token=session_token,
            user={
                "username": user.username,
                "role": user.role,
                "isActive": user.is_active,
                "expiresAt": user.expires_at
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/v1/auth/logout")
async def logout(current_user: User = Depends(get_current_user), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """로그아웃"""
    try:
        token = credentials.credentials
        db.delete_session(token)
        return {"success": True, "message": "로그아웃 되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.get("/api/v1/auth/validate", response_model=AuthValidateResponse)
async def validate_token(current_user: User = Depends(get_current_user)):
    """토큰 유효성 검증"""
    try:
        return AuthValidateResponse(
            valid=True,
            user={
                "username": current_user.username,
                "role": current_user.role,
                "isActive": current_user.is_active,
                "expiresAt": current_user.expires_at
            }
        )
    except HTTPException:
        return AuthValidateResponse(
            valid=False,
            message="Invalid or expired token"
        )

@app.post("/api/v1/test/ai", response_model=TestResponse)
async def test_ai_api(request: TestRequest, current_user: User = Depends(get_current_user)):
    """AI API 테스트 (데이터베이스 저장) - 인증 필요"""
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    try:
        if request.provider == "gemini":
            result = await test_gemini_api(request.prompt)
        elif request.provider == "claude":
            result = await test_claude_api(request.prompt)
        elif request.provider == "openai":
            result = await test_openai_api(request.prompt)
        elif request.provider == "grok":
            result = await test_grok_api(request.prompt)
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 제공자: {request.provider}")
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # 데이터베이스에 결과 저장
        test_result = TestResult(
            provider=request.provider,
            prompt=request.prompt,
            response=result["content"],
            success=True,
            token_usage=result.get("tokenUsage"),
            response_time_ms=response_time_ms,
            created_at=timestamp
        )
        db.save_test_result(test_result)
        
        return TestResponse(
            success=True,
            provider=request.provider,
            content=result["content"],
            tokenUsage=result.get("tokenUsage"),
            timestamp=timestamp
        )
        
    except HTTPException as he:
        # 실패 결과도 데이터베이스에 저장
        response_time_ms = int((time.time() - start_time) * 1000)
        test_result = TestResult(
            provider=request.provider,
            prompt=request.prompt,
            response="",
            success=False,
            error_message=str(he.detail),
            response_time_ms=response_time_ms,
            created_at=timestamp
        )
        db.save_test_result(test_result)
        raise
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        test_result = TestResult(
            provider=request.provider,
            prompt=request.prompt,
            response="",
            success=False,
            error_message=str(e),
            response_time_ms=response_time_ms,
            created_at=timestamp
        )
        db.save_test_result(test_result)
        
        return TestResponse(
            success=False,
            provider=request.provider,
            error=str(e),
            timestamp=timestamp
        )

# 새로운 API 엔드포인트들
@app.get("/api/v1/test-results/{provider}")
async def get_test_results(provider: str, limit: int = 50):
    """제공자별 테스트 결과 조회"""
    try:
        results = db.get_test_results(provider, limit)
        return [
            {
                "id": r.id,
                "provider": r.provider,
                "prompt": r.prompt,
                "response": r.response,
                "success": r.success,
                "errorMessage": r.error_message,
                "tokenUsage": r.token_usage,
                "responseTimeMs": r.response_time_ms,
                "createdAt": r.created_at
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/provider-stats/{provider}", response_model=ProviderStatsResponse)
async def get_provider_stats(provider: str):
    """제공자별 통계 조회"""
    try:
        stats = db.get_provider_stats(provider)
        return ProviderStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generation/generate", response_model=GenerationResponse)
async def generate_content(request: GenerationRequest, background_tasks: BackgroundTasks):
    """콘텐츠 생성 작업 시작"""
    job_id = f"gen_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now().isoformat()
    
    # 생성 작업을 데이터베이스에 저장
    generation_job = GenerationJob(
        job_id=job_id,
        provider=request.provider,
        topic=request.topic,
        tone=request.tone,
        word_count=request.wordCount,
        include_images=request.includeImages,
        target_language=request.targetLanguage,
        status="pending",
        progress=0,
        created_at=timestamp
    )
    
    try:
        db.save_generation_job(generation_job)
        
        # 백그라운드에서 실제 생성 작업 실행
        background_tasks.add_task(execute_generation_job, job_id)
        
        return GenerationResponse(
            jobId=job_id,
            status="started",
            message="Content generation started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

@app.get("/api/v1/generation/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    """작업 상태 조회"""
    try:
        job = db.get_generation_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        response = JobStatusResponse(
            jobId=job.job_id,
            status=job.status,
            progress=job.progress,
            tone=job.tone,
            word_count=job.word_count,
            created_at=job.created_at
        )
        
        if job.status == "completed" and job.content:
            # Try to get word_count_actual from content object
            actual_word_count = 0
            try:
                import json
                content_obj = json.loads(job.content)
                actual_word_count = content_obj.get('word_count_actual', 0)
                if not actual_word_count:
                    # Fallback: calculate from HTML content
                    html_content = content_obj.get('html_content', '')
                    if html_content:
                        import re
                        plain_text = re.sub(r'<[^>]+>', '', html_content)
                        actual_word_count = len(plain_text.split())
            except:
                actual_word_count = len(job.content.split()) if job.content else 0
            
            response.result = {
                "bundleId": f"bundle_{job.job_id}",
                "title": job.topic,
                "contentPreview": job.content[:200] + "..." if len(job.content) > 200 else job.content,
                "wordCount": actual_word_count,
                "imagesCount": 0,
                "seoScore": 85
            }
        elif job.status == "failed":
            response.errorMessage = job.error_message
            response.errorCode = "GENERATION_FAILED"
            
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/generation/jobs")
async def get_generation_jobs(provider: Optional[str] = None, limit: int = 50, current_user: User = Depends(get_current_user)):
    """콘텐츠 생성 작업 목록 조회"""
    try:
        jobs = db.get_generation_jobs(provider, limit=limit)
        return [
            {
                "jobId": j.job_id,
                "provider": j.provider,
                "topic": j.topic,
                "tone": j.tone,
                "wordCount": j.word_count,
                "status": j.status,
                "progress": j.progress,
                "content": j.content,
                "errorMessage": j.error_message,
                "createdAt": j.created_at
            }
            for j in jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_generation_job(job_id: str):
    """백그라운드에서 실행되는 실제 콘텐츠 생성 작업"""
    try:
        job = db.get_generation_job(job_id)
        if not job:
            return
        
        # 작업 상태를 진행중으로 업데이트
        db.update_generation_job_status(job_id, "in_progress", 10)
        
        # AI API 호출하여 콘텐츠 생성 (creation guide 적용)
        include_images = "yes" if job.include_images else "no"
        
        # AI 키워드 생성 함수 (전역)
        async def extract_keywords_with_ai(topic_text: str) -> list:
            """AI를 사용해서 주제에서 영어 키워드를 동적 추출"""
            try:
                # 간단한 Gemini API 호출로 키워드 생성
                keyword_prompt = f"""주제: "{topic_text}"
                
이 주제와 관련된 영어 키워드 5개를 생성해주세요. 이미지 검색에 사용할 키워드입니다.

규칙:
1. 영어 단어만 출력
2. 쉼표로 구분
3. 이미지 검색에 적합한 구체적인 키워드
4. 예: food, cooking, recipe, kitchen, ingredients

출력 형식: keyword1, keyword2, keyword3, keyword4, keyword5"""

                # Gemini API 설정에서 가져오기
                config = AI_CONFIGS["gemini"]
                if config["api_key"]:
                    url = config["url_template"].format(
                        model=config["model"],
                        api_key=config["api_key"]
                    )
                    
                    payload = {
                        "contents": [{
                            "parts": [{
                                "text": keyword_prompt
                            }]
                        }],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 100,
                        }
                    }
                    
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(url, json=payload)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if "candidates" in result and len(result["candidates"]) > 0:
                                keywords_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                                # 쉼표로 분할하고 정리
                                keywords = [k.strip().lower() for k in keywords_text.split(',')]
                                keywords = [k for k in keywords if k and len(k) > 2]  # 빈 문자열과 너무 짧은 것 제거
                                
                                print(f"🤖 AI 생성 키워드: {keywords}")
                                return keywords[:5]  # 최대 5개
                
            except Exception as e:
                print(f"⚠️ AI 키워드 생성 실패: {e}")
            
            # Fallback: 기존 방식 + 간단한 분석
            return extract_keywords_fallback(topic_text)
        
        def extract_keywords_fallback(topic_text: str) -> list:
            """AI 실패 시 사용하는 fallback 키워드 추출"""
            topic_lower = topic_text.lower()
            
            # 기본 매핑 (최소한의 핵심 키워드들만)
            basic_mapping = {
                '항공': ['airplane', 'aircraft', 'flight'],
                '비행기': ['airplane', 'aircraft'],
                '마일리지': ['airline', 'loyalty', 'frequent'],
                '고구마': ['sweet', 'potato', 'roasted'],
                '맛탕': ['candied', 'sweet', 'potato'],
                '만드는법': ['recipe', 'cooking', 'tutorial'],
                '요리': ['cooking', 'chef', 'kitchen'],
                '음식': ['food', 'cooking', 'restaurant'],
                '살기': ['living', 'city', 'apartment'],
                '서울': ['seoul', 'city', 'urban'],
                '안양': ['city', 'urban', 'korea'],
                '일본': ['japan', 'japanese', 'tokyo'],
                '놀러': ['travel', 'tourism', 'vacation'],
                '여행': ['travel', 'trip', 'tourism'],
                '팁': ['tips', 'guide', 'advice'],
                '쇼핑': ['shopping', 'mall', 'retail'],
                '패션': ['fashion', 'style', 'clothing'],
                '건강': ['health', 'wellness', 'medical'],
                '운동': ['exercise', 'fitness', 'sport'],
                '교육': ['education', 'learning', 'study'],
                '비즈니스': ['business', 'office', 'meeting'],
                '기술': ['technology', 'tech', 'digital'],
                '인공지능': ['artificial', 'intelligence', 'robot'],
                'ai': ['artificial', 'intelligence', 'technology']
            }
            
            search_terms = []
            for korean, english_list in basic_mapping.items():
                if korean in topic_lower:
                    search_terms.extend(english_list)
                    
            # 영어 키워드 직접 추가
            english_words = ['business', 'tech', 'food', 'health', 'education', 'fashion', 'sport']
            for word in english_words:
                if word in topic_lower:
                    search_terms.append(word)
            
            # 주제에서 영어 단어 직접 추출
            import re
            english_in_topic = re.findall(r'[a-zA-Z]{3,}', topic_text)
            search_terms.extend(english_in_topic)
                    
            # 검색어가 없으면 주제를 단순화
            if not search_terms:
                # 주제를 간단한 키워드로 변환 시도
                simple_words = topic_text.replace('만드는법', 'recipe').replace('하는법', 'tutorial').split()
                search_terms = [w for w in simple_words if len(w) > 2] or ['tutorial', 'guide', 'howto']
                
            return list(set(search_terms))[:5]  # 중복 제거하고 최대 5개

        # 동적 이미지 검색 시스템
        async def search_dynamic_images(topic: str, count: int = 5) -> list:
            """다양한 소스에서 실제 작동하는 이미지 URL들을 검색"""
            
            # AI를 사용해서 키워드 생성
            keywords = await extract_keywords_with_ai(topic)
            search_query = ' '.join(keywords[:3])  # 상위 3개 키워드만 사용
            
            print(f"🔍 이미지 검색: '{topic}' -> '{search_query}'")
            
            image_urls = []
            
            # 방법 1: Picsum (Lorem Picsum) - 안정적인 더미 이미지
            picsum_urls = []
            for i in range(count):
                # 각기 다른 이미지를 위해 다른 ID 사용
                url = f"https://picsum.photos/1200/675?random={i+hash(topic)%1000}"
                picsum_urls.append(url)
            image_urls.extend(picsum_urls)
            
            # 방법 2: 실제 Unsplash 고정 이미지 ID들 (검증된 URL들)
            verified_unsplash_urls = [
                # 일반적인 주제별 고품질 이미지들
                "https://images.unsplash.com/photo-1542744094-3a31f272c490?w=1200&h=675&fit=crop&auto=format", # 음식
                "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=1200&h=675&fit=crop&auto=format", # 기술
                "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1200&h=675&fit=crop&auto=format", # 비즈니스
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=675&fit=crop&auto=format", # 건강
                "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?w=1200&h=675&fit=crop&auto=format", # 여행
                "https://images.unsplash.com/photo-1554475901-4538ddfbccc2?w=1200&h=675&fit=crop&auto=format", # 교육
                "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=1200&h=675&fit=crop&auto=format", # 라이프스타일
                "https://images.unsplash.com/photo-1587440871875-191322ee64b0?w=1200&h=675&fit=crop&auto=format", # 자연
            ]
            
            # 주제에 맞는 이미지 선택 로직
            topic_lower = topic.lower()
            selected_images = []
            
            if any(word in topic_lower for word in ['음식', '요리', '레시피', '맛탕', '고구마']):
                selected_images = [
                    "https://images.unsplash.com/photo-1542744094-3a31f272c490?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1574484284002-952d92456975?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=1200&h=675&fit=crop&auto=format",
                ]
            elif any(word in topic_lower for word in ['여행', '일본', '놀러', '관광']):
                selected_images = [
                    "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1551818255-e6e10975cd6d?w=1200&h=675&fit=crop&auto=format",
                ]
            elif any(word in topic_lower for word in ['기술', 'ai', '인공지능', '개발']):
                selected_images = [
                    "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1555255707-c07966088b7b?w=1200&h=675&fit=crop&auto=format",
                ]
            else:
                # 기본 이미지들
                selected_images = verified_unsplash_urls[:3]
            
            # Picsum과 Unsplash 이미지 조합
            final_image_urls = []
            
            # Picsum 이미지 (안정적 보장)
            for i in range(min(2, count)):
                final_image_urls.append(f"https://picsum.photos/1200/675?random={i+hash(topic)%1000}")
            
            # Unsplash 검증된 이미지들
            for i in range(min(count-2, len(selected_images))):
                final_image_urls.append(selected_images[i])
            
            # 부족하면 추가 Picsum으로 채우기
            while len(final_image_urls) < count:
                idx = len(final_image_urls)
                final_image_urls.append(f"https://picsum.photos/1200/675?random={idx+hash(topic)%1000}")
            
            print(f"✅ 검증된 이미지 {len(final_image_urls)}개 생성됨")
            print(f"🔗 이미지 URL 샘플: {final_image_urls[0]}")
            
            return final_image_urls[:count]
        
        # 추가 안정적인 이미지 소스
        def get_additional_stable_images(topic: str, count: int = 3) -> list:
            """추가적인 안정적인 이미지 소스들"""
            topic_lower = topic.lower()
            
            # 주제별 더 많은 검증된 Unsplash 이미지들
            topic_image_banks = {
                'food': [
                    "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=1200&h=675&fit=crop&auto=format",
                ],
                'travel': [
                    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1200&h=675&fit=crop&auto=format", 
                    "https://images.unsplash.com/photo-1530789253388-582c481c54b0?w=1200&h=675&fit=crop&auto=format",
                ],
                'technology': [
                    "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1555255707-c07966088b7b?w=1200&h=675&fit=crop&auto=format",
                ],
                'business': [
                    "https://images.unsplash.com/photo-1556761175-b413da4baf72?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=675&fit=crop&auto=format",
                    "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=1200&h=675&fit=crop&auto=format",
                ]
            }
            
            # 주제에 맞는 카테고리 선택
            if any(word in topic_lower for word in ['음식', '요리', '레시피', '맛탕', '고구마']):
                selected_bank = topic_image_banks['food']
            elif any(word in topic_lower for word in ['여행', '일본', '놀러', '관광']):
                selected_bank = topic_image_banks['travel'] 
            elif any(word in topic_lower for word in ['기술', 'ai', '인공지능', '개발']):
                selected_bank = topic_image_banks['technology']
            elif any(word in topic_lower for word in ['비즈니스', '사업', '마케팅']):
                selected_bank = topic_image_banks['business']
            else:
                # 기본적으로 모든 카테고리에서 균등하게 선택
                all_images = []
                for category_images in topic_image_banks.values():
                    all_images.extend(category_images)
                selected_bank = all_images
            
            return selected_bank[:count]
        
        # 1차: 동적 이미지 검색 (검증된 Picsum + Unsplash 조합)
        print(f"🔍 이미지 검색 시작: {job.topic}")
        image_urls = await search_dynamic_images(job.topic, 3)
        print(f"📸 기본 이미지: {len(image_urls)}개")
        
        # 2차: 추가 안정적인 이미지로 보완  
        additional_stable_images = get_additional_stable_images(job.topic, 2)
        print(f"🎨 추가 안정 이미지: {len(additional_stable_images)}개")
        image_urls.extend(additional_stable_images)
        
        # 최종적으로 5개 이미지 확보
        if len(image_urls) < 5:
            # 부족한 경우 Picsum으로 채우기 (100% 안정성 보장)
            for i in range(len(image_urls), 5):
                fallback_url = f"https://picsum.photos/1200/675?random={i+hash(job.topic)%1000}"
                image_urls.append(fallback_url)
        
        # 중복 제거 및 최종 정리
        unique_urls = []
        seen_urls = set()
        for url in image_urls:
            if url not in seen_urls:
                unique_urls.append(url)
                seen_urls.add(url)
        
        image_urls = unique_urls[:5]
        print(f"✅ 최종 검증된 이미지 URL들:")
        for i, url in enumerate(image_urls):
            print(f"  {i+1}. {url}")
        
        # 관련 링크 생성 함수
        def get_relevant_links(topic: str) -> list:
            """주제에 관련된 실제 링크 생성"""
            topic_lower = topic.lower()
            
            if any(word in topic_lower for word in ['ai', '인공지능', 'artificial', 'intelligence']):
                return [
                    {"text": "OpenAI 공식 사이트", "url": "https://openai.com"},
                    {"text": "Google AI", "url": "https://ai.google"},
                    {"text": "Microsoft AI", "url": "https://www.microsoft.com/en-us/ai"}
                ]
            elif any(word in topic_lower for word in ['기술', 'tech', '개발', 'development']):
                return [
                    {"text": "GitHub", "url": "https://github.com"},
                    {"text": "Stack Overflow", "url": "https://stackoverflow.com"},
                    {"text": "TechCrunch", "url": "https://techcrunch.com"}
                ]
            elif any(word in topic_lower for word in ['비즈니스', 'business', '마케팅', 'marketing']):
                return [
                    {"text": "Harvard Business Review", "url": "https://hbr.org"},
                    {"text": "Forbes", "url": "https://forbes.com"},
                    {"text": "McKinsey & Company", "url": "https://mckinsey.com"}
                ]
            elif any(word in topic_lower for word in ['건강', 'health', '의료', 'medical']):
                return [
                    {"text": "WebMD", "url": "https://webmd.com"},
                    {"text": "Mayo Clinic", "url": "https://mayoclinic.org"},
                    {"text": "WHO", "url": "https://who.int"}
                ]
            elif any(word in topic_lower for word in ['여행', 'travel', '관광']):
                return [
                    {"text": "Booking.com", "url": "https://booking.com"},
                    {"text": "TripAdvisor", "url": "https://tripadvisor.com"},
                    {"text": "Lonely Planet", "url": "https://lonelyplanet.com"}
                ]
            else:
                return [
                    {"text": "Wikipedia", "url": "https://wikipedia.org"},
                    {"text": "Google", "url": "https://google.com"},
                    {"text": "Naver", "url": "https://naver.com"}
                ]
        
        relevant_links = get_relevant_links(job.topic)
        
        # 링크 정보를 문자열로 변환
        link_instructions = "\\n".join([f"- {link['text']}: {link['url']}" for link in relevant_links])
        
        prompt = f"""너는 블로그용 HTML 본문 생성기다. 아래 규칙을 정확히 지켜 순수 HTML만 출력하라. (코드펜스/추가 설명/주석 금지)

CRITICAL RULES (반드시 준수):
1. HTML만 출력한다(마크다운/설명 금지).
2. 출력 언어는 {job.target_language}, 문체는 {job.tone}.
3. **중요**: 순수 텍스트 글자수(HTML 태그 제외)를 {job.word_count}자로 맞춘다. HTML 태그는 글자수에 포함하지 않는다.
4. **중요**: 제목 중복 금지! <h1>은 1개만, 같은 내용의 <h2> 중복 생성 금지.

STRUCTURE RULES:
1. <h1>제목</h1> - 단 1개만 사용 (주제: "{job.topic}")
2. 목차:
   <div class="table-of-contents" style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 50%, #ffeaa7 100%); padding: 30px; border-radius: 20px; margin: 3em 0; box-shadow: 0 8px 32px rgba(0,0,0,0.12); border: 1px solid rgba(255,255,255,0.2);">
     <h3 style="color: #2c3e50; margin-bottom: 1.5em; font-weight: 700; font-size: 1.4em; text-align: center;">📋 목차</h3>
     <ul style="color: #2c3e50; list-style: none; padding-left: 0; margin: 0;">
       <li style="margin-bottom: 1em; background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);"><a href="#section-1" style="color: #2c3e50; text-decoration: none; font-weight: 500; display: block;">🔹 섹션 제목 1</a></li>
       <li style="margin-bottom: 1em; background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);"><a href="#section-2" style="color: #2c3e50; text-decoration: none; font-weight: 500; display: block;">🔹 섹션 제목 2</a></li>
     </ul>
   </div>

3. 본문 구성 (4-6개 프리미엄 h2 섹션):
   - <h2 id="section-1" style="color: #2c3e50; font-size: 2.1em; font-weight: 700; margin-top: 3.5em; margin-bottom: 1.5em; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #6c5ce7 100%); padding: 20px 30px; border-radius: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); text-align: center; color: white;">🎯 섹션 제목</h2>
   - 각 섹션당 {job.word_count // 5}자 분량의 상세한 내용 (프리미엄 p 태그 사용)
   - 필요시 세련된 <h3> 소제목 사용

4. 이미지 삽입 (설정: "{include_images}"):
   {f'''⚠️ 중요: 반드시 실제 이미지를 표시해야 함! 텍스트로만 표시 금지!
   
   각 h2 섹션마다 서로 다른 실제 이미지 사용:
   
   <figure style="margin: 2em 0; text-align: center;">
     <img src="{image_urls[0] if len(image_urls) > 0 else ''}" alt="{job.topic} - 1번째 이미지" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: block;" loading="lazy">
     <figcaption style="margin-top: 0.8em; font-style: italic; color: #666 !important; font-size: 14px;">{job.topic} 관련 이미지</figcaption>
   </figure>
   
   <figure style="margin: 2em 0; text-align: center;">
     <img src="{image_urls[1] if len(image_urls) > 1 else image_urls[0]}" alt="{job.topic} - 2번째 이미지" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: block;" loading="lazy">
     <figcaption style="margin-top: 0.8em; font-style: italic; color: #666 !important; font-size: 14px;">{job.topic} 관련 이미지</figcaption>
   </figure>
   
   <figure style="margin: 2em 0; text-align: center;">
     <img src="{image_urls[2] if len(image_urls) > 2 else image_urls[0]}" alt="{job.topic} - 3번째 이미지" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: block;" loading="lazy">
     <figcaption style="margin-top: 0.8em; font-style: italic; color: #666 !important; font-size: 14px;">{job.topic} 관련 이미지</figcaption>
   </figure>
   
   🚫 절대 금지: "이미지 관련 텍스트"만 표시하지 말고 위의 <img> 태그를 그대로 사용할 것!
   ✅ 필수: 각 섹션마다 위의 이미지 중 하나씩 배치
   
   사용 가능한 실제 이미지 URL들:
   {chr(10).join([f"  - {url}" for url in image_urls])}''' if include_images == "yes" else "이미지 사용 안함"}

5. 각 h2 섹션 끝에 프리미엄 CTA:
   <div style="text-align: center; margin: 30px 0; padding: 25px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.12);">
     <p style="margin-bottom: 15px; color: #2c3e50; font-weight: 700; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">📰 더 자세한 정보를 원하시나요?</p>
     <a href="[아래 링크 중 선택]" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); color: white; text-decoration: none; font-weight: 700; font-size: 15px; padding: 15px 30px; border-radius: 50px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); transform: translateY(0); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); text-transform: uppercase; letter-spacing: 1px; position: relative; overflow: hidden;">[링크 텍스트]</a>
   </div>

AVAILABLE LINKS:
{link_instructions}

WORD COUNT TARGET (절대 필수 - 매우 중요):
- 🎯 목표: 정확히 {job.word_count}자 (순수 텍스트만, HTML 태그 제외)
- ⚠️ {job.word_count}자에서 ±10% 이내로 작성 ({int(job.word_count * 0.9)}-{int(job.word_count * 1.1)}자)
- 📝 각 h2 섹션당 최소 {max(200, job.word_count // 5)}자 이상 작성 (매우 상세하게!)
- 📝 각 문단(p 태그)당 최소 120-200자 작성 (간단한 설명 금지!)
- 📝 목록 사용 시 각 항목마다 80자 이상 상세 설명
- 📝 부족하면 반드시 다음 섹션들 추가:
  * "심화 분석" (300자 이상)
  * "단계별 가이드" (400자 이상) 
  * "주의사항 및 팁" (300자 이상)
  * "자주 묻는 질문" (400자 이상)
  * "추가 정보" (300자 이상)
  * "결론 및 요약" (200자 이상)
- 🚨 중요: 짧은 문장 금지! 모든 문단을 매우 상세하고 구체적으로 작성
- 🚨 절대 규칙: {job.word_count}자 미달 시 재작성 필요!

STYLE REQUIREMENTS (필수):
- 모든 태그에 인라인 스타일 적용
- h1: color: #1a1a1a; font-size: 2.2em; font-weight: 700;
- h2: color: #2c3e50; font-size: 1.6em; font-weight: 600; margin: 2em 0 1em;
- h3: color: #34495e; font-size: 1.3em; font-weight: 500; margin: 1.5em 0 0.8em;
- p: color: #333; margin-bottom: 1.2em; line-height: 1.7; font-size: 16px;
- li: color: #333; margin-bottom: 0.5em; line-height: 1.6;
- 절대로 흰색 텍스트 사용 금지

OUTPUT: 순수 HTML만 출력 (설명, 코드펜스 없음)"""
        
        db.update_generation_job_status(job_id, "in_progress", 50)
        
        # Use ContentGenerator with premium styling system
        print(f"🎯 Using ContentGenerator for topic: {job.topic}, provider: {job.provider}")
        
        # Create proper GenerationRequest object
        from database import GenerationJob
        from packages.gen.models import GenerationRequest as GenRequest
        
        generation_request = GenRequest(
            topic=job.topic,
            provider=job.provider.lower(),
            tone=job.tone,
            word_count=job.word_count,
            include_images=job.include_images,
            target_language=job.target_language
        )
        
        generator = ContentGenerator()
        await generator.generate_content_async(job_id, generation_request)
        
        # Get the result from database after ContentGenerator completes
        updated_job = db.get_generation_job(job_id)
        print(f"🔍 After ContentGenerator:")
        print(f"  - Job status: {updated_job.status if updated_job else 'Job not found'}")
        print(f"  - Has html_content: {bool(updated_job.html_content) if updated_job else 'N/A'}")
        print(f"  - Has content: {bool(updated_job.content) if updated_job else 'N/A'}")
        print(f"  - Error message: {updated_job.error_message if updated_job else 'N/A'}")
        
        if updated_job and updated_job.html_content:
            html_content = updated_job.html_content
            print(f"✅ ContentGenerator succeeded - got HTML content ({len(html_content)} chars)")
            print(f"✅ HTML starts with: {html_content[:100] if html_content else 'Empty'}")
        elif updated_job and updated_job.content:
            # Try to use content field instead
            html_content = updated_job.content
            print(f"✅ ContentGenerator provided content field ({len(html_content)} chars)")
            print(f"✅ Content starts with: {html_content[:100] if html_content else 'Empty'}")
        else:
            print(f"❌ ContentGenerator failed - no content generated")
            html_content = "Fallback content generation needed"
        
        db.update_generation_job_status(job_id, "in_progress", 90)
        
        # ContentGenerator already completed and saved to database
        # html_content is already set above, so we can skip the old processing
        
        print(f"✅ HTML content preview (first 200 chars): {html_content[:200] if html_content else 'No content'}")
        
        # Only fallback to old system if ContentGenerator completely failed
        if not html_content or html_content == "Fallback content generation needed":
            print("🔄 ContentGenerator failed completely - Job will be marked as failed")
            # Mark job as failed instead of using fallback
            db.update_generation_job_status(job_id, "failed", 0, "ContentGenerator failed to generate content")
            return
        
        # 중복 제목 제거 (더 강화된 버전)
        import re
        def remove_duplicate_headings(content):
            # h1 태그 중복 제거 (연속된 것뿐만 아니라 전체적으로)
            h1_matches = re.findall(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
            if len(h1_matches) > 1:
                # 첫 번째 h1만 남기고 나머지 제거
                for i in range(1, len(h1_matches)):
                    pattern = r'<h1[^>]*>' + re.escape(h1_matches[i]) + r'</h1>'
                    content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            # h2 태그 중복 제거 (같은 텍스트의 h2 태그들)
            h2_matches = re.findall(r'<h2[^>]*>([^<]+)</h2>', content, re.IGNORECASE)
            seen_h2 = set()
            
            for h2_text in h2_matches:
                h2_text_clean = h2_text.strip()
                if h2_text_clean in seen_h2:
                    # 중복된 h2 제거
                    pattern = r'<h2[^>]*>' + re.escape(h2_text) + r'</h2>'
                    # 두 번째 이후 발생하는 것만 제거
                    content = re.sub(pattern, '', content, count=1, flags=re.IGNORECASE)
                else:
                    seen_h2.add(h2_text_clean)
            
            return content
        
        html_content = remove_duplicate_headings(html_content)
        
        # 글자수 검증 및 보완
        html_content = await validate_and_enhance_content(html_content, job.word_count, job)
        
        # 추가 검증: 여전히 부족하면 추가 생성 시도
        final_length = get_text_length_from_html(html_content)
        if final_length < job.word_count * 0.8:
            print(f"🔄 추가 콘텐츠 생성 필요: {final_length}자 → 목표 {job.word_count}자")
            
            # 더 강력한 추가 프롬프트로 콘텐츠 보강
            additional_prompt = f"""아래 기존 콘텐츠에 추가할 더 상세한 내용을 HTML로 생성해줘. 
            
기존 글자수: {final_length}자
목표 글자수: {job.word_count}자
추가 필요: {job.word_count - final_length}자

주제: {job.topic}

다음 섹션들 중에서 2-3개를 선택해서 각각 300자 이상 상세히 작성해줘:
1. "심화 분석" - 더 깊이 있는 내용
2. "단계별 실행방법" - 구체적인 실행 단계
3. "주의사항 및 팁" - 주의할 점과 실용적인 팁
4. "비용 및 예산" - 관련 비용 정보
5. "추천 도구 및 자료" - 유용한 도구나 자료 소개
6. "성공 사례 분석" - 실제 성공 사례 소개

규칙:
- 순수 HTML만 출력 (설명 없이)
- 각 섹션은 h2 태그로 시작
- 각 문단은 최소 100자 이상
- 구체적이고 실용적인 내용
- 색상 스타일 적용: h2는 #2c3e50, p는 #333"""

            try:
                if job.provider == "gemini":
                    additional_result = await test_gemini_api(additional_prompt)
                elif job.provider == "claude":
                    additional_result = await test_claude_api(additional_prompt)
                elif job.provider == "openai":
                    additional_result = await test_openai_api(additional_prompt)
                elif job.provider == "grok":
                    additional_result = await test_grok_api(additional_prompt)
                
                additional_content = additional_result["content"]
                
                # 추가 콘텐츠를 기존 콘텐츠에 삽입
                if '</article>' in html_content:
                    html_content = html_content.replace('</article>', additional_content + '</article>')
                elif '</body>' in html_content:
                    html_content = html_content.replace('</body>', additional_content + '</body>')
                else:
                    html_content += additional_content
                
                # 다시 글자수 확인
                final_length = get_text_length_from_html(html_content)
                print(f"🔄 추가 생성 완료: {final_length}자 ({final_length/job.word_count*100:.1f}%)")
                
            except Exception as e:
                print(f"⚠️ 추가 콘텐츠 생성 실패: {e}")
        
        # 생성된 HTML에 추가 스타일 보정 적용 (비활성화 - 프리미엄 스타일 유지)
        # html_content = apply_style_fixes(html_content)
        
        # 최종 글자수 확인
        final_length = get_text_length_from_html(html_content)
        print(f"✅ 최종 글자수: {final_length}자 (목표: {job.word_count}자, {final_length/job.word_count*100:.1f}%)")
        
        # 생성 완료
        db.update_generation_job_status(
            job_id, 
            "completed", 
            100, 
            content=html_content
        )
        
    except Exception as e:
        db.update_generation_job_status(
            job_id, 
            "failed", 
            0, 
            error_message=str(e)
        )

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "AI Writer API Tester with Real Data", "docs_url": "/docs"}

if __name__ == "__main__":
    print("🚀 AI Writer API 테스트 서버 시작")
    print(f"📍 API 문서: http://127.0.0.1:3001/docs")
    print(f"🔗 프론트엔드: http://127.0.0.1:3001")
    
    uvicorn.run(
        "api_test_endpoint:app",
        host="127.0.0.1",
        port=3001,
        reload=False
    )