#!/usr/bin/env python3
"""Post-process HTML content to remove white text."""

import re

def fix_white_text_in_html(html_content: str) -> str:
    """Fix white or very light colored text in HTML content."""
    if not html_content:
        return html_content
    
    # Patterns to find white or very light colors
    white_patterns = [
        r'color:\s*#fff\b',
        r'color:\s*#ffffff\b',
        r'color:\s*white\b',
        r'color:\s*#f[f-9][f-9][f-9][f-9][f-9]\b',  # Very light colors
        r'color:\s*rgb\(\s*25[0-5],\s*25[0-5],\s*25[0-5]\s*\)',  # RGB white/near-white
    ]
    
    # Default replacement color (dark gray)
    replacement_color = '#000000'
    
    # Replace all white/light colors
    fixed_html = html_content
    for pattern in white_patterns:
        fixed_html = re.sub(pattern, f'color: {replacement_color}', fixed_html, flags=re.IGNORECASE)
    
    return fixed_html

if __name__ == "__main__":
    # Test the function
    test_html = '''
    <p style="color: #ffffff;">This is white text</p>
    <div style="color: white;">This is also white</div>
    <span style="color: #fff;">Another white text</span>
    <h1 style="color: #e74c3c;">This is red - keep it</h1>
    '''
    
    fixed = fix_white_text_in_html(test_html)
    print("Original:")
    print(test_html)
    print("\nFixed:")
    print(fixed)