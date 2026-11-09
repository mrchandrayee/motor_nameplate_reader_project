from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np

@dataclass
class OCRLine:
    text: str
    confidence: float
    box: list

class NameplateOCR:
    def __init__(self, device="cpu"):
        try:
            import easyocr
        except ImportError as exc:
            raise RuntimeError("EasyOCR missing. Run: pip install -r requirements.txt") from exc
        self.reader = easyocr.Reader(["en"], gpu=(device == "gpu"))

    @staticmethod
    def preprocess(image: np.ndarray) -> np.ndarray:
        if image is None or image.size == 0:
            raise ValueError("Empty image")
        h, w = image.shape[:2]
        if max(h, w) < 1400:
            scale = min(3.0, 1400 / max(h, w))
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        # Mild contrast enhancement; keep original-like edges for stamped/engraved plates.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    def read(self, image: np.ndarray) -> Tuple[List[OCRLine], np.ndarray]:
        prepared = self.preprocess(image)
        results = self.reader.readtext(prepared, detail=1, paragraph=False)
        lines = []
        for box, text, conf in results:
            lines.append(OCRLine(str(text).strip(), float(conf), np.asarray(box).astype(int).tolist()))
        return lines, prepared

def annotate(image: np.ndarray, lines: List[OCRLine]) -> np.ndarray:
    out = image.copy()
    for line in lines:
        pts = np.asarray(line.box, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(out, [pts], True, (0, 145, 255), 2)
        x, y = pts[0, 0]
        cv2.putText(out, f"{line.confidence:.0%}", (int(x), max(18, int(y)-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 145, 255), 1, cv2.LINE_AA)
    return out
