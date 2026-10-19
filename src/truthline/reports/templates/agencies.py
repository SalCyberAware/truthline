"""The six report drafts, as plain data.

Each agency is a list of sections. A section body may use these {fields}, which
the renderer (reports/drafts.py) fills from the case file:

    {reporter_name} {reporter_org} {reporter_role} {reporter_phone} {reporter_email}
    {reporter_location} {file_name} {sha256} {analyzed_at} {version} {grade_label}
    {reasoning} {evidence} {not_checked} {submitter_claim} {submitter_context}
    {safety_line} {what_truthline_found}

Anything the tool cannot know is written as [FILL IN: ...]. Truthline never
submits anything: a person reads, completes and sends each draft.

Offered under Apache-2.0 in addition to the project's AGPL-3.0.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Section:
    heading: str
    body: str


@dataclass(frozen=True)
class Agency:
    id: str
    name: str
    submit_at: str          # where a human submits the real report
    use_for: str            # one line: when this is the right destination
    before_you_send: tuple[str, ...]   # checklist shown above the draft, not part of it
    sections: tuple[Section, ...]
    attach_file: bool = True           # False: the file itself must not be sent (hash only)


FOUND = Section(
    "What an analysis tool found",
    "{what_truthline_found}",
)

CONTACT = Section(
    "Who is reporting",
    "Name: {reporter_name}\nOrganization / role: {reporter_org} / {reporter_role}\n"
    "Phone: {reporter_phone}\nEmail: {reporter_email}\nLocation: {reporter_location}",
)

FBI_TIP = Agency(
    id="fbi",
    name="FBI tip (threats)",
    submit_at="https://tips.fbi.gov, or your local FBI field office",
    use_for="A threat of violence, extortion or a serious federal crime. Anonymous tips are accepted.",
    before_you_send=(
        "If anyone may be in immediate danger, call 911 first. Do not wait for this report.",
        "Keep the original file exactly as received. Do not edit, crop or re-save it.",
        "Write down who sent it to you, how, and when. Details in your own words are the most valuable part.",
        "Fill in every [FILL IN: ...] item you can; delete the ones you cannot answer.",
    ),
    sections=(
        Section("Immediate danger", "{safety_line}"),
        Section(
            "What happened",
            "On [FILL IN: date and time you received it], {reporter_org} received a file described as "
            "{submitter_claim}.\n\nHow it reached us: [FILL IN: who sent it, through which app or account, to whom].\n\n"
            "Context from the person who submitted it: {submitter_context}\n\n"
            "Account names, phone numbers or handles involved: [FILL IN].",
        ),
        FOUND,
        Section(
            "What we are asking",
            "Please review this report for possible threat or criminal activity. We have kept the original file "
            "[FILL IN: confirm where the unedited original is stored] and can provide it, the case file and the "
            "SHA-256 fingerprint above on request.",
        ),
        CONTACT,
    ),
)

IC3 = Agency(
    id="ic3",
    name="FBI Internet Crime Complaint Center (IC3)",
    submit_at="https://www.ic3.gov (File a Complaint)",
    use_for="Internet-enabled fraud, extortion, impersonation, fake invoices or voice-cloned requests for money.",
    before_you_send=(
        "Only state what you know to be true. Knowingly false statements to a federal agency can be a crime (18 U.S.C. 1001).",
        "Collect payment details first: amounts, dates, account or wallet numbers, and the receiving bank.",
        "If money was sent, contact your bank right away; fast recall requests work best.",
        "IC3 will route a complaint involving a child to NCMEC; if a child is involved, also use the NCMEC draft.",
    ),
    sections=(
        Section(
            "Type of incident",
            "[FILL IN: e.g. business email compromise, impersonation of an executive, voice-clone call, sextortion, fake invoice]",
        ),
        Section(
            "What happened",
            "Date first contacted: [FILL IN]\nHow contact was made (email, text, call, social): [FILL IN]\n"
            "The file in question was described as {submitter_claim}.\nContext: {submitter_context}\n\n"
            "What the sender asked for: [FILL IN]",
        ),
        Section(
            "Money and accounts",
            "Amount lost (or at risk): [FILL IN]\nHow it was paid: [FILL IN: wire, card, gift cards, crypto, other]\n"
            "Receiving account / wallet / phone / email: [FILL IN]\nWebsite or social account used: [FILL IN]",
        ),
        FOUND,
        CONTACT,
    ),
)

NCMEC = Agency(
    id="ncmec",
    name="NCMEC CyberTipline (any case involving a minor)",
    submit_at="https://report.cybertip.org",
    use_for="Suspected sexual images or exploitation of anyone under 18, including AI-generated or altered images and sextortion.",
    before_you_send=(
        "Do NOT view, save, copy, forward or attach the image or video. Report what you know and leave the file where it is.",
        "Do not ask the child or anyone else to send it again. Do not confront the sender.",
        "The public can report to the CyberTipline; you do not need proof, and the report is not a judgment against anyone.",
        "For the child to have their own images removed from participating platforms, see takeitdown.ncmec.org.",
        "This draft intentionally includes no description of the content. Use the official form's own questions for the rest.",
    ),
    attach_file=False,
    sections=(
        Section(
            "What happened (no description of the content)",
            "On [FILL IN: date], {reporter_org} learned of a file that may involve a person under 18.\n"
            "How we learned of it: [FILL IN: e.g. a student told staff, a parent reported it]\n"
            "Where it was seen or shared (app, website, account names, URLs): [FILL IN]\n"
            "Is anyone being threatened or pressured for money or more images? [FILL IN: yes/no]",
        ),
        Section(
            "File identifiers (the file itself is not attached)",
            "File name as received: {file_name}\nSHA-256: {sha256}\nTool analysis ({version}, {analyzed_at}): {grade_label}",
        ),
        CONTACT,
    ),
)

SCHOOL_TIP = Agency(
    id="school",
    name="School or district tip line (school threats)",
    submit_at="Your state's school tip line, e.g. FortifyFL (Florida), Safe2Tell (Colorado), Say Something (other states); or your district's threat-assessment team",
    use_for="A threat or alarming message connected to a school. Run your own threat-assessment protocol regardless of what any tool says.",
    before_you_send=(
        "If anyone may be in immediate danger, call 911 first.",
        "Share the file only with your threat-assessment team and law enforcement. Do not circulate it to staff or students.",
        "Records sharing for health and safety can be allowed under FERPA; if unsure, ask your district's counsel.",
        "A tool's grade does not close a threat case. A fabricated screenshot can still be a crime and still needs a human response.",
    ),
    sections=(
        Section("Immediate danger", "{safety_line}"),
        Section(
            "What was reported",
            "School / district: {reporter_org}\nReceived on: [FILL IN: date and time]\n"
            "The item is described as {submitter_claim}.\nContext: {submitter_context}\n\n"
            "Who is named or implied, and at which school or event: [FILL IN]\nWho sent or posted it, if known: [FILL IN]",
        ),
        FOUND,
        Section(
            "Actions already taken",
            "[FILL IN: e.g. threat-assessment team convened, parents notified, police contacted at (time), original preserved]",
        ),
        CONTACT,
    ),
)

FTC = Agency(
    id="ftc",
    name="FTC ReportFraud (scams, fake reviews, impersonation)",
    submit_at="https://reportfraud.ftc.gov",
    use_for="Scams, impersonation of a business or agency, fake reviews, fake charity appeals. For non-consensual intimate images, see also TakeItDown.ftc.gov.",
    before_you_send=(
        "Have the business or person's name, website, phone number and any payment details ready.",
        "The FTC does not resolve individual complaints, but reports help it find and stop patterns.",
        "If money was sent, contact your bank or card issuer now.",
    ),
    sections=(
        Section(
            "What happened",
            "Date: [FILL IN]\nBusiness or person's name: [FILL IN]\nWebsite / phone / email / social account: [FILL IN]\n"
            "What they claimed or sold: [FILL IN]\nThe file in question was described as {submitter_claim}.\n"
            "Context: {submitter_context}",
        ),
        Section(
            "Money",
            "Amount paid: [FILL IN]\nHow you paid: [FILL IN: card, wire, gift card, crypto, app]\nDate paid: [FILL IN]",
        ),
        FOUND,
        CONTACT,
    ),
)

PRESERVATION = Agency(
    id="preservation",
    name="Evidence preservation request, 18 U.S.C. 2703(f) (for police to send)",
    submit_at="The platform's law-enforcement request portal or legal contact (each company publishes its own)",
    use_for="Asking a platform to keep an account's records before they are deleted. Only a governmental entity may send this; a school or business cannot.",
    before_you_send=(
        "THIS LETTER MUST BE SENT BY A GOVERNMENTAL ENTITY (a police officer or prosecutor). Give this draft to your local police; they decide whether to send it.",
        "A preservation request only asks the company to keep records. It does not make them hand anything over; that takes legal process.",
        "Preservation lasts 90 days and can be renewed once for 90 more if the agency asks again.",
        "Use the account names exactly as shown in the platform, including numeric IDs if available.",
        "Companies will not confirm anything to a school, business or individual without legal process. Expect that.",
    ),
    sections=(
        Section(
            "Letter",
            "FOR USE BY A GOVERNMENTAL ENTITY ONLY\n\n"
            "To: [FILL IN: platform name] Legal / Law Enforcement Compliance\n"
            "From: {reporter_name}, {reporter_role}, {reporter_org}\n"
            "Date: [FILL IN]\nAgency case number: [FILL IN]\n\n"
            "RE: Request to preserve records, 18 U.S.C. 2703(f)\n\n"
            "Pursuant to 18 U.S.C. 2703(f)(1), {reporter_org} requests that you take all necessary steps to preserve "
            "records and other evidence in your possession relating to the account(s) below, pending the issuance of "
            "a court order or other process.\n\n"
            "Account identifiers (username, display name, numeric ID, URL, email, phone): [FILL IN]\n"
            "Date range of interest: [FILL IN]\n"
            "Records to preserve: account registration and subscriber information, login and IP address records, and "
            "stored content and messages associated with the account(s), including content matching the file "
            "fingerprint (SHA-256) {sha256} if you can match it.\n\n"
            "Preservation is requested for 90 days from receipt. We may request one renewal for an additional 90 days.\n"
            "Please confirm receipt and the preservation period to the contact below.\n\n"
            "{reporter_name}\n{reporter_role}, {reporter_org}\nPhone: {reporter_phone}\nEmail: {reporter_email}\n"
            "Badge / ID: [FILL IN]\nSignature: [FILL IN]",
        ),
        Section(
            "Background for the officer (not part of the letter)",
            "{what_truthline_found}",
        ),
    ),
)

AGENCIES: dict[str, Agency] = {a.id: a for a in (FBI_TIP, IC3, NCMEC, SCHOOL_TIP, FTC, PRESERVATION)}
