#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기초 데이터 생성 스크립트
새로운 환경에서 데모 및 테스트용 샘플 데이터를 생성합니다.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from uuid import uuid4

# Windows 콘솔 인코딩 설정
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager, GenerationJob, TestResult

def create_sample_generation_jobs(db: DatabaseManager):
    """샘플 콘텐츠 생성 작업 생성"""
    print("[INFO] 샘플 콘텐츠 생성 작업 생성 중...")
    
    sample_jobs = [
        {
            "topic": "서울 3박 4일 여행 코스 추천",
            "provider": "gemini",
            "tone": "friendly",
            "word_count": 1200,
            "workflow_template_id": 2,  # 여행 정보전달
            "content": {
                "title": "서울 3박 4일 완벽 여행 가이드 - 핫플부터 숨은 명소까지",
                "html_content": """
<h1>서울 3박 4일 완벽 여행 가이드</h1>

<h2>1일차: 경복궁과 북촌 한옥마을</h2>
<h3>오전 (9:00-12:00)</h3>
<ul>
<li><strong>경복궁</strong> - 입장료: 성인 3,000원, 관람시간: 2-3시간</li>
<li><strong>국립민속박물관</strong> - 경복궁 내 위치, 추가 요금 없음</li>
<li><strong>팁:</strong> 한복 대여점(1시간 15,000원)에서 한복을 입고 관람하면 입장료 무료</li>
</ul>

<h3>점심 (12:00-13:30)</h3>
<ul>
<li><strong>토속촌 삼계탕</strong> - 예산: 1인 18,000원</li>
<li>주소: 서울 종로구 자하문로 5길 5</li>
<li>현지인 추천: 인삼주와 함께 드세요</li>
</ul>

<h3>오후 (14:00-18:00)</h3>
<ul>
<li><strong>북촌 한옥마을</strong> - 무료, 사진 촬영 명소</li>
<li><strong>삼청동길</strong> - 카페거리, 갤러리 구경</li>
<li><strong>인사동</strong> - 전통 공예품 쇼핑</li>
</ul>

<h2>2일차: 강남과 한강</h2>
<h3>오전 (10:00-12:00)</h3>
<ul>
<li><strong>코엑스 아쿠아리움</strong> - 입장료: 성인 29,000원</li>
<li><strong>봉은사</strong> - 무료, 도심 속 전통 사찰</li>
</ul>

<h3>점심 (12:00-14:00)</h3>
<ul>
<li><strong>강남역 지하상가</strong> - 다양한 먹거리, 예산: 8,000-15,000원</li>
<li>추천: 유명한 떡볶이 맛집들</li>
</ul>

<h3>오후-저녁 (14:00-22:00)</h3>
<ul>
<li><strong>한강공원 (반포지구)</strong> - 무료</li>
<li><strong>반포 무지개 분수</strong> - 분수쇼 시간: 20:00, 20:30, 21:00</li>
<li><strong>한강에서 치킨 배달</strong> - 현지 문화 체험, 예산: 2-3만원</li>
</ul>

<h2>3일차: 홍대와 이태원</h2>
<h3>낮 (11:00-18:00)</h3>
<ul>
<li><strong>홍익대학교 주변</strong> - 거리 퍼포먼스, 클럽 거리</li>
<li><strong>망원 한강공원</strong> - 피크닉 스팟</li>
<li><strong>연남동</strong> - 젊은 감성의 카페거리</li>
</ul>

<h3>저녁 (18:00-23:00)</h3>
<ul>
<li><strong>이태원</strong> - 세계 각국 음식 체험</li>
<li><strong>N서울타워</strong> - 입장료: 성인 16,000원 (전망대)</li>
<li>야경 명소로 유명, 케이블카 이용 추천</li>
</ul>

<h2>4일차: 명동과 동대문</h2>
<h3>오전-오후 (10:00-17:00)</h3>
<ul>
<li><strong>명동성당</strong> - 무료, 역사적 건축물</li>
<li><strong>명동 쇼핑거리</strong> - 화장품, 패션 쇼핑</li>
<li><strong>남대문시장</strong> - 전통시장 체험, 저렴한 쇼핑</li>
</ul>

<h3>저녁 (17:00-22:00)</h3>
<ul>
<li><strong>동대문 디자인 플라자(DDP)</strong> - 무료, 현대 건축물</li>
<li><strong>동대문 야시장</strong> - 야식과 쇼핑의 메카</li>
</ul>

<h2>💰 예산 가이드</h2>
<ul>
<li><strong>숙박:</strong> 1박당 5-10만원 (게스트하우스), 10-20만원 (호텔)</li>
<li><strong>교통:</strong> T-money 카드 충전 5만원 (4일간 충분)</li>
<li><strong>식비:</strong> 1일 3-5만원 (현지 음식 기준)</li>
<li><strong>관광:</strong> 총 10-15만원</li>
<li><strong>쇼핑:</strong> 개인 취향에 따라</li>
</ul>

<h2>🚇 교통 팁</h2>
<ul>
<li>지하철이 가장 효율적, T-money 카드 필수</li>
<li>버스도 같은 카드로 이용 가능</li>
<li>택시 기본요금: 3,800원</li>
<li>카카오택시 앱 추천</li>
</ul>

<h2>⚠️ 주의사항</h2>
<ul>
<li>대부분의 상점은 오후 10-11시에 문 닫음</li>
<li>일요일에는 일부 전통시장 휴무</li>
<li>한국어 번역 앱 미리 다운로드</li>
<li>현금보다 카드 사용이 더 편리</li>
<li>팁 문화 없음</li>
</ul>

<h2>🍜 현지인 추천 숨은 맛집</h2>
<ul>
<li><strong>광장시장 빈대떡</strong> - 저렴하고 맛있는 전통 음식</li>
<li><strong>을지로 3가 곱창골목</strong> - 진짜 현지 분위기</li>
<li><strong>종로 포장마차</strong> - 한국의 야식 문화 체험</li>
</ul>
""",
                "summary": "서울 3박 4일 여행의 완벽한 일정과 실용적인 정보를 담은 가이드. 주요 관광지부터 숨은 명소, 예산 정보, 교통 팁까지 모든 것을 포함.",
                "tags": ["서울여행", "3박4일", "관광코스", "여행가이드", "한국여행", "서울관광"]
            }
        },
        {
            "topic": "2024년 전기차 시장 동향과 정부 정책 분석",
            "provider": "claude",
            "tone": "professional",
            "word_count": 1000,
            "workflow_template_id": 3,  # 시사 정보전달
            "content": {
                "title": "2024년 전기차 시장, 새로운 전환점에 서다 - 정책 변화와 시장 전망",
                "html_content": """
<h1>2024년 전기차 시장, 새로운 전환점에 서다</h1>

<h2>📊 2024년 전기차 시장 현황</h2>

<h3>국내 전기차 판매 동향</h3>
<ul>
<li><strong>2024년 상반기 등록 대수:</strong> 97,342대 (전년 동기 대비 12.3% 증가)</li>
<li><strong>시장 점유율:</strong> 전체 신차 대비 8.7% (2023년 7.2%에서 상승)</li>
<li><strong>누적 등록 대수:</strong> 42만대 돌파 (2024년 8월 기준)</li>
</ul>

<h3>브랜드별 시장 현황</h3>
<ul>
<li><strong>현대차그룹:</strong> 45.2% (아이오닉5, 아이오닉6, EV6 등)</li>
<li><strong>테슬라:</strong> 22.8% (모델Y, 모델3)</li>
<li><strong>BMW:</strong> 8.4% (iX, i4 시리즈)</li>
<li><strong>벤츠:</strong> 6.1% (EQC, EQS 시리즈)</li>
<li><strong>기타:</strong> 17.5% (기아, 폭스바겐, 볼보 등)</li>
</ul>

<h2>🏛️ 정부 정책 변화 분석</h2>

<h3>전기차 보조금 정책 개편</h3>
<h4>2024년 주요 변화</h4>
<ul>
<li><strong>국가 보조금:</strong> 최대 680만원 → 600만원으로 축소</li>
<li><strong>지방자치단체 보조금:</strong> 평균 300-800만원 (지역별 상이)</li>
<li><strong>소득 기준 강화:</strong> 개인 6천만원, 법인 15억원 이하</li>
<li><strong>차량 가격 상한:</strong> 5,500만원 → 5,700만원으로 상향</li>
</ul>

<h4>정책 변화 배경</h4>
<ul>
<li>전기차 시장 성숙도 증가에 따른 정책 지원 단계적 축소</li>
<li>재정 효율성 제고 및 보급 초기 목표 달성</li>
<li>고가 전기차에 대한 세금 혜택 집중 현상 완화</li>
</ul>

<h3>충전 인프라 확충 계획</h3>
<ul>
<li><strong>목표:</strong> 2025년까지 급속충전기 5만기 구축</li>
<li><strong>현재 현황:</strong> 급속충전기 2.8만기 (2024년 기준)</li>
<li><strong>투자 규모:</strong> 정부 1.2조원, 민간 3.8조원</li>
<li><strong>우선 설치 지역:</strong> 고속도로 휴게소, 대형마트, 공동주택</li>
</ul>

<h2>🌍 글로벌 시장과의 비교</h2>

<h3>주요국 전기차 보급률 (2024년)</h3>
<ul>
<li><strong>노르웨이:</strong> 82.4% (세계 1위)</li>
<li><strong>중국:</strong> 35.7% (세계 최대 시장)</li>
<li><strong>독일:</strong> 18.4% (유럽 주요 시장)</li>
<li><strong>미국:</strong> 8.1% (IRA 법안 효과)</li>
<li><strong>한국:</strong> 8.7% (아시아 3위)</li>
</ul>

<h3>국제 정책 동향</h3>
<ul>
<li><strong>EU:</strong> 2035년 내연기관차 판매 금지 정책 유지</li>
<li><strong>미국:</strong> IRA(인플레이션 감축법) 세액공제 7,500달러</li>
<li><strong>중국:</strong> NEV(신에너지차) 쿼터제 지속 운영</li>
<li><strong>일본:</strong> 2035년 전동화 100% 목표 설정</li>
</ul>

<h2>🔮 2025년 전망과 과제</h2>

<h3>긍정적 전망</h3>
<ul>
<li><strong>신차 출시:</strong> 현대 캐스퍼 일렉트릭, 기아 EV3 등 보급형 모델</li>
<li><strong>배터리 기술:</strong> LFP 배터리 도입으로 가격 경쟁력 향상</li>
<li><strong>충전 편의성:</strong> 초고속 충전기 확산으로 충전 시간 단축</li>
<li><strong>중고차 시장:</strong> 전기차 중고시장 형성으로 진입장벽 완화</li>
</ul>

<h3>해결해야 할 과제</h3>
<ul>
<li><strong>가격 경쟁력:</strong> 보조금 축소로 구매 부담 증가</li>
<li><strong>충전 인프라:</strong> 아파트 거주자 충전 접근성 문제</li>
<li><strong>배터리 공급망:</strong> 핵심 원료 수급 안정성 확보</li>
<li><strong>폐배터리 처리:</strong> 친환경 재활용 체계 구축</li>
</ul>

<h2>💡 전문가 의견</h2>

<blockquote>
<p><strong>한국자동차산업협회:</strong> "2024년은 전기차 시장이 본격적인 대중화 단계로 진입하는 원년이 될 것으로 전망된다. 정부 보조금 의존도를 줄이고 시장 경쟁력을 높이는 것이 중요하다."</p>
</blockquote>

<blockquote>
<p><strong>에너지경제연구원:</strong> "충전 인프라 확충과 더불어 전력망 안정성 확보가 전기차 대중화의 핵심 요소가 될 것이다. 스마트 그리드와의 연계도 고려해야 한다."</p>
</blockquote>

<h2>📈 투자 및 산업 영향</h2>

<h3>관련 산업 투자 동향</h3>
<ul>
<li><strong>배터리:</strong> LG에너지솔루션, SK온 등 해외 공장 증설</li>
<li><strong>충전사업:</strong> 환경부 인증 충전사업자 50여개社 경쟁</li>
<li><strong>부품산업:</strong> 전기차 전용 부품 기업 매출 급성장</li>
<li><strong>중고차:</strong> 전기차 전문 중고차 플랫폼 등장</li>
</ul>

<h3>향후 시장 예측</h3>
<ul>
<li><strong>2025년:</strong> 연간 15만대 판매 전망</li>
<li><strong>2030년:</strong> 누적 283만대 보급 목표</li>
<li><strong>시장 규모:</strong> 2030년 35조원 규모 예상</li>
</ul>

<p><strong>결론:</strong> 2024년 전기차 시장은 정부 정책의 변화와 기술 발전이 맞물리면서 새로운 성장 동력을 찾아가는 중요한 시기입니다. 보조금 축소에도 불구하고 기술 발전과 인프라 확충을 통해 지속 가능한 성장 기반을 마련해 나가고 있습니다.</p>
""",
                "summary": "2024년 전기차 시장의 주요 동향과 정부 정책 변화를 분석한 종합 보고서. 시장 현황, 정책 개편, 글로벌 비교, 향후 전망을 객관적으로 제시.",
                "tags": ["전기차", "정책분석", "시장동향", "2024년", "자동차산업", "환경정책"]
            }
        },
        {
            "topic": "집에서 할 수 있는 5분 요가 루틴",
            "provider": "openai",
            "tone": "friendly",
            "word_count": 600,
            "workflow_template_id": 4,  # 소셜 미디어 포스트
            "content": {
                "title": "바쁜 당신을 위한 5분 요가 ✨ 집에서 간단하게!",
                "html_content": """
<h1>🧘‍♀️ 바쁜 당신을 위한 5분 요가 루틴</h1>

<p>매일 바쁜 일상 속에서도 건강을 챙기고 싶다면? <strong>집에서 5분만 투자해도 충분해요!</strong> 🏠✨</p>

<h2>🌅 아침용 에너지 충전 루틴</h2>

<h3>1️⃣ 고양이-소 자세 (1분)</h3>
<ul>
<li>네발기기 자세에서 시작</li>
<li>척추를 둥글게 → 배를 아래로</li>
<li>5-8회 반복하면서 깊게 호흡 🐱</li>
<li><strong>효과:</strong> 척추 유연성 UP, 아침 경직 해소</li>
</ul>

<h3>2️⃣ 아래를 보는 개 자세 (30초)</h3>
<ul>
<li>손과 발로 바닥 지지, 엉덩이 높이 들기</li>
<li>전신 스트레칭의 완벽한 자세 🐕</li>
<li><strong>효과:</strong> 햄스트링, 어깨 스트레칭</li>
</ul>

<h3>3️⃣ 전사 자세 1번 (양쪽 각 1분)</h3>
<ul>
<li>한 발 앞으로 크게 내딛기</li>
<li>뒷다리 쭉 펴고 팔 위로</li>
<li><strong>파워포즈로 하루를 시작하세요!</strong> 💪</li>
</ul>

<h3>4️⃣ 나무 자세 (양쪽 각 30초)</h3>
<ul>
<li>한 발로 서서 다른 발을 허벅지에</li>
<li>균형감각과 집중력 향상 🌳</li>
<li><strong>팁:</strong> 벽에 기대도 OK!</li>
</ul>

<h3>5️⃣ 아이 자세 (30초)</h3>
<ul>
<li>무릎 꿇고 앉아 팔을 앞으로</li>
<li>마음의 평온을 찾는 시간 🧘‍♀️</li>
</ul>

<h2>🌙 저녁용 릴랙스 루틴</h2>

<h3>🌸 꽃봉오리 비틀기 (양쪽 각 1분)</h3>
<ul>
<li>다리 꼬고 앉아 몸통 비틀기</li>
<li>하루 종일 쌓인 척추 긴장 해소</li>
</ul>

<h3>🦋 나비 자세 (1분)</h3>
<ul>
<li>발바닥 붙이고 앉아 무릎을 바닥으로</li>
<li>고관절 유연성 향상</li>
</ul>

<h3>🛌 다리 벽에 올리기 (2분)</h3>
<ul>
<li>누워서 다리를 벽에 기대기</li>
<li>혈액순환 개선, 부종 완화</li>
<li><strong>꿀잠 보장! 😴</strong></li>
</ul>

<h2>💡 성공하는 요가 팁</h2>

<h3>🕐 시간 설정</h3>
<ul>
<li><strong>아침:</strong> 기상 후 5분</li>
<li><strong>저녁:</strong> 잠들기 1시간 전</li>
<li><strong>점심:</strong> 업무 중 스트레칭 타임</li>
</ul>

<h3>📱 앱 추천</h3>
<ul>
<li><strong>Down Dog Yoga:</strong> 초보자 친화적</li>
<li><strong>Daily Yoga:</strong> 5분 루틴 제공</li>
<li><strong>YouTube:</strong> 무료 영상 많음</li>
</ul>

<h3>🎯 동기부여 꿀팁</h3>
<ul>
<li>✅ 요가매트 항상 펼쳐두기</li>
<li>📅 달력에 체크하기</li>
<li>📸 인스타그램에 인증샷</li>
<li>👥 친구와 함께 챌린지</li>
</ul>

<h2>🎉 이런 변화를 느껴보세요!</h2>

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin: 20px 0;">
<h3>1주일 후:</h3>
<ul>
<li>🌅 아침에 더 상쾌하게 일어나요</li>
<li>💪 몸이 더 유연해져요</li>
<li>😌 스트레스가 줄어들어요</li>
</ul>

<h3>1개월 후:</h3>
<ul>
<li>🧘‍♀️ 균형감각이 좋아져요</li>
<li>😴 수면의 질이 향상돼요</li>
<li>💆‍♀️ 어깨 결림이 사라져요</li>
</ul>
</div>

<h2>📢 지금 바로 시작하세요!</h2>

<p><strong>요가는 완벽함이 아니라 꾸준함이에요!</strong> 💜</p>

<p>오늘 저녁부터 5분만 투자해보세요. 작은 변화가 큰 차이를 만들어요! ✨</p>

<p><strong>💬 댓글로 여러분의 요가 경험을 공유해주세요!</strong><br>
<strong>🔄 도움이 되었다면 리포스트도 부탁드려요!</strong></p>

<p style="text-align: center; font-size: 18px; margin-top: 30px;">
<strong>🧘‍♀️ #홈요가 #5분요가 #힐링타임 #건강한하루 #요가초보 #스트레칭 #셀프케어</strong>
</p>
""",
                "summary": "바쁜 현대인을 위한 집에서 할 수 있는 5분 요가 루틴. 아침 에너지 충전용과 저녁 릴랙스용 동작들을 친근하고 재미있게 소개.",
                "tags": ["요가", "홈트레이닝", "5분운동", "스트레칭", "건강관리", "힐링"]
            }
        },
        {
            "topic": "부산 해운대 맛집 베스트 5",
            "provider": "gemini",
            "tone": "casual",
            "word_count": 800,
            "workflow_template_id": 2,  # 여행 정보전달
            "content": {
                "title": "부산 해운대 현지인이 추천하는 진짜 맛집 5곳",
                "html_content": """
<h1>🏖️ 부산 해운대 현지인 추천 맛집 5곳</h1>

<p>해운대 가면 꼭 가봐야 할 맛집들을 현지인의 시선으로 엄선했어요! 관광지 바가지 말고 <strong>진짜 맛집</strong>만 골라드릴게요 😋</p>

<h2>🥢 1위: 할매가야밀면 (냉면/밀면)</h2>

<div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0;">
<h3>📍 위치 정보</h3>
<ul>
<li><strong>주소:</strong> 부산 해운대구 구남로 31</li>
<li><strong>영업시간:</strong> 10:30 - 21:00 (월요일 휴무)</li>
<li><strong>주차:</strong> 주변 유료주차장 이용</li>
<li><strong>해운대역에서 도보 7분</strong></li>
</ul>
</div>

<h3>💰 가격 정보</h3>
<ul>
<li>밀면: 7,000원</li>
<li>비빔밀면: 7,500원</li>
<li>만두: 6,000원</li>
</ul>

<h3>🌟 현지인 평가</h3>
<p>50년 전통의 부산 밀면 원조 맛집! 육수가 진짜 깊고 면발이 쫄깃해요. 관광객보다 현지인이 더 많이 찾는 곳이라 그런지 가격도 합리적이고 맛도 보장됩니다.</p>

<p><strong>🍜 꿀팁:</strong> 비빔밀면도 맛있지만 처음이라면 물밀면 강추! 만두는 꼭 추가 주문하세요.</p>

<hr>

<h2>🦀 2위: 민락횟집 (회/해산물)</h2>

<div style="background: #e3f2fd; padding: 15px; border-radius: 10px; margin: 15px 0;">
<h3>📍 위치 정보</h3>
<ul>
<li><strong>주소:</strong> 부산 수영구 민락수변로 29</li>
<li><strong>영업시간:</strong> 11:00 - 23:00 (연중무휴)</li>
<li><strong>주차:</strong> 매장 전용 주차장 10대</li>
<li><strong>광안리 해변 바로 앞, 해운대에서 차로 15분</strong></li>
</ul>
</div>

<h3>💰 가격 정보</h3>
<ul>
<li>모듬회 (2-3인): 60,000원</li>
<li>활어회 (kg당): 35,000-50,000원</li>
<li>매운탕: 12,000원</li>
<li>해물파전: 15,000원</li>
</ul>

<h3>🌟 현지인 평가</h3>
<p>광안대교 뷰가 끝내주는 곳! 회도 신선하고 매운탕도 칼칼해서 술 한잔하기 딱 좋아요. 특히 저녁에 가면 야경이 정말 예뻐서 데이트 코스로도 완벽합니다.</p>

<p><strong>🌉 꿀팁:</strong> 저녁 7시 이후에 가면 광안대교 조명을 보면서 식사할 수 있어요. 미리 예약 필수!</p>

<hr>

<h2>🍖 3위: 원조할매집 (돼지국밥)</h2>

<div style="background: #fff3e0; padding: 15px; border-radius: 10px; margin: 15px 0;">
<h3>📍 위치 정보</h3>
<ul>
<li><strong>주소:</strong> 부산 해운대구 해운대해변로 32</li>
<li><strong>영업시간:</strong> 24시간 (연중무휴)</li>
<li><strong>주차:</strong> 주변 공영주차장 이용</li>
<li><strong>해운대 해수욕장에서 도보 3분</strong></li>
</ul>
</div>

<h3>💰 가격 정보</h3>
<ul>
<li>돼지국밥: 8,000원</li>
<li>수육: 22,000원 (중)</li>
<li>순대: 15,000원</li>
<li>소주: 4,000원</li>
</ul>

<h3>🌟 현지인 평가</h3>
<p>해운대에서 40년 된 전설의 돼지국밥집! 24시간이라 해수욕 후 해장용으로도 최고예요. 국물이 진짜 진하고 고기도 부드러워서 관광객들도 줄 서서 먹습니다.</p>

<p><strong>🥢 꿀팁:</strong> 새우젓과 부추 듬뿍 넣어서 드세요. 술 마신 다음날 아침에도 강추!</p>

<hr>

<h2>☕ 4위: 더베이101 (카페/브런치)</h2>

<div style="background: #f3e5f5; padding: 15px; border-radius: 10px; margin: 15px 0;">
<h3>📍 위치 정보</h3>
<ul>
<li><strong>주소:</strong> 부산 해운대구 달맞이길 117</li>
<li><strong>영업시간:</strong> 09:00 - 22:00 (연중무휴)</li>
<li><strong>주차:</strong> 전용 주차장 15대</li>
<li><strong>달맞이고개 중턱, 해운대 전망 끝판왕</strong></li>
</ul>
</div>

<h3>💰 가격 정보</h3>
<ul>
<li>아메리카노: 6,500원</li>
<li>브런치 세트: 18,000-25,000원</li>
<li>케이크: 7,000원</li>
</ul>

<h3>🌟 현지인 평가</h3>
<p>해운대 전체가 한눈에 보이는 뷰맛집! 인스타그램 감성 카페지만 커피 맛도 좋고 브런치도 푸짐해요. 특히 일출이나 일몰 시간에 가면 정말 감동적입니다.</p>

<p><strong>📸 꿀팁:</strong> 창가 자리 예약은 필수! 평일 오후 3-5시가 사람 적고 뷰 보기 좋아요.</p>

<hr>

<h2>🍤 5위: 기장시장 곰장어골목</h2>

<div style="background: #e8f5e8; padding: 15px; border-radius: 10px; margin: 15px 0;">
<h3>📍 위치 정보</h3>
<ul>
<li><strong>주소:</strong> 부산 기장군 기장읍 기장대로 560</li>
<li><strong>영업시간:</strong> 17:00 - 24:00 (목요일 휴무)</li>
<li><strong>주차:</strong> 기장시장 공영주차장</li>
<li><strong>해운대에서 차로 30분, 버스 40분</strong></li>
</ul>
</div>

<h3>💰 가격 정보</h3>
<ul>
<li>곰장어구이 (1kg): 45,000원</li>
<li>곰장어탕: 12,000원</li>
<li>멸치회: 15,000원</li>
</ul>

<h3>🌟 현지인 평가</h3>
<p>부산 사람들도 특별한 날에만 가는 곳! 곰장어가 이렇게 맛있는 줄 몰랐다는 분들이 많아요. 좀 멀긴 하지만 정말 특별한 경험을 원한다면 강추합니다.</p>

<p><strong>🔥 꿀팁:</strong> 곰장어는 미리 예약하고 가세요. 멸치회도 같이 시키면 술안주로 완벽!</p>

<h2>🚗 교통 및 코스 추천</h2>

<h3>대중교통 이용시</h3>
<ul>
<li><strong>지하철 2호선 해운대역</strong> 하차 후 도보 이용</li>
<li><strong>버스:</strong> 해운대 해수욕장 정류장 이용</li>
<li><strong>택시:</strong> 부산역에서 약 20분, 15,000원</li>
</ul>

<h3>추천 코스</h3>
<ol>
<li><strong>점심:</strong> 할매가야밀면에서 밀면</li>
<li><strong>오후:</strong> 해운대 해수욕장 산책</li>
<li><strong>카페:</strong> 더베이101에서 커피타임</li>
<li><strong>저녁:</strong> 민락횟집에서 회 + 야경</li>
<li><strong>마무리:</strong> 원조할매집에서 해장국밥</li>
</ol>

<h2>💡 현지인 꿀팁</h2>

<ul>
<li>🅿️ <strong>주차:</strong> 해운대는 주차가 어려우니 대중교통 추천</li>
<li>⏰ <strong>시간:</strong> 점심시간(12-13시), 저녁시간(6-8시) 피하면 대기 줄어요</li>
<li>💳 <strong>결제:</strong> 현금 할인 해주는 곳 많으니 현금 준비</li>
<li>🍺 <strong>술:</strong> 해변가에서 치맥도 부산의 묘미!</li>
<li>🌊 <strong>계절:</strong> 여름엔 사람 많으니 봄/가을 추천</li>
</ul>

<p style="text-align: center; font-size: 18px; margin-top: 30px; background: linear-gradient(45deg, #ff6b6b, #ffd93d); color: white; padding: 15px; border-radius: 10px;">
<strong>🏖️ 부산 해운대에서 맛있는 여행 되세요! 🦀</strong>
</p>
""",
                "summary": "부산 해운대 지역의 현지인 추천 맛집 5곳을 상세히 소개. 위치, 가격, 특징, 꿀팁까지 실용적인 정보를 재미있게 전달.",
                "tags": ["부산맛집", "해운대맛집", "부산여행", "현지인추천", "해운대", "부산음식"]
            }
        },
        {
            "topic": "ChatGPT vs Claude 비교 분석",
            "provider": "claude",
            "tone": "professional",
            "word_count": 900,
            "workflow_template_id": 3,  # 시사 정보전달
            "content": {
                "title": "AI 어시스턴트 대결: ChatGPT vs Claude 2024년 종합 비교",
                "html_content": """
<h1>AI 어시스턴트 대결: ChatGPT vs Claude 2024년 종합 비교</h1>

<h2>🤖 개요</h2>
<p>2024년 현재 가장 주목받는 두 AI 어시스턴트인 ChatGPT(OpenAI)와 Claude(Anthropic)를 다양한 관점에서 비교 분석해보겠습니다.</p>

<h2>📊 기본 정보 비교</h2>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
<tr style="background-color: #f5f5f5;">
<th style="border: 1px solid #ddd; padding: 12px; text-align: left;">구분</th>
<th style="border: 1px solid #ddd; padding: 12px; text-align: left;">ChatGPT</th>
<th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Claude</th>
</tr>
<tr>
<td style="border: 1px solid #ddd; padding: 12px;"><strong>개발사</strong></td>
<td style="border: 1px solid #ddd; padding: 12px;">OpenAI</td>
<td style="border: 1px solid #ddd; padding: 12px;">Anthropic</td>
</tr>
<tr>
<td style="border: 1px solid #ddd; padding: 12px;"><strong>최신 모델</strong></td>
<td style="border: 1px solid #ddd; padding: 12px;">GPT-4 Turbo</td>
<td style="border: 1px solid #ddd; padding: 12px;">Claude 3.5 Sonnet</td>
</tr>
<tr>
<td style="border: 1px solid #ddd; padding: 12px;"><strong>출시일</strong></td>
<td style="border: 1px solid #ddd; padding: 12px;">2022년 11월</td>
<td style="border: 1px solid #ddd; padding: 12px;">2022년 3월</td>
</tr>
<tr>
<td style="border: 1px solid #ddd; padding: 12px;"><strong>무료 버전</strong></td>
<td style="border: 1px solid #ddd; padding: 12px;">GPT-3.5 기반</td>
<td style="border: 1px solid #ddd; padding: 12px;">Claude 3 Haiku 기반</td>
</tr>
</table>

<h2>💰 가격 정책</h2>

<h3>ChatGPT</h3>
<ul>
<li><strong>무료:</strong> 월 사용량 제한, GPT-3.5 사용</li>
<li><strong>Plus ($20/월):</strong> GPT-4 접근, 우선 접속, 플러그인 사용</li>
<li><strong>Enterprise:</strong> 맞춤형 가격, 보안 강화</li>
</ul>

<h3>Claude</h3>
<ul>
<li><strong>무료:</strong> 일일 메시지 제한, Claude 3 Haiku</li>
<li><strong>Pro ($20/월):</strong> Claude 3.5 Sonnet, 5배 많은 사용량</li>
<li><strong>Team ($25/월/인):</strong> 팀 협업 기능 추가</li>
</ul>

<h2>🧠 성능 비교</h2>

<h3>언어 이해 및 생성</h3>
<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0;">
<h4>ChatGPT 강점</h4>
<ul>
<li>창의적 글쓰기 및 스토리텔링</li>
<li>코드 생성 및 디버깅</li>
<li>다양한 플러그인 생태계</li>
<li>이미지 생성 (DALL-E 연동)</li>
</ul>
</div>

<div style="background: #f3e5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
<h4>Claude 강점</h4>
<ul>
<li>긴 문서 분석 및 요약</li>
<li>논리적 추론 및 분석</li>
<li>안전하고 정확한 답변</li>
<li>복잡한 지시사항 이해</li>
</ul>
</div>

<h3>벤치마크 성능</h3>
<ul>
<li><strong>수학 문제 해결:</strong> Claude 3.5 Sonnet 우세</li>
<li><strong>코딩 능력:</strong> GPT-4 Turbo 근소 우세</li>
<li><strong>텍스트 이해:</strong> 비슷한 수준</li>
<li><strong>창의성:</strong> ChatGPT 우세</li>
</ul>

<h2>🛡️ 안전성 및 윤리</h2>

<h3>ChatGPT</h3>
<ul>
<li><strong>콘텐츠 정책:</strong> 유해 콘텐츠 필터링 시스템</li>
<li><strong>데이터 보안:</strong> 대화 내용 학습 활용 (설정 변경 가능)</li>
<li><strong>편향성:</strong> 지속적 개선 중, 일부 편향 여전히 존재</li>
</ul>

<h3>Claude</h3>
<ul>
<li><strong>Constitutional AI:</strong> 자체 윤리 규칙 적용</li>
<li><strong>데이터 보안:</strong> 대화 내용 학습에 미사용</li>
<li><strong>편향성:</strong> 상대적으로 중립적 응답</li>
</ul>

<h2>🚀 특별 기능</h2>

<h3>ChatGPT만의 기능</h3>
<ul>
<li><strong>플러그인:</strong> Wolfram, Zapier 등 다양한 외부 서비스 연동</li>
<li><strong>DALL-E:</strong> 텍스트로 이미지 생성</li>
<li><strong>Code Interpreter:</strong> 코드 실행 및 데이터 분석</li>
<li><strong>음성 대화:</strong> 음성 입출력 지원</li>
</ul>

<h3>Claude만의 기능</h3>
<ul>
<li><strong>긴 컨텍스트:</strong> 200K 토큰까지 처리 가능</li>
<li><strong>문서 업로드:</strong> PDF, 이미지 등 파일 분석</li>
<li><strong>Artifacts:</strong> 코드, 문서 등을 별도 패널에서 실행</li>
<li><strong>비전 분석:</strong> 이미지 이해 및 분석</li>
</ul>

<h2>📈 사용 사례별 추천</h2>

<div style="background: #fff3e0; padding: 20px; border-radius: 10px; margin: 20px 0;">
<h3>🎨 창작 활동</h3>
<p><strong>추천: ChatGPT</strong></p>
<ul>
<li>소설, 시나리오 작성</li>
<li>마케팅 카피 제작</li>
<li>이미지 생성이 필요한 프로젝트</li>
</ul>
</div>

<div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
<h3>📊 분석 업무</h3>
<p><strong>추천: Claude</strong></p>
<ul>
<li>긴 문서 요약 및 분석</li>
<li>법률, 학술 문서 검토</li>
<li>복잡한 논리적 추론</li>
</ul>
</div>

<div style="background: #f3e5f5; padding: 20px; border-radius: 10px; margin: 20px 0;">
<h3>💻 개발 업무</h3>
<p><strong>추천: 상황에 따라</strong></p>
<ul>
<li><strong>ChatGPT:</strong> 플러그인 활용, 빠른 프로토타이핑</li>
<li><strong>Claude:</strong> 코드 리뷰, 복잡한 로직 설계</li>
</ul>
</div>

<h2>🌐 접근성 및 가용성</h2>

<h3>지역별 접근성</h3>
<ul>
<li><strong>ChatGPT:</strong> 전 세계 대부분 지역에서 사용 가능</li>
<li><strong>Claude:</strong> 미국, 영국 등 일부 지역에서만 사용 가능 (VPN 필요)</li>
</ul>

<h3>API 및 통합</h3>
<ul>
<li><strong>ChatGPT:</strong> 성숙한 API, 다양한 제3자 도구 지원</li>
<li><strong>Claude:</strong> API 제공, 상대적으로 제한적인 생태계</li>
</ul>

<h2>🔮 미래 전망</h2>

<h3>개발 방향</h3>
<ul>
<li><strong>OpenAI:</strong> GPT-5 개발, 범용 AI 에이전트</li>
<li><strong>Anthropic:</strong> 안전성 강화, Constitutional AI 발전</li>
</ul>

<h3>시장 동향</h3>
<ul>
<li><strong>경쟁 심화:</strong> Google Bard, Microsoft Copilot 등 참여</li>
<li><strong>특화 서비스:</strong> 도메인별 특화 AI 등장</li>
<li><strong>규제 강화:</strong> AI 윤리 및 안전성 규제 증가</li>
</ul>

<h2>📋 종합 평가</h2>

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin: 20px 0;">
<h3>결론</h3>
<p><strong>ChatGPT</strong>는 창의성과 다양한 기능 확장성에서 우세하며, <strong>Claude</strong>는 안전성과 분석 능력에서 강점을 보입니다.</p>

<p>용도에 따른 선택이 중요하며, 두 서비스 모두 지속적으로 발전하고 있어 미래의 변화를 주목할 필요가 있습니다.</p>
</div>

<h3>최종 추천</h3>
<ul>
<li><strong>일반 사용자:</strong> ChatGPT (접근성과 기능의 다양성)</li>
<li><strong>비즈니스 사용자:</strong> Claude (안전성과 분석 능력)</li>
<li><strong>개발자:</strong> 두 서비스 모두 활용 권장</li>
<li><strong>연구자:</strong> Claude (긴 문서 처리 능력)</li>
</ul>
""",
                "summary": "ChatGPT와 Claude를 다양한 관점에서 종합 비교한 분석 보고서. 기능, 성능, 가격, 사용 사례별 추천을 객관적으로 제시.",
                "tags": ["AI비교", "ChatGPT", "Claude", "인공지능", "기술분석", "2024년"]
            }
        }
    ]
    
    # 샘플 작업들 생성
    for i, job_data in enumerate(sample_jobs):
        # 작업 완료 시간을 다양하게 설정
        created_time = datetime.now() - timedelta(days=i*2, hours=i*3)
        completed_time = created_time + timedelta(minutes=30+i*10)
        
        job = GenerationJob(
            job_id=str(uuid4()),
            provider=job_data["provider"],
            topic=job_data["topic"],
            tone=job_data["tone"],
            word_count=job_data["word_count"],
            include_images=False,  # 이미지는 일단 false로
            target_language="ko",
            status="completed",
            progress=100,
            content=json.dumps(job_data["content"]),
            html_content=job_data["content"]["html_content"],
            created_at=created_time.isoformat(),
            updated_at=completed_time.isoformat()
        )
        
        db.save_generation_job(job)
        print(f"[OK] 샘플 작업 {i+1}/5 생성: {job_data['topic']}")

