"""Generate the deterministic synthetic PDF evidence corpus.

The generated PDFs are committed fixtures for the canonical Material Continuity
demo. ReportLab is intentionally a build-time utility only; the application
runtime remains dependency-free.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "documents"
PAGE_WIDTH, PAGE_HEIGHT = A4

NAVY = HexColor("#102A43")
TEAL = HexColor("#007F7B")
PALE_TEAL = HexColor("#E8F4F3")
PALE_BLUE = HexColor("#EEF4FA")
INK = HexColor("#243B53")
MUTED = HexColor("#627D98")
LINE = HexColor("#BCCCDC")
WHITE = HexColor("#FFFFFF")
AMBER = HexColor("#D9822B")


@dataclass(frozen=True)
class Page:
    title: str
    subtitle: str
    sections: tuple[tuple[str, tuple[str, ...]], ...]
    notice: str | None = None


@dataclass(frozen=True)
class Document:
    filename: str
    document_id: str
    title: str
    revision: str
    effective_date: str
    owner: str
    pages: tuple[Page, ...]


def page(
    title: str,
    subtitle: str,
    *sections: tuple[str, Iterable[str]],
    notice: str | None = None,
) -> Page:
    return Page(
        title=title,
        subtitle=subtitle,
        sections=tuple((heading, tuple(items)) for heading, items in sections),
        notice=notice,
    )


DOCUMENTS = (
    Document(
        "Candidate_A_Datasheet_Rev2.pdf",
        "DS-CAND-A",
        "Candidate A Precision Bearing Datasheet",
        "2",
        "2026-09-15",
        "Supplier Alpha Engineering",
        (
            page(
                "Product identity and scope",
                "Model A25-6205 - single-row deep-groove bearing",
                ("Identification", ("Candidate ID: CAND-A", "Supplier part: A25-6205-R2", "Bearing family: 6205 equivalent", "Nominal bore class: 25 mm")),
                ("Document scope", ("Supplier catalog characteristics for the stated part and revision.", "Values are product-level specifications unless an application is named.", "Plant-A qualification and production release are outside this datasheet.")),
                notice="Synthetic supplier fixture. Availability does not imply production release.",
            ),
            page(
                "Dimensions",
                "Controlled dimensions for Candidate A",
                ("Dimensions table", ("Bore diameter | 25 mm | tolerance 0 / -0.010 mm", "Outside diameter | 52 mm | tolerance 0 / -0.013 mm", "Width | 15 mm | tolerance 0 / -0.120 mm", "Corner radius | 1.0 mm maximum")),
                ("Application reference", ("Seat family: BEARING-SEAT-25MM", "Measurement condition: 20 C", "Drawing compatibility still requires application review.")),
            ),
            page(
                "Load ratings",
                "Catalog ratings under supplier reference conditions",
                ("Load ratings table", ("Basic dynamic load rating | 16 kN", "Basic static load rating | 7.8 kN", "Reference speed | 12,000 rpm", "Limiting speed | 15,000 rpm")),
                ("Rating basis", ("Ratings follow the supplier's catalog calculation basis.", "Application factors and duty-cycle suitability require Engineering review.")),
            ),
            page(
                "Lubrication and evidence limitations",
                "General product information - not application qualification",
                ("Supplied condition", ("Factory grease: Supplier Alpha G-42", "Shield configuration: dual shield", "Storage range: -20 C to 50 C")),
                ("Explicit evidence limitation", ("No application-specific lubricant temperature qualification is provided for HIGH-TEMP-LUBRICATION.", "No test result demonstrates suitability at the Assembly A operating temperature.", "REQ-LUBE-TEMP-001 therefore requires evidence or qualification testing.")),
                notice="Missing application evidence must remain UNKNOWN. Do not infer compatibility from storage range.",
            ),
        ),
    ),
    Document(
        "Candidate_A_Certificate.pdf",
        "COC-CAND-A-0926",
        "Candidate A Certificate of Conformance",
        "1",
        "2026-09-18",
        "Supplier Alpha Quality",
        (
            page(
                "Certificate summary",
                "Lot-level conformance statement for Candidate A",
                ("Lot identification", ("Candidate ID: CAND-A", "Supplier part: A25-6205-R2", "Lot: ALPHA-260918-A", "Quantity: 500 EA")),
                ("Conformance statement", ("The lot was inspected against Supplier Alpha drawing A25-6205 revision 2.", "Dimensional and workmanship checks passed supplier release criteria.", "This certificate is not a Plant-A qualification release.")),
                notice="Synthetic certificate fixture. Independent application requirements still apply.",
            ),
            page(
                "Inspection results and exclusions",
                "Recorded lot checks",
                ("Inspection summary", ("Bore sample | 25.000 to 25.008 mm | PASS", "Outside diameter sample | 52.000 to 52.009 mm | PASS", "Visual workmanship | no defects observed | PASS", "Certificate disposition | supplier released")),
                ("Exclusions", ("Lubricant suitability at Assembly A operating temperature was not tested.", "Plant-A Engineering approval was not performed.", "Plant-A Quality release was not performed.")),
            ),
        ),
    ),
    Document(
        "Candidate_B_Datasheet.pdf",
        "DS-CAND-B",
        "Candidate B Precision Bearing Datasheet",
        "1",
        "2026-09-12",
        "Supplier Beta Engineering",
        (
            page(
                "Product identity and scope",
                "Model B30-6206 - single-row deep-groove bearing",
                ("Identification", ("Candidate ID: CAND-B", "Supplier part: B30-6206", "Bearing family: 6206", "Nominal bore class: 30 mm")),
                ("Document scope", ("Catalog data for the identified product revision.", "Application fit and plant release require separate review.")),
                notice="Synthetic supplier fixture. Technical evidence does not grant release.",
            ),
            page(
                "Dimensions",
                "Controlled dimensions for Candidate B",
                ("Dimensions table", ("Bore diameter | 30 mm | tolerance 0 / -0.010 mm", "Outside diameter | 62 mm | tolerance 0 / -0.013 mm", "Width | 16 mm | tolerance 0 / -0.120 mm", "Corner radius | 1.0 mm maximum")),
                ("Fit warning", ("Assembly A requires a 25 mm bearing seat.", "This 30 mm bore cannot be installed on BEARING-SEAT-25MM without redesign.")),
                notice="The bore difference is a hard dimensional mismatch for Assembly A.",
            ),
            page(
                "Load ratings",
                "Catalog ratings under supplier reference conditions",
                ("Load ratings table", ("Basic dynamic load rating | 18 kN", "Basic static load rating | 9.5 kN", "Reference speed | 11,000 rpm", "Limiting speed | 14,000 rpm")),
                ("Rating basis", ("Dynamic load exceeds the 14 kN minimum in REQ-LOAD-001.", "Passing one requirement does not override a hard dimensional mismatch.")),
            ),
            page(
                "Lubrication operating range",
                "Application note for high-temperature grease package",
                ("Qualified configuration", ("Grease package: Beta HT-120", "Continuous operating range: -20 C to 120 C", "Application class: HIGH-TEMP-LUBRICATION", "Supplier test reference: BETA-LUBE-HT-441")),
                ("Applicability", ("The stated configuration is suitable for the Assembly A lubricant temperature requirement.", "Plant-A qualification release remains a separate gate.")),
            ),
        ),
    ),
    Document(
        "Candidate_C_Datasheet.pdf",
        "DS-CAND-C",
        "Candidate C Bearing Preliminary Datasheet",
        "1",
        "2026-08-01",
        "Supplier Gamma Engineering",
        (
            page(
                "Product identity and status",
                "Model C25-6205 - preliminary supplier data",
                ("Identification", ("Candidate ID: CAND-C", "Supplier part: C25-6205", "Nominal bore class: 25 mm", "Data status: preliminary")),
                ("Control status", ("Not listed as an approved Plant-A production source.", "A prior temporary deviation is documented separately.")),
            ),
            page(
                "Dimensions and load",
                "Preliminary catalog characteristics",
                ("Characteristics", ("Bore diameter | 25 mm", "Outside diameter | 52 mm", "Width | 15 mm", "Basic dynamic load rating | 15 kN")),
                ("Limitations", ("Final tolerance report is not included.", "Lot-specific certificate is not included.")),
            ),
            page(
                "Evidence gaps",
                "Items requiring current evidence before qualification",
                ("Missing evidence", ("No application-specific lubricant temperature result.", "No current Plant-A qualification release.", "No current deviation applicable after 2026-09-25.")),
                ("Disposition", ("Candidate remains unqualified.", "Prior acceptance must not be treated as a current release.")),
                notice="Expired deviations are not valid recovery authorization.",
            ),
        ),
    ),
    Document(
        "Engineering_Drawing_Assembly_A.pdf",
        "DWG-ASSY-A",
        "Assembly A Bearing Interface Drawing",
        "A",
        "2026-07-14",
        "Plant-A Mechanical Engineering",
        (
            page(
                "Assembly definition",
                "Bearing station A-01",
                ("Drawing references", ("Assembly: ASSEMBLY-A", "Material: MAT-BRG-001", "Interface: BEARING-SEAT-25MM", "Units: millimeters unless stated")),
                ("Control note", ("Use only the current drawing revision for fit decisions.", "Supplier catalog dimensions do not replace this interface definition.")),
            ),
            page(
                "Bearing seat dimensions",
                "Hard dimensional interface requirements",
                ("Interface dimensions", ("Required bearing bore | 25.000 mm nominal", "Shaft seat | 25.000 mm nominal", "Maximum bearing width | 15.2 mm", "Maximum outside diameter | 52.1 mm")),
                ("Requirement mapping", ("REQ-BORE-001 | Bore diameter = 25 mm | HARD", "A bore other than 25 mm is a fit mismatch.")),
                notice="Dimensional mismatch requires rejection, not qualification by inference.",
            ),
            page(
                "Engineering notes",
                "Application controls",
                ("Notes", ("Bearing supports continuous assembly duty.", "Dynamic load and lubricant suitability are controlled by the application requirements document.", "Any alternative part requires evidence review and Plant-A Quality release.")),
                ("Related documents", ("Bearing_Application_Requirements.pdf revision 1", "Quality_Release_Procedure.pdf revision 3")),
            ),
        ),
    ),
    Document(
        "Engineering_Drawing_Assembly_B.pdf",
        "DWG-ASSY-B",
        "Assembly B Bearing Interface Drawing",
        "A",
        "2026-07-14",
        "Plant-A Mechanical Engineering",
        (
            page(
                "Assembly definition",
                "Bearing station B-01",
                ("Drawing references", ("Assembly: ASSEMBLY-B", "Material: MAT-BRG-001", "Interface: BEARING-SEAT-25MM", "Units: millimeters unless stated")),
                ("Control note", ("This assembly consumes the same purchased bearing family as Assembly A.", "Use the current drawing revision for fit decisions.")),
            ),
            page(
                "Bearing seat dimensions",
                "Hard dimensional interface requirements",
                ("Interface dimensions", ("Required bearing bore | 25.000 mm nominal", "Shaft seat | 25.000 mm nominal", "Maximum bearing width | 15.2 mm", "Maximum outside diameter | 52.1 mm")),
                ("Fit control", ("A 30 mm bore bearing does not fit this interface.", "Machining changes are outside the recovery-case scope.")),
            ),
            page(
                "Engineering notes",
                "Shared material controls",
                ("Notes", ("MAT-BRG-001 is purchased directly into the assembly BOM.", "Alternative parts require requirement-level evidence.", "Production use requires a current Plant-A release.")),
                ("Related documents", ("Bearing_Application_Requirements.pdf revision 1", "Quality_Release_Procedure.pdf revision 3")),
            ),
        ),
    ),
    Document(
        "Bearing_Application_Requirements.pdf",
        "REQ-BRG-APP",
        "Bearing Application Requirements",
        "1",
        "2026-07-20",
        "Plant-A Product Engineering",
        (
            page(
                "Requirement set scope",
                "Application requirements for MAT-BRG-001 alternatives",
                ("Scope", ("Product: ASSEMBLY-A", "Material: MAT-BRG-001", "Review level: requirement-by-requirement", "Evidence must identify source, revision, and page.")),
                ("Decision semantics", ("MATCH requires applicable evidence.", "MISMATCH rejects a hard requirement.", "Missing or insufficient evidence remains UNKNOWN.")),
            ),
            page(
                "Technical requirements",
                "Controlled requirements for substitute review",
                ("Requirement register", ("REQ-BORE-001 | Bore diameter | = 25 mm | HARD | BEARING-SEAT-25MM", "REQ-LOAD-001 | Dynamic load | >= 14 kN | HARD | BEARING-SEAT-25MM", "REQ-LUBE-TEMP-001 | Lubricant temperature suitability | = SUITABLE | CRITICAL | HIGH-TEMP-LUBRICATION")),
                ("Evidence rule", ("Catalog claims are acceptable only when applicable to the exact candidate revision.", "Generic storage-temperature data does not satisfy lubricant operating suitability.")),
            ),
            page(
                "Release requirement",
                "Production use remains a separate controlled decision",
                ("Release gate", ("REQ-RELEASE-001 | Plant qualification release | = true | CRITICAL | PLANT-A", "Engineering evidence review is necessary but not sufficient.", "Qualification task approval does not authorize production use.")),
                ("Related procedure", ("Quality_Release_Procedure.pdf revision 3", "Current QMS candidate status record")),
                notice="Humans retain Engineering and Quality release authority.",
            ),
        ),
    ),
    Document(
        "Qualification_SOP_Temperature.pdf",
        "SOP-QUAL-TEMP",
        "Lubricant Temperature Qualification SOP",
        "2",
        "2026-08-10",
        "Plant-A Qualification Laboratory",
        (
            page(
                "Purpose and authorization",
                "Procedure QUAL-TEMP-001",
                ("Purpose", ("Generate application-specific evidence for REQ-LUBE-TEMP-001.", "Applies to unqualified bearing candidates proposed for Assembly A.")),
                ("Authority boundary", ("Scheduling or approving this test does not release material for production.", "Only authorized laboratory personnel may record execution results.")),
            ),
            page(
                "Test method",
                "Controlled temperature endurance cycle",
                ("Method", ("Install candidate in the representative test fixture.", "Operate at the Assembly A duty point.", "Run for 16 working hours of laboratory time.", "Record temperature, torque, noise, and lubricant condition.")),
                ("Resource", ("Required resource: LAB-TEMPERATURE", "Calendar: weekdays, 08:00 to 16:00 Asia/Jakarta", "Interrupted work resumes at the next available period.")),
            ),
            page(
                "Acceptance and evidence record",
                "Required output for Engineering review",
                ("Acceptance criteria", ("No lubricant breakdown or leakage.", "Measured temperature remains within the application limit.", "No abnormal torque or noise trend.")),
                ("Required record", ("Candidate ID and lot", "SOP revision", "Start and completion timestamps", "Measured results and reviewer signature", "Disposition: PASS, FAIL, or INCONCLUSIVE")),
                notice="An absent or incomplete result remains UNKNOWN.",
            ),
        ),
    ),
    Document(
        "Qualification_SOP_Load.pdf",
        "SOP-QUAL-LOAD",
        "Bearing Load Verification SOP",
        "1",
        "2026-08-10",
        "Plant-A Qualification Laboratory",
        (
            page(
                "Purpose and scope",
                "Procedure QUAL-LOAD-001",
                ("Purpose", ("Verify candidate load capability when catalog evidence is missing or disputed.", "Supports REQ-LOAD-001 for MAT-BRG-001 alternatives.")),
                ("Boundary", ("Use only when Engineering requests physical verification.", "A test result does not override a dimensional mismatch.")),
            ),
            page(
                "Test method",
                "Radial load endurance verification",
                ("Method", ("Confirm the candidate is dimensionally installable.", "Apply the defined radial load profile.", "Run for 8 working hours.", "Record vibration, noise, temperature, and damage indicators.")),
                ("Controls", ("Calibrate load cell before execution.", "Trace all samples to candidate and lot identifiers.")),
            ),
            page(
                "Acceptance and disposition",
                "Evidence requirements",
                ("Acceptance criteria", ("No race, cage, or rolling-element damage.", "No abnormal vibration increase.", "Measured capability supports at least 14 kN dynamic rating.")),
                ("Disposition", ("PASS supports the load requirement only.", "FAIL is evidence of mismatch.", "INCONCLUSIVE remains UNKNOWN and requires review.")),
            ),
        ),
    ),
    Document(
        "Approved_Supplier_List.pdf",
        "ASL-BRG-001",
        "Approved Supplier List - Bearing Family",
        "5",
        "2026-09-01",
        "Plant-A Supplier Quality",
        (
            page(
                "Approved production sources",
                "Status as of the effective date",
                ("Approved sources", ("SUP-ORIGINAL | MAT-BRG-001 original part | APPROVED", "SUP-EQUIVALENT | Approved equivalent EQ-001 | APPROVED - no inventory", "Plant B transfer | Original part | APPROVED network source")),
                ("Timing note", ("Approved status does not guarantee availability by the shortage date.", "Supply timing must be evaluated separately.")),
            ),
            page(
                "Unqualified candidates",
                "Sources not approved for Plant-A production use",
                ("Candidate status", ("Supplier Alpha / CAND-A | NOT APPROVED - qualification required", "Supplier Beta / CAND-B | NOT APPROVED - qualification required", "Supplier Gamma / CAND-C | NOT APPROVED - prior deviation expired")),
                ("Control rule", ("Supplier listing is not a substitute for part qualification.", "No candidate on this page is authorized for production use.")),
                notice="Check current QMS release status before any controlled action.",
            ),
        ),
    ),
    Document(
        "Existing_Deviation.pdf",
        "DEV-C-001",
        "Temporary Material Deviation - Candidate C",
        "1",
        "2026-08-01",
        "Plant-A Quality",
        (
            page(
                "Deviation authorization",
                "Temporary and scope-limited disposition",
                ("Scope", ("Candidate: CAND-C", "Material: MAT-BRG-001", "Plant: PLANT-A", "Authorized quantity: maximum 300 EA", "Authorized assemblies: ASSEMBLY-A and ASSEMBLY-B")),
                ("Validity", ("Valid from: 2026-08-01", "Valid until: 2026-09-25", "Status after validity end: EXPIRED")),
                notice="This deviation is expired before the 2026-10-04 shortage date.",
            ),
            page(
                "Conditions and closure",
                "Controls attached to DEV-C-001",
                ("Conditions", ("Lot certificate required before receipt.", "Incoming dimensional inspection required.", "Use beyond 300 EA is prohibited.", "Extension requires a new signed deviation.")),
                ("Closure", ("No extension was issued.", "The record remains auditable but cannot authorize a current recovery action.", "Candidate C returns to unqualified status after 2026-09-25.")),
            ),
        ),
    ),
    Document(
        "Quality_Release_Procedure.pdf",
        "PROC-QA-RELEASE",
        "Plant-A Alternative Material Release Procedure",
        "3",
        "2026-09-05",
        "Plant-A Quality Systems",
        (
            page(
                "Purpose and roles",
                "Controlled release workflow for alternative materials",
                ("Purpose", ("Define evidence, review, and authorization required before production use.", "Applies to unqualified candidates and temporary deviations.")),
                ("Roles", ("Engineering reviews technical evidence.", "Quality reviews qualification and release controls.", "Production may consume material only after current release is recorded.")),
            ),
            page(
                "Release prerequisites",
                "All gates must be satisfied",
                ("Required gates", ("Current candidate identity and source revision verified.", "All hard requirements are MATCH.", "Critical requirements are MATCH or covered by a current authorized disposition.", "Qualification tasks are complete with accepted results.", "Engineering and Quality approvals reference the current case version.")),
                ("Fail-closed rules", ("UNKNOWN is not MATCH.", "Expired deviations are invalid.", "Stale case or evidence versions invalidate authorization.")),
            ),
            page(
                "Action boundary and records",
                "Qualification task approval is not production release",
                ("Action boundary", ("A reviewer may authorize creation of a qualification task.", "That authorization permits the task only.", "Production release remains blocked until Quality records a separate release decision.")),
                ("Audit record", ("Record approver identity and role.", "Bind approval to case version and case hash.", "Enforce approval expiry and idempotency.", "Store an action receipt for controlled writes.")),
                notice="Human Quality authority is required for final production release.",
            ),
        ),
    ),
)


def wrap_text(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = "Helvetica",
    size: float = 9.5,
    leading: float = 13,
    color=INK,
) -> float:
    pdf.setFont(font, size)
    pdf.setFillColor(color)
    for line in wrap_text(text, font, size, width):
        pdf.drawString(x, y, line)
        y -= leading
    return y


def draw_page(pdf: canvas.Canvas, document: Document, content: Page, page_number: int) -> None:
    margin = 48
    pdf.setFillColor(NAVY)
    pdf.rect(0, PAGE_HEIGHT - 78, PAGE_WIDTH, 78, stroke=0, fill=1)
    pdf.setFillColor(TEAL)
    pdf.rect(0, PAGE_HEIGHT - 84, PAGE_WIDTH, 6, stroke=0, fill=1)

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(margin, PAGE_HEIGHT - 26, "MATERIAL CONTINUITY | SYNTHETIC EVIDENCE")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, PAGE_HEIGHT - 55, content.title)

    y = PAGE_HEIGHT - 112
    y = draw_wrapped(pdf, content.subtitle, margin, y, PAGE_WIDTH - 2 * margin, font="Helvetica-Bold", size=11, leading=15, color=TEAL)
    y -= 10

    meta = (
        ("Document ID", document.document_id),
        ("Revision", document.revision),
        ("Effective date", document.effective_date),
        ("Owner", document.owner),
        ("Classification", "Synthetic hackathon fixture"),
    )
    box_height = 78
    pdf.setFillColor(PALE_BLUE)
    pdf.roundRect(margin, y - box_height, PAGE_WIDTH - 2 * margin, box_height, 5, stroke=0, fill=1)
    col_width = (PAGE_WIDTH - 2 * margin - 24) / 2
    meta_y = y - 17
    for index, (label, value) in enumerate(meta):
        column = index % 2
        row = index // 2
        x = margin + 12 + column * col_width
        row_y = meta_y - row * 22
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.setFillColor(MUTED)
        pdf.drawString(x, row_y, label.upper())
        pdf.setFont("Helvetica", 9)
        pdf.setFillColor(INK)
        pdf.drawString(x, row_y - 10, value)
    y -= box_height + 20

    for section_index, (heading, items) in enumerate(content.sections):
        pdf.setFillColor(TEAL if section_index == 0 else NAVY)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(margin, y, heading)
        y -= 8
        pdf.setStrokeColor(LINE)
        pdf.setLineWidth(0.6)
        pdf.line(margin, y, PAGE_WIDTH - margin, y)
        y -= 16
        for item_index, item in enumerate(items):
            row_lines = wrap_text(item, "Helvetica", 9.2, PAGE_WIDTH - 2 * margin - 32)
            row_height = max(25, 10 + 12 * len(row_lines))
            pdf.setFillColor(PALE_TEAL if item_index % 2 == 0 else WHITE)
            pdf.roundRect(margin, y - row_height + 5, PAGE_WIDTH - 2 * margin, row_height, 3, stroke=0, fill=1)
            pdf.setFillColor(TEAL)
            pdf.circle(margin + 12, y - 5, 2.4, stroke=0, fill=1)
            text_y = y
            for line in row_lines:
                pdf.setFillColor(INK)
                pdf.setFont("Helvetica", 9.2)
                pdf.drawString(margin + 24, text_y, line)
                text_y -= 12
            y -= row_height + 3
        y -= 13

    if content.notice:
        notice_lines = wrap_text(content.notice, "Helvetica-Bold", 8.5, PAGE_WIDTH - 2 * margin - 28)
        notice_height = 18 + 11 * len(notice_lines)
        notice_y = 57 + notice_height
        pdf.setFillColor(HexColor("#FFF4E5"))
        pdf.roundRect(margin, 57, PAGE_WIDTH - 2 * margin, notice_height, 4, stroke=0, fill=1)
        pdf.setFillColor(AMBER)
        pdf.rect(margin, 57, 5, notice_height, stroke=0, fill=1)
        pdf.setFillColor(INK)
        pdf.setFont("Helvetica-Bold", 8.5)
        for line in notice_lines:
            notice_y -= 11
            pdf.drawString(margin + 14, notice_y, line)

    pdf.setStrokeColor(LINE)
    pdf.line(margin, 42, PAGE_WIDTH - margin, 42)
    pdf.setFont("Helvetica", 7.5)
    pdf.setFillColor(MUTED)
    pdf.drawString(margin, 28, f"{document.document_id} | Revision {document.revision}")
    page_label = f"Page {page_number} of {len(document.pages)}"
    pdf.drawRightString(PAGE_WIDTH - margin, 28, page_label)


def build_document(document: Document) -> Path:
    output_path = OUTPUT_DIR / document.filename
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1, invariant=1)
    pdf.setTitle(document.title)
    pdf.setAuthor(document.owner)
    pdf.setSubject("Material Continuity synthetic evidence fixture")
    pdf.setKeywords(f"synthetic,evidence,{document.document_id},revision-{document.revision}")
    for page_number, content in enumerate(document.pages, start=1):
        draw_page(pdf, document, content, page_number)
        pdf.showPage()
    pdf.save()
    return output_path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    expected_names = {document.filename for document in DOCUMENTS}
    for stale_pdf in OUTPUT_DIR.glob("*.pdf"):
        if stale_pdf.name not in expected_names:
            raise RuntimeError(f"Unexpected PDF already exists: {stale_pdf.name}")

    generated = [build_document(document) for document in DOCUMENTS]
    manifest = {
        "schema_version": 1,
        "corpus_id": "material-continuity-synthetic-v1",
        "classification": "Synthetic hackathon fixture",
        "documents": [
            {
                "filename": document.filename,
                "document_id": document.document_id,
                "title": document.title,
                "revision": document.revision,
                "effective_date": document.effective_date,
                "owner": document.owner,
                "page_count": len(document.pages),
                "sha256": sha256(path),
            }
            for document, path in zip(DOCUMENTS, generated, strict=True)
        ],
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(generated)} PDFs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
