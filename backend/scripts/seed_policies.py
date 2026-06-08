"""
Insurance Claim Pre-Assurance – Policy PDF Seeder
Generates realistic sample policy PDFs for all insurer/policy-type combinations.
Used for local development and CI testing when real policy docs are unavailable.

Run from backend/:
    python scripts/seed_policies.py
"""
import sys
import textwrap
from pathlib import Path

# ── Make sure app imports work when run directly ──────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from reportlab.lib.pagesizes import A4          # type: ignore
    from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # type: ignore
    from reportlab.lib.units import cm              # type: ignore
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

import pdfplumber  # already in requirements; used to verify

# ── Policy content templates ──────────────────────────────────────────────────

POLICIES: list[dict] = [
    {
        "insurer": "hdfc_ergo",
        "policy_type": "health",
        "filename": "hdfc_ergo_health_policy.pdf",
        "title": "HDFC ERGO Health Suraksha – Policy Wordings",
        "content": textwrap.dedent("""\
            SECTION 1 – COVERAGE OVERVIEW
            This policy provides indemnity-based hospitalisation cover for the insured and
            eligible family members. The policy operates on a floater or individual sum insured
            basis as selected at the time of proposal.

            SECTION 2 – ROOM RENT SUB-LIMIT
            Room rent is limited to 1% of the Sum Insured per day for a single private room.
            ICU/ICCU charges are capped at 2% of the Sum Insured per day.
            If the insured opts for a room beyond the entitled category, all related charges
            (surgery, doctor fees, medicines) shall be proportionately reduced.

            SECTION 3 – WAITING PERIODS
            3.1 Initial Waiting Period: 30 days from policy inception (except accidents).
            3.2 Specific Illness Waiting Period: 2 years for listed illnesses (e.g., hernia,
                cataracts, joint replacement).
            3.3 Pre-Existing Disease (PED) Waiting Period: 4 years continuous coverage before
                PED-related claims are admissible.

            SECTION 4 – PRE-EXISTING DISEASES (PED)
            Any condition, ailment, injury or disease diagnosed or treated within 48 months
            before the first policy issuance date is considered a PED and subject to the
            waiting period in Section 3.3.

            SECTION 5 – EXCLUSIONS
            5.1 Cosmetic or plastic surgery (unless required due to accident or cancer treatment).
            5.2 Dental treatment (unless due to accident requiring hospitalisation).
            5.3 Maternity (covered under the Enhanced Maternity add-on rider only).
            5.4 Self-inflicted injuries, suicide attempt, and war-related injuries.
            5.5 Experimental treatments not approved by medical authorities.
            5.6 OPD (outpatient) consultations unless add-on OPD rider is active.

            SECTION 6 – CLAIM PROCEDURE
            6.1 Cashless Claims: Inform the insurer/TPA at least 3 days prior to planned
                hospitalisation (24 hours for emergency). The hospital must be on the
                empanelled network list.
            6.2 Reimbursement Claims: Submit original bills, discharge summary, prescription,
                and investigation reports within 30 days of discharge.
            6.3 Documents Required: Claim form, Photo ID, policy document, treating doctor's
                certificate, all original bills and receipts.

            SECTION 7 – SUM INSURED RESTORATION
            If the Sum Insured is exhausted in a policy year, it shall be restored once by
            100% for unrelated illnesses only. The restored amount cannot be used for the
            same illness or PEDs.

            SECTION 8 – NO CLAIM BONUS
            A cumulative bonus of 10% of Sum Insured per claim-free year, up to a maximum
            of 50% of the base Sum Insured, shall be added at renewal.

            SECTION 9 – DOMICILIARY TREATMENT
            Expenses incurred at home for conditions that would otherwise require
            hospitalisation, for a minimum period of 3 consecutive days, are covered up to
            10% of Sum Insured per policy year.

            SECTION 10 – GRIEVANCE REDRESSAL
            Disputes must first be raised with the company's Grievance Cell. If unresolved
            within 15 days, the insured may approach the Insurance Ombudsman in the
            jurisdiction of the registered office.
        """),
    },
    {
        "insurer": "star_health",
        "policy_type": "health",
        "filename": "star_health_comprehensive_policy.pdf",
        "title": "Star Health Comprehensive Insurance – Policy Schedule",
        "content": textwrap.dedent("""\
            SECTION 1 – INSURING CLAUSE
            Star Health & Allied Insurance Company Limited agrees to indemnify the insured
            for medical expenses incurred as an in-patient during the policy period, subject
            to terms and conditions herein.

            SECTION 2 – HOSPITALISATION BENEFITS
            2.1 In-patient hospitalisation: Covered for minimum 24 hours of admission.
            2.2 Day-care procedures: 541 listed procedures covered without 24-hour requirement.
            2.3 Pre-hospitalisation: Expenses 60 days before admission covered.
            2.4 Post-hospitalisation: Expenses 90 days after discharge covered.

            SECTION 3 – ROOM RENT
            Room rent is payable as per actuals up to the entitled category:
            - Bronze Plan: Shared room / General ward
            - Silver Plan: Single private room
            - Gold Plan: Suite / Deluxe room
            Proportionate deduction applies if entitled category is breached.

            SECTION 4 – WAITING PERIODS
            4.1 Initial waiting period: 30 days (waived for accidents).
            4.2 Named illness waiting period: 24 months.
            4.3 Pre-existing disease waiting period: 48 months from first policy date.

            SECTION 5 – MATERNITY BENEFIT (OPTIONAL RIDER)
            Covers normal delivery (up to ₹25,000) and caesarean section (up to ₹40,000)
            after a waiting period of 24 months. New-born cover included for first 90 days.

            SECTION 6 – EXCLUSIONS
            6.1 Any PED during waiting period.
            6.2 Non-allopathic treatment unless specifically covered.
            6.3 Obesity-related surgery (bariatric surgery) – excluded unless BMI > 40.
            6.4 Hazardous sports injuries.
            6.5 Treatment outside India.

            SECTION 7 – CLAIM INTIMATION
            Cashless claims require pre-authorisation from TPA 48 hours before planned
            hospitalisation. Emergency admissions: within 24 hours of admission.
            Reimbursement claims: documents to be submitted within 30 days of discharge.

            SECTION 8 – FRAUD INDICATORS
            Claims submitted with duplicate or fabricated bills, claims where the insured
            was not actually admitted, or claims with inflated diagnosis codes will be
            investigated and may result in policy cancellation and legal action.
        """),
    },
    {
        "insurer": "icici_lombard",
        "policy_type": "health",
        "filename": "icici_lombard_health_advantage.pdf",
        "title": "ICICI Lombard Health Advantage – Policy Wordings",
        "content": textwrap.dedent("""\
            SECTION 1 – SCOPE OF COVER
            ICICI Lombard General Insurance Company Limited provides health cover for
            hospitalisation expenses incurred in India due to illness or accident.

            SECTION 2 – KEY BENEFITS
            2.1 In-patient treatment: All medically necessary procedures covered.
            2.2 AYUSH treatment: Covered in government-recognised AYUSH hospitals.
            2.3 Organ donor expenses: Covered for harvesting of organ from a live donor.
            2.4 Mental illness: Covered per IRDAI Mental Healthcare guidelines 2016.

            SECTION 3 – SUB-LIMITS
            3.1 Room rent: 1% of SI/day for standard room; 2% for ICU.
            3.2 Cataract surgery: ₹40,000 per eye per policy year.
            3.3 Knee/Hip replacement: ₹1,50,000 per joint.
            3.4 Ambulance charges: ₹3,000 per hospitalisation.

            SECTION 4 – PRE-EXISTING DISEASE EXCLUSION
            PEDs are excluded for the first 48 months of continuous coverage.
            After 48 months, PED claims are fully covered up to the Sum Insured.

            SECTION 5 – CRITICAL ILLNESS LUMP SUM (RIDER)
            On first diagnosis of any of the 20 listed critical illnesses (cancer, stroke,
            heart attack, kidney failure, etc.), a lump sum of 100% of CI Sum Insured
            is payable irrespective of actual hospitalisation costs.

            SECTION 6 – CLAIM REQUIREMENTS
            - Completed claim form (ICICI Lombard standard form)
            - Original hospital bills, receipts, and discharge summary
            - Treating doctor's certificate with diagnosis (ICD-10 code)
            - Indoor case papers / medical records
            - Pharmacy bills with prescriptions
            - NEFT details for reimbursement
            - KYC documents (Aadhaar / PAN)
        """),
    },
    {
        "insurer": "niva_bupa",
        "policy_type": "health",
        "filename": "niva_bupa_reassure_policy.pdf",
        "title": "Niva Bupa ReAssure 2.0 – Policy Terms",
        "content": textwrap.dedent("""\
            SECTION 1 – PRODUCT FEATURES
            Niva Bupa ReAssure 2.0 offers a Reload benefit – if the base Sum Insured
            is exhausted, it is automatically reloaded for unrelated subsequent claims.

            SECTION 2 – LOCK THE CLOCK
            The premium applicable at the age of entry shall remain locked and will not
            increase solely due to age, provided the policy is renewed without break.

            SECTION 3 – BOOSTER BENEFIT
            Unused Sum Insured accumulates and is carried forward for up to 10 years.
            The booster amount can be used for any claim including PEDs after the
            waiting period.

            SECTION 4 – WAITING PERIODS
            4.1 First 30 days: Only accidents covered.
            4.2 Specific ailments: 2 years.
            4.3 PED: 3 years (reduced from industry standard of 4 years).

            SECTION 5 – ROOM RENT
            No room rent sub-limit under this plan. Insured is entitled to any room
            category at any network hospital without proportionate deduction.

            SECTION 6 – EXCLUSIONS
            6.1 Vitamins and supplements unless medically prescribed.
            6.2 Convalescence, general debility, rest cure.
            6.3 Sexually transmitted diseases.
            6.4 Hormone replacement therapy.

            SECTION 7 – CLAIMS PROCESS
            All cashless claims require pre-authorisation via the Niva Bupa app or
            helpline (1860-500-8888). Reimbursement forms must be submitted online
            within 30 days of discharge.
        """),
    },
    {
        "insurer": "hdfc_ergo",
        "policy_type": "motor",
        "filename": "hdfc_ergo_motor_comprehensive.pdf",
        "title": "HDFC ERGO Motor Comprehensive Policy – Private Car",
        "content": textwrap.dedent("""\
            SECTION 1 – OWN DAMAGE COVER
            The company will indemnify the insured for loss or damage to the insured
            vehicle caused by: accident, fire, explosion, self-ignition, lightning,
            theft, riot, strike, malicious act, flood, cyclone, or landslide.

            SECTION 2 – THIRD PARTY LIABILITY
            Unlimited liability for death/bodily injury to third parties.
            Property damage to third parties: up to ₹7.5 lakhs per accident.

            SECTION 3 – CLAIM PROCEDURE
            3.1 Notify the insurer within 24 hours of any accident or loss.
            3.2 File an FIR for theft, third-party injury, or major accidents.
            3.3 Do not repair vehicle without insurer's survey (except emergency repairs).
            3.4 Cashless repair available at 6,800+ network garages.

            SECTION 4 – DEPRECIATION SCHEDULE
            Rubber/nylon parts: 50% depreciation.
            Fibre glass: 30%.
            Wooden parts: 5% per year (max 50%).
            Metal body parts: as per Indian Motor Tariff depreciation table.

            SECTION 5 – EXCLUSIONS
            5.1 Wear and tear, mechanical/electrical breakdown.
            5.2 Driving under influence of alcohol or drugs.
            5.3 Driving without valid licence.
            5.4 War, nuclear risk, contamination.

            SECTION 6 – IDV (INSURED DECLARED VALUE)
            IDV is the maximum claim payable. It is calculated as manufacturer's listed
            price minus depreciation as per the Motor Tariff schedule.
        """),
    },
]


