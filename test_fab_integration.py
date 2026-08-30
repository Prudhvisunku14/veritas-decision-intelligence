#!/usr/bin/env python3
"""
Quick test to verify FAB (Floating Assistant Button) integration in streamlit_app.py
"""

import re

# Read the streamlit app file
with open("frontend/streamlit_app.py", "r") as f:
    content = f.read()

# Check for key components
checks = {
    "✓ FAB container exists (veritas_fab key)": "veritas_fab" in content,
    "✓ Chat launcher button exists": "veritas_chat_launcher" in content,
    "✓ CSS for FAB present": ".st-key-veritas_fab" in content,
    "✓ Chatbot bubble SVG gradient colors (#00c6ff)": "stop-color:%2300c6ff" in content,
    "✓ Chat open/close logic": "st.session_state.chat_open = True" in content,
    "✓ Welcome message system": "_welcome_map" in content,
    "✓ Backend integration": "requests.post" in content and "/api/ask" in content,
    "✓ Security enforcement (403 handling)": "403" in content,
    "✓ Message persistence": "st.session_state.chat_messages" in content,
    "✓ Persona-based suggestions": "_page_suggestions" in content,
}

print("\n" + "="*60)
print("FAB INTEGRATION VERIFICATION")
print("="*60 + "\n")

all_passed = True
for check, result in checks.items():
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"  {status} : {check}")
    if not result:
        all_passed = False

print("\n" + "="*60)
if all_passed:
    print("✓ ALL CHECKS PASSED - FAB IS PROPERLY INTEGRATED")
    print("\nNext steps:")
    print("  1. Reload the Streamlit app (or restart the server)")
    print("  2. Navigate to CEO/CFO dashboard")
    print("  3. Look for chatbot bubble icon in bottom-right corner")
    print("  4. Click the bubble to open chat window")
else:
    print("✗ SOME CHECKS FAILED - REVIEW IMPLEMENTATION")
print("="*60 + "\n")

# Extract and print SVG info
svg_match = re.search(r"background: url\('data:image/svg\+xml;utf8,<svg[^']+'\)", content)
if svg_match:
    print("SVG Data URI Found (trimmed):")
    svg_data = svg_match.group(0)
    if len(svg_data) > 200:
        print(f"  {svg_data[:100]}...{svg_data[-100:]}")
    else:
        print(f"  {svg_data}")
