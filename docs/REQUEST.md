🚀 AI 기반 블로그 포스팅 프롬프트 개선 가이드

기존의 if-elif 방식 대신 더 유연하고 확장 가능한 구조로 개선하는 방법을 정리한 문서입니다.
이 문서에 따라 코드를 수정하면 새로운 주제가 들어와도 쉽게 대응할 수 있습니다.

1️⃣ 개선 목표
애
기존 코드 문제점:

if-elif 분기문으로 인해 새로운 주제 추가 시 코드 수정이 필요함

하드코딩된 텍스트가 코드 안에 있어서 유지보수 어려움

Universal guidance가 단일 옵션이라 주제 확장성이 부족함

개선 목표:

카테고리별 템플릿을 외부 설정(YAML/JSON) 으로 분리

dict 매핑 구조로 간단히 카테고리 참조

fallback 다층 구조로 예상치 못한 주제도 자연스럽게 처리

2️⃣ 아키텍처 개요
사용자 요청 → AI가 주제 카테고리 분류 →
카테고리별 guidance 불러오기(dict or yaml) →
없으면 fallback universal guidance 적용 →
최종 프롬프트 생성

3️⃣ 단계별 구현 방법
🔹 1단계: 카테고리 매핑 딕셔너리
topic_guidance_map = {
"food": "🍽️ 음식/요리 주제 특별 요구사항:\n- 재료 및 조리법 상세 설명\n- 맛집 정보\n- 영양 정보\n- 보관 및 섭취 팁",
"health": "🏥 건강/의료 주제 특별 요구사항:\n- 증상 및 원인 설명\n- 예방 및 관리법\n- 전문 의료진 조언\n- ⚠️ 면책조항 포함",
"tourism": "🗺️ 관광/여행지 주제 특별 요구사항:\n- 명소 상세 정보\n- 실용 정보\n- 계절별 특징\n- 주변 관광 코스",
"transportation": "🚨 교통/이동방법 주제 특별 요구사항:\n- 구체적인 교통수단 상세 설명\n- 소요시간 및 요금\n- 단계별 이동 경로\n- 운행 시간표"
}

🔹 2단계: 외부 설정(YAML)로 분리

📂 guidance.yaml

food:
icon: "🍽️"
guidance: |
음식/요리 주제 특별 요구사항:
- 재료 및 조리법 상세 설명
- 맛집 정보
- 영양 정보
- 보관 및 섭취 팁

health:
icon: "🏥"
guidance: |
건강/의료 주제 특별 요구사항:
- 증상 및 원인 설명
- 예방 및 관리법
- 전문 의료진 조언
- ⚠️ 면책조항 포함

tourism:
icon: "🗺️"
guidance: |
관광/여행지 주제 특별 요구사항:
- 명소 상세 정보
- 실용 정보
- 계절별 특징
- 주변 관광 코스


📂 loader.py

import yaml

def load_guidance():
with open("guidance.yaml", "r", encoding="utf-8") as f:
return yaml.safe_load(f)

guidance_data = load_guidance()

🔹 3단계: Fallback 다층 구조
def get_guidance(topic_category: str, guidance_data: dict) -> str:
if topic_category in guidance_data:
return f"{guidance_data[topic_category]['icon']} {guidance_data[topic_category]['guidance']}"
else:
return f"""
🎯 Universal Guidance:
- 주제의 핵심 가치 설명
- 단계별 접근법 (입문 → 중급 → 전문가)
- 실용적 팁과 주의사항
- 다양한 관점 제시
  """

4️⃣ 주의사항 및 팁

주의사항

이미 버전 관리된 guidance.yaml 파일은 UTF-8 BOM 없는 상태로 저장해야 함

카테고리 키워드는 소문자 통일 (예: food, health)

fallback이 단순하면 결과가 딱딱할 수 있으므로 최소 2~3개 버전 준비 권장

실무 팁

guidance.yaml을 팀 내 공유 저장소에서 관리하면 협업에 유리

필요 시 topic_category 분류를 AI에게 맡겨 "이 주제는 어떤 카테고리인가?" 프롬프트를 활용

장기적으로는 사용자 입력 키워드 기반으로 guidance를 동적으로 확장 가능

5️⃣ 기대 효과

새로운 주제 추가 시 guidance.yaml에만 작성하면 됨 → 코드 수정 불필요

카테고리별 가이드를 모듈화 → 유지보수 및 협업 용이

Fallback 강화 → 예상치 못한 주제에도 안정적인 출력

다양한 주제 확장 가능 (금융, 개발, 스포츠, 라이프스타일 등)