#!/usr/bin/env python3
"""
Gemini API 테스트 스크립트
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

async def test_gemini_api():
    """Gemini API 연결 테스트"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Gemini API 엔드포인트
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    
    # 테스트 요청 데이터
    payload = {
        "contents": [{
            "parts": [{
                "text": "안녕하세요! 간단한 인사말로 답해주세요."
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Gemini API 테스트 시작...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"📊 응답 상태코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"✅ API 연결 성공!")
                    print(f"🤖 Gemini 응답: {content}")
                    
                    # 토큰 사용량 정보 (있다면)
                    if "usageMetadata" in result:
                        usage = result["usageMetadata"]
                        print(f"📈 토큰 사용량: {usage}")
                    
                    return True
                else:
                    print("❌ 응답에 콘텐츠가 없습니다.")
                    print(f"응답 데이터: {result}")
                    return False
                    
            else:
                print(f"❌ API 호출 실패: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"에러 정보: {error_data}")
                except:
                    print(f"에러 응답: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ API 호출 타임아웃")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

async def test_gemini_content_generation():
    """콘텐츠 생성 테스트"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "인공지능의 미래에 대해 300자 정도로 전문적인 톤으로 설명해주세요."
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
        }
    }
    
    try:
        print("\n📝 콘텐츠 생성 테스트 시작...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"✅ 콘텐츠 생성 성공!")
                    print(f"📄 생성된 콘텐츠:\n{content}")
                    
                    # 안전성 등급 확인
                    if "safetyRatings" in result["candidates"][0]:
                        safety = result["candidates"][0]["safetyRatings"]
                        print(f"🔒 안전성 등급: {safety}")
                    
                    return True
                else:
                    print("❌ 콘텐츠 생성 실패")
                    return False
                    
            else:
                print(f"❌ 콘텐츠 생성 API 호출 실패: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 콘텐츠 생성 오류: {e}")
        return False

async def main():
    """메인 테스트 실행"""
    print("=" * 50)
    print("🧪 Gemini API 테스트")
    print("=" * 50)
    
    # 기본 연결 테스트
    basic_test = await test_gemini_api()
    
    if basic_test:
        # 콘텐츠 생성 테스트
        content_test = await test_gemini_content_generation()
        
        if content_test:
            print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
            print("✅ Gemini API가 정상적으로 작동합니다.")
        else:
            print("\n⚠️  기본 연결은 성공했으나 콘텐츠 생성에 문제가 있습니다.")
    else:
        print("\n❌ Gemini API 연결에 실패했습니다.")
        print("🔧 API 키를 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())