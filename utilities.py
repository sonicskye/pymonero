import requests

def getContent(url):
    req = requests.get(url)
    page = req.content
    return page

def QuotedStr(s):
    return '"%s"'%s

def SingleQuotedStr(s):
    return "'%s'"%s