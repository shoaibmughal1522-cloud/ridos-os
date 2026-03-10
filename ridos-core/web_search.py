"""
╔══════════════════════════════════════════════════════════════╗
║  RIDOS OS v1.1 — Web Search Module                          ║
║  Copyright (C) 2026 RIDOS OS Project                        ║
║  Licensed under GNU General Public License v3 (GPL-3.0)     ║
║  https://github.com/ridos-os/ridos-os                       ║
╚══════════════════════════════════════════════════════════════╝

Provides web search capabilities using DuckDuckGo Instant Answer API.
No API key required — completely free.

Features:
  - DuckDuckGo Instant Answers (definitions, facts, quick answers)
  - IT-specific search keyword detection
  - CVE / security advisory lookup
  - RFC / protocol documentation lookup
  - Result formatting for terminal display
"""

import re
import asyncio
from typing import Optional

# ── Search trigger keywords ────────────────────────────────────
# General search
SEARCH_KEYWORDS = [
    "search for", "look up", "find", "google",
    "search:", "what is the latest", "news about",
    "tell me about", "information on",
]

# IT-specific search triggers
IT_SEARCH_KEYWORDS = [
    # CVE & Security
    "cve-", "cve ", "vulnerability", "exploit", "security advisory",
    "patch for", "zero day", "security bulletin",
    # Protocols & Standards
    "rfc ", "rfc-", "protocol spec", "ieee ", "ietf",
    # Tools & Commands
    "how to use", "man page for", "syntax of", "example of",
    "how do i", "command for", "flag for",
    # Error lookup
    "error code", "exit code", "errno", "what does error",
    # Networking
    "port number", "default port", "well-known port",
    "ip range", "subnet for", "asn for", "whois",
]

# ── Search result dataclass ────────────────────────────────────
class SearchResult:
    def __init__(self, query: str, answer: str, abstract: str,
                 source: str, url: str, related: list,
                 success: bool, search_type: str = "general"):
        self.query       = query
        self.answer      = answer
        self.abstract    = abstract
        self.source      = source
        self.url         = url
        self.related     = related
        self.success     = success
        self.search_type = search_type  # "general" | "cve" | "rfc" | "port"

    def to_dict(self) -> dict:
        return self.__dict__


# ── Query classifier ───────────────────────────────────────────
def is_search_query(text: str) -> bool:
    """Returns True if the message should trigger a web search."""
    t = text.lower().strip()

    # Check general search triggers
    for kw in SEARCH_KEYWORDS:
        if t.startswith(kw) or f" {kw}" in t:
            return True

    # Check IT-specific triggers
    for kw in IT_SEARCH_KEYWORDS:
        if kw in t:
            return True

    return False


def classify_query(text: str) -> str:
    """
    Returns query type: 'cve' | 'rfc' | 'port' | 'general'
    Helps route to the best data source.
    """
    t = text.lower()
    if re.search(r"cve-\d{4}-\d+", t) or "cve " in t:
        return "cve"
    if re.search(r"rfc[- ]?\d+", t) or "rfc " in t:
        return "rfc"
    if re.search(r"port\s+\d+", t) or "default port" in t:
        return "port"
    return "general"


def clean_query(text: str) -> str:
    """Strip command prefixes to get the actual search terms."""
    # Remove leading command words
    prefixes = [
        r"^search for\s+", r"^search:\s+", r"^look up\s+",
        r"^find\s+", r"^google\s+", r"^tell me about\s+",
        r"^what is the latest\s+", r"^news about\s+",
        r"^information on\s+", r"^how to use\s+",
        r"^man page for\s+", r"^syntax of\s+",
    ]
    q = text.strip()
    for prefix in prefixes:
        q = re.sub(prefix, "", q, flags=re.IGNORECASE).strip()
    return q


# ── DuckDuckGo search ──────────────────────────────────────────
async def duckduckgo_search(query: str) -> dict:
    """
    Query DuckDuckGo Instant Answer API.
    Free, no API key, no rate limit for reasonable usage.
    """
    import httpx

    params = {
        "q":           query,
        "format":      "json",
        "no_html":     "1",
        "skip_disambig": "1",
        "no_redirect": "1",
    }

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.get(
            "https://api.duckduckgo.com/",
            params=params,
            headers={"User-Agent": "RIDOS-OS/1.1 (IT Search Module)"}
        )
        response.raise_for_status()
        return response.json()


