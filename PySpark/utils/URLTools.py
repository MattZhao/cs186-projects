import urllib2

def fetch_webpage(uri):
    try:
        raw_html_text = urllib2.urlopen(uri, timeout=2).read()
    except:
        return ""
    return raw_html_text
