#!/usr/bin/env python3
"""Test news link addition functionality."""

import re
import sys
import os

# Add the packages directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages'))

def test_news_link_detection():
    """Test if topics are correctly identified as news topics."""
    
    def is_news_topic(topic: str) -> bool:
        """Check if this is a news/current affairs topic - expanded keywords"""
        news_keywords = ['트럼프', 'trump', '관세', 'tariff', '핫', '이슈', 'top', '순위', 
                        '뉴스', '사건', '정치', '경제', '사회', '최신', '화제', '트렌드', 
                        '현안', '대통령', '정부', '정책', '행정부', '통상', '무역']
        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in news_keywords)
    
    test_topics = [
        ("미국 트럼프의 대 대한민국 관세 총정리", True),
        ("대한민국 핫 이슈 top3", True),
        ("수도권 광역 교통망 개편", False),
        ("인공지능 교육 의무화", False),
        ("트럼프 정부 무역정책", True),
        ("정부 정책 변화", True),
        ("맛집 추천", False),
        ("여행 가이드", False),
    ]
    
    print("Testing News Topic Detection")
    print("=" * 40)
    
    for topic, expected in test_topics:
        result = is_news_topic(topic)
        status = "PASS" if result == expected else "FAIL"
        print(f"{topic} -> {result} ({status})")
    
    return True

def test_news_link_addition():
    """Test adding news links to content sections."""
    
    def _replace_generic_with_news_links(html_content: str, news_links: list) -> str:
        """Add specific news links to content sections."""
        if not news_links:
            return html_content
        
        # Find h2 and h3 headings to add relevant links after them
        section_pattern = r'(<h[23][^>]*>.*?</h[23]>)'
        
        sections_with_links = 0
        max_sections_with_links = min(3, len(news_links))
        
        def add_news_link_after_section(match):
            nonlocal sections_with_links
            
            if sections_with_links < max_sections_with_links:
                news_link = news_links[sections_with_links]
                url = news_link.get('url', '#')
                title = news_link.get('title', '관련 정보')
                source = news_link.get('source', '')
                
                # Verify URL is not prohibited
                if any(prohibited in url.lower() for prohibited in ['google.com', 'search', '%ec%']):
                    sections_with_links += 1
                    return match.group(0)
                
                display_text = title if len(title) < 40 else f"{title[:37]}..."
                if source and len(source) < 15:
                    display_text += f" ({source})"
                
                news_link_html = f'''
<div style="margin: 20px 0 15px 0; padding: 12px; background: #f8f9fa; border-left: 4px solid #3498db; border-radius: 4px;">
    <p style="color: #000000; margin: 0 0 8px 0; font-weight: 600; font-size: 14px;">📰 관련 정보</p>
    <a href="{url}" target="_blank" rel="noopener noreferrer" 
       style="color: #3498db; text-decoration: none; font-weight: 500; font-size: 14px;">
        {display_text}
    </a>
</div>'''
                sections_with_links += 1
                return match.group(0) + news_link_html
            
            return match.group(0)
        
        modified_content = re.sub(section_pattern, add_news_link_after_section, html_content, flags=re.IGNORECASE)
        return modified_content
    
    # Test content
    test_content = '''
<h1>미국 트럼프 관세 정책</h1>
<p>내용입니다.</p>

<h2>트럼프 행정부 통상 정책의 배경</h2>
<p>배경 설명입니다.</p>

<h2>한국에 대한 관세 영향</h2>
<p>영향 분석입니다.</p>

<h2>대응 방안</h2>
<p>대응책 설명입니다.</p>
'''
    
    # Mock news links
    test_news_links = [
        {"title": "기획재정부 관세 대응 발표", "url": "https://www.mosf.go.kr/", "source": "기재부"},
        {"title": "산업통상자원부 무역정책", "url": "https://www.motie.go.kr/", "source": "산업부"},
        {"title": "트럼프 관세 관련 뉴스", "url": "https://news.kbs.co.kr/", "source": "KBS"},
    ]
    
    print("\nTesting News Link Addition")
    print("=" * 40)
    
    print("Original content length:", len(test_content))
    
    modified_content = _replace_generic_with_news_links(test_content, test_news_links.copy())
    
    print("Modified content length:", len(modified_content))
    print("News links added:", modified_content.count('관련 정보'))
    
    # Check if legitimate links are present
    has_gov_links = 'mosf.go.kr' in modified_content and 'motie.go.kr' in modified_content
    has_news_links = 'news.kbs.co.kr' in modified_content
    has_no_google = 'google.com' not in modified_content.lower()
    
    print(f"Contains government links: {has_gov_links}")
    print(f"Contains news links: {has_news_links}")
    print(f"No Google links: {has_no_google}")
    
    if has_gov_links and has_news_links and has_no_google:
        print("PASS: News links added correctly!")
    else:
        print("FAIL: Issues with news link addition")
    
    return True

if __name__ == "__main__":
    test_news_link_detection()
    test_news_link_addition()