# ── Specialized IT searches ────────────────────────────────────
async def search_cve(cve_id: str) -> SearchResult:
    """
    Look up a CVE (Common Vulnerabilities and Exposures) entry.
    Uses NVD (National Vulnerability Database) via DuckDuckGo.
    """
    query = f"{cve_id} site:nvd.nist.gov OR site:cve.mitre.org"
    try:
        data = await duckduckgo_search(cve_id)
        answer   = data.get("Answer", "")
        abstract = data.get("AbstractText", "")
        url      = data.get("AbstractURL", f"https://nvd.nist.gov/vuln/detail/{cve_id.upper()}")

        if not abstract:
            abstract = (
                f"CVE lookup: {cve_id.upper()}\n"
                f"Check NVD for full details: https://nvd.nist.gov/vuln/detail/{cve_id.upper()}\n"
                f"Check MITRE: https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id.upper()}"
            )

        return SearchResult(
            query=cve_id, answer=answer, abstract=abstract,
            source="NVD / MITRE", url=url, related=[],
            success=True, search_type="cve"
        )
    except Exception as e:
        return SearchResult(
            query=cve_id, answer="", abstract=f"CVE lookup failed: {e}",
            source="", url=f"https://nvd.nist.gov/vuln/detail/{cve_id.upper()}",
            related=[], success=False, search_type="cve"
        )


async def search_rfc(rfc_number: str) -> SearchResult:
    """Look up an RFC (Request for Comments) document."""
    num = re.search(r"\d+", rfc_number)
    if not num:
        return SearchResult(
            query=rfc_number, answer="", abstract="Invalid RFC number.",
            source="", url="https://www.rfc-editor.org", related=[],
            success=False, search_type="rfc"
        )
    n = num.group(0)
    url = f"https://www.rfc-editor.org/rfc/rfc{n}"
    try:
        data = await duckduckgo_search(f"RFC {n} IETF standard")
        abstract = data.get("AbstractText", "") or (
            f"RFC {n} — Internet Engineering Task Force\n"
            f"Full document: {url}"
        )
        return SearchResult(
            query=f"RFC {n}", answer=data.get("Answer", ""),
            abstract=abstract, source="IETF RFC Editor",
            url=url, related=[], success=True, search_type="rfc"
        )
    except Exception as e:
        return SearchResult(
            query=f"RFC {n}", answer="",
            abstract=f"RFC lookup failed: {e}\nDirect link: {url}",
            source="IETF", url=url, related=[], success=False, search_type="rfc"
        )


async def search_port(port_query: str) -> SearchResult:
    """Look up information about a network port number."""
    port_match = re.search(r"\d+", port_query)
    if not port_match:
        return SearchResult(
            query=port_query, answer="", abstract="No port number found.",
            source="", url="", related=[], success=False, search_type="port"
        )

    port = port_match.group(0)

    # Common well-known ports — instant answer without network call
    WELL_KNOWN = {
        "20":   "FTP Data Transfer",
        "21":   "FTP Control",
        "22":   "SSH — Secure Shell",
        "23":   "Telnet (unencrypted, avoid)",
        "25":   "SMTP — Email sending",
        "53":   "DNS — Domain Name System",
        "67":   "DHCP Server",
        "68":   "DHCP Client",
        "80":   "HTTP — Web traffic",
        "110":  "POP3 — Email retrieval",
        "119":  "NNTP — Usenet",
        "123":  "NTP — Network Time Protocol",
        "143":  "IMAP — Email retrieval",
        "161":  "SNMP — Network management",
        "194":  "IRC",
        "389":  "LDAP — Directory services",
        "443":  "HTTPS — Encrypted web traffic",
        "445":  "SMB — Windows file sharing",
        "465":  "SMTPS — Encrypted email",
        "514":  "Syslog",
        "587":  "SMTP Submission (email clients)",
        "636":  "LDAPS — Encrypted LDAP",
        "993":  "IMAPS — Encrypted IMAP",
        "995":  "POP3S — Encrypted POP3",
        "1194": "OpenVPN",
        "1433": "Microsoft SQL Server",
        "1521": "Oracle Database",
        "3306": "MySQL / MariaDB",
        "3389": "RDP — Remote Desktop Protocol",
        "5432": "PostgreSQL",
        "5900": "VNC — Remote desktop",
        "6379": "Redis",
        "8080": "HTTP Alternate / Proxy",
        "8443": "HTTPS Alternate",
        "9200": "Elasticsearch",
        "27017":"MongoDB",
    }

    if port in WELL_KNOWN:
        desc = WELL_KNOWN[port]
        return SearchResult(
            query=f"Port {port}", answer=f"Port {port}/TCP — {desc}",
            abstract=(
                f"Port {port} — {desc}\n"
                f"Protocol: TCP (also UDP in some cases)\n"
                f"Status: {'Well-known (IANA assigned)' if int(port) < 1024 else 'Registered'}"
            ),
            source="IANA Port Registry", url="https://www.iana.org/assignments/service-names-port-numbers",
            related=[], success=True, search_type="port"
        )

    # Unknown port — search DuckDuckGo
    try:
        data = await duckduckgo_search(f"TCP port {port} service protocol")
        abstract = data.get("AbstractText", "") or f"Port {port} — No IANA standard assignment found."
        return SearchResult(
            query=f"Port {port}", answer=data.get("Answer", ""),
            abstract=abstract, source="IANA",
            url="https://www.iana.org/assignments/service-names-port-numbers",
            related=[], success=bool(abstract), search_type="port"
        )
    except Exception as e:
        return SearchResult(
            query=f"Port {port}", answer="",
            abstract=f"Port lookup failed: {e}",
            source="", url="", related=[], success=False, search_type="port"
        )


