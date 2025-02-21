import re
from bs4 import BeautifulSoup

def has_body(data):
    try:
        soup = BeautifulSoup(data, 'lxml-xml')
    except Exception as err:
        print("soupify failed:",err)
    else:
        try:
            body = soup.find('body')
        except Exception as err:
            print('find failed:', err)
        else:
            if body:
                return True
    return False


def suppress_title(record, suppressed_titles):
    title = record.get('title', {}).get('textEnglish', None)
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
                    if doi_bibc.get(doi, None):
                        doi_bibc[doi] = bibcode
                    else:
                        print("WARNING: multiple canonical bibs for one DOI: %s\t%s\t%s" % (doi, doi_bibc[doi], bibcode))
    except Exception as err:
        print("Failed to load doi-bibcode mapping: %s" % err)
    return doi_bibc

