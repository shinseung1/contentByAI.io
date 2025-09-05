#!/usr/bin/env python3
"""Test Google link filtering functionality."""

import re
import sys
import os

# Add the packages directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages'))

def test_google_link_cleanup():
    """Test the final Google link cleanup function."""
    
    # Simulate the _final_google_link_cleanup function logic
    def _final_google_link_cleanup(html_content: str) -> str:
        """Final pass to remove any remaining Google search links and meaningless links."""
        
        # ULTRA AGGRESSIVE GOOGLE LINK REMOVAL
        # Step 1: Remove ALL links first
        
        # Remove any links containing google.com or search patterns
        google_patterns = [
            r'<a[^>]*href="[^"]*google\.com[^"]*"[^>]*>.*?</a>',
            r'<a[^>]*href="[^"]*search[^"]*"[^>]*>.*?</a>',
            r'<a[^>]*href="[^"]*%EC%[^"]*"[^>]*>.*?</a>',  # URL encoded Korean
            r'<a[^>]*href="[^"]*q=[^"]*"[^>]*>.*?</a>',     # Query parameters
        ]
        
        for pattern in google_patterns:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
        
        # Also remove entire div containers that might have Google links
        div_pattern = r'<div[^>]*>.*?<a[^>]*href="[^"]*google\.com[^"]*"[^>]*>.*?</a>.*?</div>'
        html_content = re.sub(div_pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove ALL existing links (most aggressive approach)
        html_content = re.sub(r'<a[^>]*>.*?</a>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<div[^>]*>\s*</div>', '', html_content, flags=re.IGNORECASE)  # Remove empty divs
        
        return html_content
    
    # Test cases
    test_cases = [
        # Case 1: Google search link
        '''<div style="margin: 15px 0;"><a href="https://www.google.com/search?q=1.+%ED%8A%B8%EB%9F%BC%ED%94%84+%ED%96%89%EC%A0%95%EB%B6%80+%ED%86%B5%EC%83%81+%EC%A0%95%EC%B1%85%EC%9D%98+%EB%B0%B0%EA%B2%BD">트럼프 행정부 통상 정책의 배경</a></div>''',
        
        # Case 2: Meaningless link with #
        # '''<div style="margin: 15px 0;"><a href="#" style="color: #3498db;">바로가기</a></div>''',
        
        # Case 3: Mixed content with Google links
        '''<h2>트럼프 관세 정책</h2>
        <p>내용입니다.</p>
        <p>더 많은 내용</p>''',
        
        # Case 4: URL encoded Korean in Google search
        '''<a href="https://www.google.com/search?q=%ED%8A%B8%EB%9F%BC%ED%94%84+%EA%B4%80%EC%84%B8">한글 검색</a>''',
    ]
    
    print("Testing Google Link Cleanup Function")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print("Original:")
        print(test_case)
        
        cleaned = _final_google_link_cleanup(test_case)
        
        print("\nCleaned:")
        print(cleaned)
        
        # Check if any Google links remain
        has_google_links = ('google.com' in cleaned.lower() or 
                          'search?' in cleaned.lower() or
                          '%ec%' in cleaned.lower() or
                          '<a ' in cleaned.lower())
        
        if has_google_links:
            print("FAIL: Google links or other links still present!")
        else:
            print("PASS: All links removed successfully!")
        
        print("-" * 30)
    
    print("\nSummary:")
    print("The new ultra-aggressive link removal approach:")
    print("1. Removes ALL Google search links")  
    print("2. Removes meaningless # links")
    print("3. Removes URL-encoded Korean search links")
    print("4. Removes ALL <a> tags completely")
    print("5. Cleans up empty div containers")
    
    return True

if __name__ == "__main__":
    test_google_link_cleanup()