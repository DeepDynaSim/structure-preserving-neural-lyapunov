from __future__ import annotations

import json
import os
import re
import zipfile
from pathlib import Path

from pypdf import PdfReader


docx_path = Path("output/docx/Structure_Preserving_Neural_Lyapunov_Certificates.docx")
pdf_path = Path("output/pdf/Structure_Preserving_Neural_Lyapunov_Certificates.pdf")

with zipfile.ZipFile(docx_path) as archive:
    document_xml = archive.read("word/document.xml").decode("utf-8")
    relationships_xml = archive.read("word/_rels/document.xml.rels").decode("utf-8")

reader = PdfReader(pdf_path)
pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)

checks = {
    "docx_bytes": os.path.getsize(docx_path),
    "pdf_bytes": os.path.getsize(pdf_path),
    "pdf_pages": len(reader.pages),
    "native_math_objects": document_xml.count("<m:oMath>"),
    "inline_images": document_xml.count("<a:blip "),
    "tables": document_xml.count("<w:tbl>"),
    "external_links": relationships_xml.count('TargetMode="External"'),
    "reference_entries": len(re.findall(r"^\[\d+\]", pdf_text, re.MULTILINE)),
    "has_232761_validation_count": "232,761" in pdf_text,
    "has_190952_source_violation": "19.0952%" in pdf_text,
    "has_07978_robust_bound": "0.7978" in pdf_text,
    "has_32_state_result": "32-state" in pdf_text,
    "placeholder_terms": re.findall(
        r"\b(?:TODO|TBD|PLACEHOLDER|Lorem ipsum)\b", pdf_text, re.IGNORECASE
    ),
}

print(json.dumps(checks, indent=2, ensure_ascii=False))

assert checks["pdf_pages"] == 19
assert checks["native_math_objects"] == 15
assert checks["inline_images"] == 7
assert checks["tables"] == 5
assert checks["reference_entries"] == 30
assert checks["external_links"] == 30
assert not checks["placeholder_terms"]
assert all(value for key, value in checks.items() if key.startswith("has_"))

