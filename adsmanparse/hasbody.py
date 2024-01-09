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
