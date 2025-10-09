#!/usr/bin/env python3
"""
Test all Korean text processing functions
"""

def test_korean_preservation():
    """Test that all our Unicode processing functions preserve Korean characters"""
    
    from packages.gen.content_generator import safe_print, remove_emojis, ContentGenerator
    
    test_korean = "인공지능 기술의 발전 🚀 과 한국의 미래 ✈️"
    expected_korean = "인공지능 기술의 발전  과 한국의 미래 "  # emojis removed but Korean preserved
    
    print("=== TESTING KOREAN PRESERVATION ===")
    print(f"Original: {repr(test_korean)}")
    print()
    
    # Test safe_print function
    safe_result = safe_print(test_korean)
    print(f"safe_print result: {repr(safe_result)}")
    
    # Test remove_emojis function
    emoji_result = remove_emojis(test_korean)
    print(f"remove_emojis result: {repr(emoji_result)}")
    
    # Test safe_print_str method
    generator = ContentGenerator()
    safe_str_result = generator.safe_print_str(test_korean)
    print(f"safe_print_str result: {repr(safe_str_result)}")
    
    print()
    
    # Count Korean characters in original
    korean_chars_original = sum(1 for c in test_korean if '\uAC00' <= c <= '\uD7AF')
    print(f"Korean chars in original: {korean_chars_original}")
    
    # Count Korean characters in results
    korean_chars_safe = sum(1 for c in safe_result if '\uAC00' <= c <= '\uD7AF')
    korean_chars_emoji = sum(1 for c in emoji_result if '\uAC00' <= c <= '\uD7AF')
    korean_chars_safe_str = sum(1 for c in safe_str_result if '\uAC00' <= c <= '\uD7AF')
    
    print(f"Korean chars in safe_print: {korean_chars_safe}")
    print(f"Korean chars in remove_emojis: {korean_chars_emoji}")
    print(f"Korean chars in safe_print_str: {korean_chars_safe_str}")
    
    print()
    
    # Check if Korean characters are preserved
    if korean_chars_safe == korean_chars_original:
        print("✓ safe_print preserves Korean characters")
    else:
        print("✗ safe_print corrupts Korean characters")
    
    if korean_chars_emoji == korean_chars_original:
        print("✓ remove_emojis preserves Korean characters")
    else:
        print("✗ remove_emojis corrupts Korean characters")
        
    if korean_chars_safe_str == korean_chars_original:
        print("✓ safe_print_str preserves Korean characters")
    else:
        print("✗ safe_print_str corrupts Korean characters")
    
    print()
    
    # Check emoji removal
    emoji_count_original = test_korean.count('🚀') + test_korean.count('✈️')
    emoji_count_result = emoji_result.count('🚀') + emoji_result.count('✈️')
    
    print(f"Emojis in original: {emoji_count_original}")
    print(f"Emojis in remove_emojis result: {emoji_count_result}")
    
    if emoji_count_result == 0:
        print("✓ remove_emojis successfully removes emojis")
    else:
        print("✗ remove_emojis fails to remove emojis")
    
    if korean_chars_emoji == korean_chars_original and emoji_count_result == 0:
        print("\n🎉 SUCCESS: All functions correctly preserve Korean while removing emojis!")
        return True
    else:
        print("\n❌ FAILURE: Functions still have issues")
        return False

if __name__ == "__main__":
    test_korean_preservation()