# ── General web search ─────────────────────────────────────────
async def web_search(query: str) -> SearchResult:
    """
    Main search entry point. Automatically routes to the
    best search method based on query type.
    """
    clean  = clean_query(query)
    qtype  = classify_query(clean)

    # Route to specialized handlers
    if qtype == "cve":
        cve_match = re.search(r"cve-\d{4}-\d+", clean, re.IGNORECASE)
        if cve_match:
            return await search_cve(cve_match.group(0))

    if qtype == "rfc":
        return await search_rfc(clean)

    if qtype == "port":
        return await search_port(clean)

    # General DuckDuckGo search
    try:
        data    = await duckduckgo_search(clean)
        answer   = data.get("Answer", "")
        abstract = data.get("AbstractText", "")
        source   = data.get("AbstractSource", "")
        url      = data.get("AbstractURL", "")

        # Collect related topics
        related = []
        for topic in data.get("RelatedTopics", [])[:4]:
            if isinstance(topic, dict) and "Text" in topic:
                related.append(topic["Text"][:100])

        # If no direct answer, try to get something useful
        if not answer and not abstract:
            # Check if DuckDuckGo redirected us somewhere
            redirect = data.get("Redirect", "")
            if redirect:
                abstract = f"Top result: {redirect}"
            elif related:
                abstract = f"Related: {related[0]}"
            else:
                abstract = f"No instant answer found for: {clean}"

        return SearchResult(
            query=clean, answer=answer,
            abstract=abstract[:500] if abstract else "",
            source=source, url=url,
            related=related, success=bool(answer or abstract),
            search_type="general"
        )

    except Exception as e:
        return SearchResult(
            query=clean, answer="",
            abstract=f"Search failed: {e}",
            source="", url="", related=[],
            success=False, search_type="general"
        )


# ── Terminal formatter ─────────────────────────────────────────
def format_result(result: SearchResult) -> str:
    """
    Formats a SearchResult for clean terminal display.
    Used by ai_daemon.py to prepend search context to the AI prompt.
    """
    lines = []

    # Header by type
    type_headers = {
        "cve":     f"[CVE Lookup: {result.query.upper()}]",
        "rfc":     f"[RFC Lookup: {result.query}]",
        "port":    f"[Port Lookup: {result.query}]",
        "general": f"[Web Search: {result.query}]",
    }
    lines.append(type_headers.get(result.search_type, f"[Search: {result.query}]"))

    if result.answer:
        lines.append(f"Answer: {result.answer}")

    if result.abstract:
        lines.append(f"Summary: {result.abstract}")

    if result.source:
        lines.append(f"Source: {result.source}")

    if result.url:
        lines.append(f"URL: {result.url}")

    if result.related:
        lines.append("Related:")
        for r in result.related[:3]:
            lines.append(f"  • {r}")

    if not result.success:
        lines.append("⚠ Search returned no results.")

    return "\n".join(lines)


def format_result_short(result: SearchResult) -> str:
    """Compact one-line summary for display in the shell."""
    if result.answer:
        return result.answer[:200]
    if result.abstract:
        return result.abstract[:200]
    return f"No result for: {result.query}"


# ── CLI test (run directly to test) ───────────────────────────
if __name__ == "__main__":
    import sys

    async def test():
        queries = [
            "search for nmap tutorial",
            "CVE-2024-1234",
            "RFC 793",
            "port 443",
            "what is DNS over HTTPS",
        ]
        test_q = sys.argv[1] if len(sys.argv) > 1 else queries[0]

        print(f"\nTesting: {test_q}")
        print(f"Is search query: {is_search_query(test_q)}")
        print(f"Query type: {classify_query(clean_query(test_q))}")
        print("─" * 50)

        result = await web_search(test_q)
        print(format_result(result))

    asyncio.run(test())