def create_sample_test_results(db: DatabaseManager):
    """샘플 테스트 결과 생성"""
    print("[INFO] 샘플 테스트 결과 생성 중...")
    
    providers = ["gemini", "openai", "claude", "grok"]
    
    for provider in providers:
        for i in range(10):  # 각 제공자별 10개씩
            # 성공/실패를 9:1 비율로 설정
            success = i < 9
            
            if success:
                test_result = TestResult(
                    provider=provider,
                    prompt=f"{provider} 테스트 프롬프트 {i+1}",
                    response=f"이것은 {provider}의 성공적인 응답입니다. 테스트 번호: {i+1}",
                    success=True,
                    token_usage={
                        "input_tokens": 50 + i*5,
                        "output_tokens": 100 + i*10,
                        "total_tokens": 150 + i*15
                    },
                    response_time_ms=1000 + i*100,
                    created_at=(datetime.now() - timedelta(hours=i)).isoformat()
                )
            else:
                test_result = TestResult(
                    provider=provider,
                    prompt=f"{provider} 실패 테스트 프롬프트",
                    response="",
                    success=False,
                    error_message="API 요청 실패 - 네트워크 오류",
                    response_time_ms=5000,
                    created_at=(datetime.now() - timedelta(hours=i)).isoformat()
                )
            
            db.save_test_result(test_result)
    
    print("[OK] 각 AI 제공자별 10개씩 테스트 결과 생성 완료")

def main():
    """메인 실행 함수"""
    print("[START] 기초 데이터 생성 스크립트 시작")
    print("=" * 50)
    
    # 데이터베이스 초기화
    db = DatabaseManager()
    print("[OK] 데이터베이스 연결 완료")
    
    try:
        # 샘플 콘텐츠 생성 작업 생성
        create_sample_generation_jobs(db)
        print()
        
        # 샘플 테스트 결과 생성
        create_sample_test_results(db)
        print()
        
        print("[SUCCESS] 모든 기초 데이터 생성 완료!")
        print("=" * 50)
        print("[INFO] 생성된 데이터:")
        
        # 통계 출력
        jobs = db.get_generation_jobs()
        print(f"   - 콘텐츠 생성 작업: {len(jobs)}개")
        
        for provider in ["gemini", "openai", "claude", "grok"]:
            stats = db.get_provider_stats(provider)
            print(f"   - {provider} 테스트: {stats['total_tests']}회 ({stats['success_rate']}% 성공)")
        
        print("\n[INFO] 웹 인터페이스에서 확인 가능:")
        print("   - http://127.0.0.1:3000 (프론트엔드)")
        print("   - http://127.0.0.1:3005/docs (API 문서)")
        
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()