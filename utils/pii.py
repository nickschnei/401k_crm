import re
from typing import Tuple, List

# Regex to detect standard hyphenated SSN (XXX-XX-XXXX)
SSN_HYPHENATED_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Regex to detect plain 9-digit sequences (for routing numbers or plain SSNs)
NINE_DIGIT_PATTERN = re.compile(r"\b\d{9}\b")

def is_valid_aba_routing_number(routing: str) -> bool:
    """
    Validates a 9-digit ABA routing transit number using the standard checksum algorithm.
    Formula: 3*(d1 + d4 + d7) + 7*(d2 + d5 + d8) + (d3 + d6 + d9) mod 10 == 0
    """
    if len(routing) != 9 or not routing.isdigit():
        return False
    d = [int(char) for char in routing]
    checksum = (
        3 * (d[0] + d[3] + d[6]) +
        7 * (d[1] + d[4] + d[7]) +
        (d[2] + d[5] + d[8])
    )
    return checksum % 10 == 0

def screen_and_mask_pii(text: str) -> Tuple[str, List[str]]:
    """
    Screens incoming text for plain text Social Security Numbers (SSN) and bank routing numbers.
    Masks detected PII with placeholder tags.
    Returns:
        A tuple of (masked_text, list_of_detected_pii_types)
    """
    detected = []
    
    # 1. Mask hyphenated SSNs
    if SSN_HYPHENATED_PATTERN.search(text):
        text = SSN_HYPHENATED_PATTERN.sub("[MASKED SSN]", text)
        detected.append("Social Security Number")

    # 2. Extract potential 9-digit numbers for ABA routing checksum or plain SSN check
    potential_nine_digits = NINE_DIGIT_PATTERN.findall(text)
    for num in potential_nine_digits:
        if is_valid_aba_routing_number(num):
            text = text.replace(num, "[MASKED ROUTING NUMBER]")
            if "Routing Number" not in detected:
                detected.append("Routing Number")

    return text, detected
