#!/usr/bin/env python3
"""
Simple test for Korean text processing functions
"""

def test_korean_preservation():
    """Test that all our Unicode processing functions preserve Korean characters"""
    
    from packages.gen.content_generator import safe_print, remove_emojis, ContentGenerator
    
    test_korean = "인공지능 기술의 발전"  # No emojis to avoid console issues
    
    # Test safe_print function
    safe_result = safe_print(test_korean)
    
    # Test remove_emojis function
    emoji_result = remove_emojis(test_korean)
    
    # Test safe_print_str method
    generator = ContentGenerator()
    safe_str_result = generator.safe_print_str(test_korean)
    
    # Count Korean characters in original
    korean_chars_original = sum(1 for c in test_korean if '\uAC00' <= c <= '\uD7AF')
    
    # Count Korean characters in results
    korean_chars_safe = sum(1 for c in safe_result if '\uAC00' <= c <= '\uD7AF')
    korean_chars_emoji = sum(1 for c in emoji_result if '\uAC00' <= c <= '\uD7AF')
    korean_chars_safe_str = sum(1 for c in safe_str_result if '\uAC00' <= c <= '\uD7AF')
    
    # Write results to file to avoid console encoding issues
    with open('korean_test_results.txt', 'w', encoding='utf-8') as f:
        f.write("=== KOREAN CHARACTER PRESERVATION TEST ===\n")
        f.write(f"Original text: {test_korean}\n")
        f.write(f"Korean chars in original: {korean_chars_original}\n\n")
        
        f.write(f"safe_print result: {safe_result}\n")
        f.write(f"Korean chars in safe_print: {korean_chars_safe}\n")
        
        f.write(f"remove_emojis result: {emoji_result}\n")
        f.write(f"Korean chars in remove_emojis: {korean_chars_emoji}\n")
        
        f.write(f"safe_print_str result: {safe_str_result}\n")
        f.write(f"Korean chars in safe_print_str: {korean_chars_safe_str}\n\n")
        
        # Results
        safe_ok = korean_chars_safe == korean_chars_original
        emoji_ok = korean_chars_emoji == korean_chars_original  
        safe_str_ok = korean_chars_safe_str == korean_chars_original
        
        f.write("RESULTS:\n")
        f.write(f"safe_print preserves Korean: {'YES' if safe_ok else 'NO'}\n")
        f.write(f"remove_emojis preserves Korean: {'YES' if emoji_ok else 'NO'}\n")
        f.write(f"safe_print_str preserves Korean: {'YES' if safe_str_ok else 'NO'}\n")
        
        all_ok = safe_ok and emoji_ok and safe_str_ok
        f.write(f"\nOVERALL: {'SUCCESS - All functions preserve Korean' if all_ok else 'FAILURE - Some functions corrupt Korean'}\n")
    
    return korean_chars_original, korean_chars_safe, korean_chars_emoji, korean_chars_safe_str

if __name__ == "__main__":
    try:
        results = test_korean_preservation()
        print("Test completed - check korean_test_results.txt")
        # Simple safe output
        original, safe, emoji, safe_str = results
        print(f"Korean chars: orig={original}, safe={safe}, emoji={emoji}, safe_str={safe_str}")
        if original == safe == emoji == safe_str:
            print("SUCCESS: All functions preserve Korean characters!")
        else:
            print("ISSUE: Some functions may corrupt Korean characters")
    except Exception as e:
        print(f"Error: {e}")