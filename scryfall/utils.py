import requests
def getbysetcodecardnum(setcode, cardnum):
    r = requests.get("https://api.scryfall.com/cards/{}/{}?format=json".format(setcode.lower(), cardnum))
    print(r.json())

getbysetcodecardnum("vma", 321)
