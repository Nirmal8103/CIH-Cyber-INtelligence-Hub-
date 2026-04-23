# tests/test_ner.py
from src.processor.ner import extract_entities

def test_ner():
    test_cases = [
        ("Microsoft and Google reported a new critical vulnerability CVE-2024-1234 affecting their cloud services.", 
         ["Microsoft", "Google", "CVE-2024-1234"]),
        ("Ransomware gang LockBit targets US schools demanding Bitcoin payments.", 
         ["LockBit"]),
        ("A patch was released for CVE-2023-99999 in the Linux kernel.", 
         ["CVE-2023-99999", "Linux"])
    ]
    
    for text, expected in test_cases:
        extracted = extract_entities(text)
        print(f"Text: {text}")
        print(f"Extracted: {extracted}")
        for exp in expected:
            if exp.upper() in extracted.upper():
                print(f"  [PASS] Found {exp}")
            else:
                print(f"  [FAIL] Missing {exp}")
        print("-" * 20)

if __name__ == "__main__":
    test_ner()
