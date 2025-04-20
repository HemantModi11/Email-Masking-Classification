import re
import spacy

nlp = spacy.load("en_core_web_sm")

# Improved regex patterns
patterns = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone_number": r"\+?\d[\d\s().-]{7,}\d",
    "aadhar_num": r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b",
    "credit_debit_no": r"\b(?:\d[ -]*?){13,16}\b",
    "cvv_no": r"(?<!\d)(\d{3})(?!\d)",
    "expiry_no": r"\b(0[1-9]|1[0-2])\/([0-9]{2}|[0-9]{4})\b",
    "dob": r"\b\d{2}[/-]\d{2}[/-]\d{4}\b"
}



def apply_regex_patterns(text):
    entities = []

    for label, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            start, end = match.start(), match.end()
            entities.append({
                "position": [start, end],
                "classification": label,
                "entity": match.group()
            })

    return entities

def apply_spacy_ner(text):
    entities = []
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities.append({
                "position": [ent.start_char, ent.end_char],
                "classification": "full_name",
                "entity": ent.text
            })

    return entities

def merge_entities(regex_entities, spacy_entities):
    # Priority: Aadhaar > Email > Phone > CVV...
    priority = {
        "aadhar_num": 1,
        "email": 2,
        "full_name": 3,
        "phone_number": 4,
        "credit_debit_no": 5,
        "cvv_no": 6,
        "expiry_no": 7,
        "dob": 8
    }

    all_entities = regex_entities + spacy_entities

    # Sort: start index ASC, then priority ASC
    all_entities.sort(key=lambda e: (e["position"][0], priority.get(e["classification"], 99)))

    result = []
    occupied = set()

    for ent in all_entities:
        start, end = ent["position"]
        overlap = any(i in occupied for i in range(start, end))

        if not overlap:
            result.append(ent)
            occupied.update(range(start, end))

    return result

def mask_text(text, entities):
    masked_text = text
    offset = 0
    for ent in entities:
        start, end = ent["position"]
        label = ent["classification"]
        replacement = f"[{label}]"
        masked_text = (
            masked_text[:start + offset] + replacement + masked_text[end + offset:]
        )
        offset += len(replacement) - (end - start)
    return masked_text

def mask_pii(email_body: str):
    regex_entities = apply_regex_patterns(email_body)
    spacy_entities = apply_spacy_ner(email_body)
    combined_entities = merge_entities(regex_entities, spacy_entities)
    masked_email = mask_text(email_body, combined_entities)

    return {
        "input_email_body": email_body,
        "list_of_masked_entities": combined_entities,
        "masked_email": masked_email
    }