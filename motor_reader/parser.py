import re

FIELDS = [
    "Manufacturer", "Model", "Serial", "Phase", "Voltage", "Current",
    "Power", "Speed", "Frequency", "Power Factor", "Efficiency",
    "IP Rating", "Insulation", "Mounting", "Duty", "Frame", "Standard"
]

def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.strip(" |:;") for line in text.splitlines() if line.strip())

def _first(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return m.group(1).strip(" .,:;")
    return ""

def parse_nameplate(raw_text):
    text = clean_text(raw_text)
    flat = re.sub(r"\s+", " ", text)
    result = {field: "" for field in FIELDS}
    result["Manufacturer"] = _first([
        r"\b(?:manufacturer|make|brand)\s*[:\-]?\s*([A-Z][A-Z0-9 &.-]{1,35})",
    ], flat)
    result["Model"] = _first([
        r"\b(?:model|type|motor type)\s*[:\-]?\s*([A-Z0-9][A-Z0-9./_-]{2,30})",
        r"\bTYPE\s+([A-Z0-9][A-Z0-9./_-]{2,30})",
    ], flat)
    result["Serial"] = _first([
        r"\b(?:serial(?:\s*(?:no|number))?|s/?n)\s*[:#\-]?\s*([A-Z0-9./_-]{3,30})",
    ], flat)
    result["Phase"] = _first([
        r"\b(3|three)\s*[- ]?\s*phase\b", r"\b(1|single)\s*[- ]?\s*phase\b",
        r"\bPH\s*[:\-]?\s*([13])\b"
    ], flat)
    if result["Phase"] in ("3", "three"): result["Phase"] = "3"
    if result["Phase"] in ("1", "single"): result["Phase"] = "1"
    result["Voltage"] = _first([
        r"\b(?:voltage|volts?|v)\s*[:=]?\s*((?:\d{2,4}\s*[/\-]\s*)?\d{2,4}\s*V?)\b",
        r"\b(\d{2,4}\s*/\s*\d{2,4}\s*V)\b"
    ], flat)
    result["Current"] = _first([
        r"\b(?:current|amps?|a)\s*[:=]?\s*(\d+(?:\.\d+)?\s*(?:/\s*\d+(?:\.\d+)?)?\s*A?)\b"
    ], flat)
    result["Power"] = _first([
        r"\b(?:power|output|kw|hp)\s*[:=]?\s*(\d+(?:\.\d+)?\s*(?:kW|KW|HP|hp|W)?)\b"
    ], flat)
    result["Speed"] = _first([
        r"\b(?:speed|rpm|r/min|min-1)\s*[:=]?\s*(\d{3,5}\s*(?:rpm|r/min)?)\b",
        r"\b(\d{3,5})\s*(?:rpm|r/min)\b"
    ], flat)
    result["Frequency"] = _first([r"\b(?:frequency|freq|hz)\s*[:=]?\s*(\d{2,3}(?:\.\d+)?\s*Hz?)\b"], flat)
    result["Power Factor"] = _first([r"\b(?:power factor|cos\s*phi|cosφ)\s*[:=]?\s*(0?\.\d{2,3})"], flat)
    result["Efficiency"] = _first([r"\b(?:eff(?:iciency)?|IE[1-5])\s*[:=]?\s*(IE[1-5]|\d{2,3}(?:\.\d+)?\s*%?)"], flat)
    result["IP Rating"] = _first([r"\b(IP\s*\d{2,3}[A-Z]?)\b"], flat).replace(" ", "")
    result["Insulation"] = _first([r"\b(?:insulation|ins\.?\s*class|class)\s*[:=]?\s*([A-H])\b"], flat)
    result["Mounting"] = _first([r"\b(?:mounting|mount)\s*[:=]?\s*((?:IM\s*)?[A-Z0-9-]{2,8})\b"], flat)
    result["Duty"] = _first([r"\b(?:duty)\s*[:=]?\s*(S[1-9])\b"], flat)
    result["Frame"] = _first([r"\b(?:frame)\s*[:=]?\s*(\d{2,4}[A-Z]?)\b"], flat)
    result["Standard"] = _first([r"\b(IEC\s*[\d.-]+)\b"], flat)
    return result

def confidence_summary(lines):
    if not lines:
        return 0.0
    return round(sum(x.confidence for x in lines) / len(lines) * 100, 1)
