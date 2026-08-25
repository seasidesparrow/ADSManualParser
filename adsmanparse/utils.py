import html
import re

from bs4 import BeautifulSoup

from adsmanparse.custom_entity_conversions import ASCII_CUST_MAP

ENTITY_RE = re.compile(r"&([a-zA-Z#][a-zA-Z0-9]+);")


def has_body(data):
    try:
        soup = BeautifulSoup(data, "lxml-xml")
    except Exception as err:
        print("soupify failed:", err)
    else:
        try:
            body = soup.find("body")
        except Exception as err:
            print("find failed:", err)
        else:
            if body:
                return True
    return False


def suppress_title(record, suppressed_titles):
    title = record.get("title", {}).get("textEnglish", None)
    if title:
        for dtitle in suppressed_titles:
            if re.search(dtitle, title, flags=re.IGNORECASE):
                return True


def load_doi_bibcode(infile):
    doi_bibc = {}
    try:
        with open(infile, "r") as fd:
            for l in fd.readlines():
                (bibcode, doi) = l.strip().split("\t")
                if "\.tmp" not in bibcode:
                    if not doi_bibc.get(doi, None):
                        doi_bibc[doi] = bibcode
                    # else:
                    #     print("WARNING: multiple canonical bibs for one DOI: %s\t%s\t%s" % (doi, doi_bibc[doi], bibcode))
    except Exception as err:
        print("Failed to load doi-bibcode mapping: %s" % err)
    return doi_bibc


class ConvertEntities(object):
    def __init__(self):
        pass

    def convert(self, text):
        try:
            new_text = self._convert_html5_to_html4(text)
            new_text = self._convert_entities_to_ascii(new_text)
            new_text = self._enforce_ascii(new_text)
        except Exception as err:
            raise Exception("Entity conversion failed: %s" % err)
        else:
            return new_text

    def _enforce_ascii(self, text: str) -> str:
        """
        Safety net: guarantee the returned text is strictly ASCII.

        Every code point above ASCII should already have been turned into
        a named or decimal entity by _convert_html5_to_html4. This pass
        exists so that if a future change to the rules there (or an
        unanticipated code point) ever lets a raw Unicode character slip
        through, it still comes out as an ASCII-safe decimal NCR instead
        of unescaped Unicode.
        """
        if text.isascii():
            return text
        else:
            out = []
            for ch in text:
                cp = ord(ch)
                out.append(ch if cp < 128 else f"&#{cp};")
            return "".join(out)

    def _convert_entities_to_ascii(self, text: str) -> str:
        def replacer(match):
            name = match.group(1)

            # If it's in our ASCII conversion map, convert it
            if name in ASCII_CUST_MAP:
                return ASCII_CUST_MAP[name]

            # Otherwise leave unchanged
            return match.group(0)

        return ENTITY_RE.sub(replacer, text)

    def _convert_html5_to_html4(self, text):
        """
        Convert HTML5 content to HTML4-compatible output.

        Rules:
          1. ASCII characters are preserved.
          2. HTML4 Latin accented letters and Greek letters use named entities.
          3. Cyrillic characters always become decimal NCRs.
          4. Mathematical, logical, arrow, and technical symbols always become
             decimal NCRs.
          5. Other HTML4 entities use their named form.
          6. Everything else above ASCII becomes a decimal NCR.

        Examples:
          &alpha;         -> &alpha;
          &Acy;           -> &#1040;
          &forall;        -> &#8704;
          &GreaterEqual;  -> &#8805;
          &inodot;        -> &#305;
        """

        decoded = html.unescape(text)

        out = []

        for ch in decoded:
            cp = ord(ch)

            # Preserve ASCII
            if cp < 128:
                if ch == "&":
                    out.append("&")
                    # out.append('&amp;')
                elif ch == "<":
                    out.append("<")
                    # out.append('&lt;')
                elif ch == ">":
                    out.append(">")
                    # out.append('&gt;')
                else:
                    out.append(ch)
                continue

            # Cyrillic -> decimal NCR
            if (
                0x0400 <= cp <= 0x04FF
                or 0x0500 <= cp <= 0x052F
                or 0x2DE0 <= cp <= 0x2DFF
                or 0xA640 <= cp <= 0xA69F
            ):
                out.append(f"&#{cp};")
                continue

            # Math, logic, arrows, technical symbols -> decimal NCR
            if (
                0x2190 <= cp <= 0x21FF
                or 0x2200 <= cp <= 0x22FF
                or 0x27C0 <= cp <= 0x27EF
                or 0x2980 <= cp <= 0x29FF
                or 0x2A00 <= cp <= 0x2AFF
                or 0x2300 <= cp <= 0x23FF
            ):
                out.append(f"&#{cp};")
                continue

            # Latin Extended (Turkish, etc.)
            if 0x0100 <= cp <= 0x017F or 0x0180 <= cp <= 0x024F:
                if cp in html.entities.codepoint2name:
                    name = html.entities.codepoint2name[cp]

                    # Preserve traditional HTML4 accented Latin entities
                    if name.startswith(
                        (
                            "A",
                            "a",
                            "E",
                            "e",
                            "I",
                            "i",
                            "O",
                            "o",
                            "U",
                            "u",
                            "Y",
                            "y",
                            "C",
                            "c",
                            "N",
                            "n",
                            "S",
                            "s",
                        )
                    ):
                        out.append(f"&{name};")
                    else:
                        out.append(f"&#{cp};")
                else:
                    out.append(f"&#{cp};")
                continue

            # Greek -> prefer named HTML4 entities
            if 0x0370 <= cp <= 0x03FF:
                if cp in html.entities.codepoint2name:
                    out.append(f"&{html.entities.codepoint2name[cp]};")
                else:
                    out.append(f"&#{cp};")
                continue

            # Everything else
            if cp in html.entities.codepoint2name:
                out.append(f"&{html.entities.codepoint2name[cp]};")
            else:
                out.append(f"&#{cp};")

        return "".join(out)
