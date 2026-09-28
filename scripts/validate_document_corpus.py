"""Perform semantic and provenance validation for the synthetic PDF corpus."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = ROOT / "data" / "documents"

EXPECTED_PAGE_TEXT = {
    ("Candidate_A_Datasheet_Rev2.pdf", 2): ("Bore diameter | 25 mm",),
    ("Candidate_A_Datasheet_Rev2.pdf", 3): ("Basic dynamic load rating | 16 kN",),
    ("Candidate_A_Datasheet_Rev2.pdf", 4): (
        "No application-specific lubricant temperature qualification",
        "REQ-LUBE-TEMP-001 therefore requires evidence or qualification testing",
    ),
    ("Candidate_B_Datasheet.pdf", 2): ("Bore diameter | 30 mm",),
    ("Candidate_B_Datasheet.pdf", 3): ("Basic dynamic load rating | 18 kN",),
    ("Candidate_B_Datasheet.pdf", 4): (
        "Continuous operating range: -20 C to 120 C",
        "suitable for the Assembly A lubricant temperature requirement",
    ),
    ("Engineering_Drawing_Assembly_A.pdf", 2): (
        "REQ-BORE-001 | Bore diameter = 25 mm | HARD",
    ),
    ("Bearing_Application_Requirements.pdf", 2): (
        "REQ-LOAD-001 | Dynamic load | >= 14 kN",
        "REQ-LUBE-TEMP-001 | Lubricant temperature suitability",
    ),
    ("Qualification_SOP_Temperature.pdf", 2): (
        "Run for 16 working hours of laboratory time",
    ),
    ("Existing_Deviation.pdf", 1): (
        "Valid until: 2026-09-25",
        "EXPIRED",
    ),
    ("Quality_Release_Procedure.pdf", 3): (
        "Qualification task approval is not production release",
        "Bind approval to case version and case hash",
    ),
}


def normalized(text: str) -> str:
    return " ".join(text.split())


def main() -> None:
    manifest = json.loads((DOCUMENT_DIR / "manifest.json").read_text(encoding="utf-8"))
    documents = manifest["documents"]
    if len(documents) != 12:
        raise AssertionError(f"Expected 12 documents, found {len(documents)}")

    total_pages = 0
    extracted: dict[tuple[str, int], str] = {}
    for item in documents:
        path = DOCUMENT_DIR / item["filename"]
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != item["sha256"]:
            raise AssertionError(f"Checksum mismatch: {path.name}")

        reader = PdfReader(path)
        if len(reader.pages) != item["page_count"]:
            raise AssertionError(f"Page-count mismatch: {path.name}")
        total_pages += len(reader.pages)

        for page_number, pdf_page in enumerate(reader.pages, start=1):
            text = normalized(pdf_page.extract_text() or "")
            if not text:
                raise AssertionError(f"Empty extracted text: {path.name} page {page_number}")
            for marker in (
                item["document_id"],
                f"Revision {item['revision']}",
                "Synthetic hackathon fixture",
                f"Page {page_number} of {len(reader.pages)}",
            ):
                if normalized(marker) not in text:
                    raise AssertionError(
                        f"Missing provenance marker {marker!r}: {path.name} page {page_number}"
                    )
            extracted[(path.name, page_number)] = text

    for location, required_fragments in EXPECTED_PAGE_TEXT.items():
        page_text = extracted[location]
        for fragment in required_fragments:
            if normalized(fragment) not in page_text:
                raise AssertionError(f"Missing evidence {fragment!r} at {location}")

    print(f"Validated {len(documents)} PDFs, {total_pages} pages, and stable evidence provenance")


if __name__ == "__main__":
    main()
