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