# ── PDF generation ────────────────────────────────────────────────────────────

def _write_pdf_with_reportlab(path: Path, title: str, content: str) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 0.5 * cm),
    ]
    for line in content.splitlines():
        if line.strip():
            story.append(Paragraph(line.strip(), styles["Normal"]))
            story.append(Spacer(1, 0.1 * cm))
        else:
            story.append(Spacer(1, 0.3 * cm))
    doc.build(story)


def _write_pdf_plain(path: Path, title: str, content: str) -> None:
    """Minimal PDF writer using raw PDF syntax — no extra dependencies."""
    lines = [title, "=" * len(title), ""] + content.splitlines()
    # Encode as simple PDF stream
    pdf_lines = []
    y = 800
    page_content = []
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        page_content.append(f"BT /F1 10 Tf {50} {y} Td ({safe}) Tj ET")
        y -= 14
        if y < 50:
            break  # single page for simplicity

    stream = "\n".join(page_content)
    stream_bytes = stream.encode("latin-1", errors="replace")

    objects = []
    # 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2: Pages
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # 3: Page
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    # 4: Content stream
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode()
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )
    # 5: Font
    objects.append(
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    # Build PDF
    body = b"%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(body))
        body += obj

    # Cross-reference table
    xref_offset = len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    body += xref.encode() + trailer.encode()
    path.write_bytes(body)


def seed_policies(base_dir: Path | None = None) -> int:
    """
    Write sample policy PDFs to the dataset directory.
    Returns the number of files written.
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent / "datasets" / "policies"

    count = 0
    for policy in POLICIES:
        target_dir = base_dir / policy["insurer"] / policy["policy_type"]
        target_dir.mkdir(parents=True, exist_ok=True)
        out_path = target_dir / policy["filename"]

        if out_path.exists():
            print(f"  [skip] {out_path.relative_to(base_dir)} (already exists)")
            continue

        if _REPORTLAB:
            _write_pdf_with_reportlab(out_path, policy["title"], policy["content"])
        else:
            _write_pdf_plain(out_path, policy["title"], policy["content"])

        print(f"  [ok]   {out_path.relative_to(base_dir)}")
        count += 1

    return count


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Insurance Claim Pre-Assurance – Policy PDF Seeder")
    print(f"  reportlab available: {_REPORTLAB}")
    print()
    base = Path(__file__).parent.parent / "datasets" / "policies"
    written = seed_policies(base)
    print(f"\nDone. {written} PDF(s) written.")
    if written == 0:
        print("All files already exist — delete them to regenerate.")
