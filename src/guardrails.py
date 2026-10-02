"""Rule-based routing: PII, advice, performance, and factual queries."""
import re

PII = {
    "PAN": re.compile(r"\b[A-Za-z]{5}\d{4}[A-Za-z]\b"),
    "Aadhaar": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)"),
    "account/folio number": re.compile(r"\b(?:account|a/c|folio)\s*(?:no\.?|number|#)?\s*[:\-]?\s*\d{6,}\b", re.I),
    "OTP": re.compile(r"\b(?:otp|one[- ]time password)\b[^\n]{0,20}\d{4,8}|\b\d{4,8}\b[^\n]{0,15}\botp\b", re.I),
}
ADVICE = re.compile(
    r"\b(should i|shall i|can i)\b.*\b(buy|sell|invest|redeem|switch|hold|stop|exit|put)\b|"
    r"\b(is it (a )?(good|bad|safe|worth)|worth (investing|buying)|good (time|fund|investment)|best (fund|scheme|time)|"
    r"which (fund|scheme) (is|should)|better than|recommend|suggest|advice|advise|my portfolio|how much should|"
    r"will (it|the fund|nav) (go|rise|fall|grow)|predict|forecast|target price|safe to invest)\b", re.I)
PERFORMANCE = re.compile(
    r"\b(returns?|cagr|xirr|performance|performed|outperform|underperform|beat|growth rate|how much (has|did|will)|profit|gain(ed)?|"
    r"past \d+ years?|\d+ ?(yr|year)s? (return|performance)|nav (today|now|latest|current))\b", re.I)

EDU_LINK = "https://www.sebi.gov.in/investor-education.html"
AMFI_LINK = "https://www.amfiindia.com/investor-corner/knowledge-center"


def detect_pii(text):
    return [k for k, rx in PII.items() if rx.search(text)]


def route(query):
    """Return (route, detail). route in {pii, advice, performance, factual}."""
    pii = detect_pii(query)
    if pii:
        return "pii", pii
    if ADVICE.search(query):
        return "advice", None
    if PERFORMANCE.search(query):
        return "performance", None
    return "factual", None
