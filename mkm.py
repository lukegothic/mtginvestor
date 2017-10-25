from mkmsdk.mkm import mkm
from lxml import html
import os, re, sys, json, requests
def getPriceDataFromHTML(page):
    prices = []
    tree = html.fromstring(page)
    for row in tree.xpath('//tbody[@id="articlesTable"]/tr[not(@class)]'):
        itemlocation = row.xpath(".//td[@class='Seller']/span/span/span[@class='icon']")[0].attrib["onmouseover"]
        itemlocation = re.search("'Item location: (.*)'", itemlocation).group(1)
        seller = row.xpath(".//td[@class='Seller']/span/span/a")[0].attrib["href"].replace("/en/Magic/Users/", "")
        price = row.xpath(".//td[contains(@class,'st_price')]")[0].text_content().replace(",",".").replace("€","")
        available = row.xpath(".//td[contains(@class,'st_ItemCount')]")[0].text_content()
        ppu = re.search('\(PPU: (.*?)\)', price)
        if not ppu is None:
            price = ppu.group(1)
            available = "4"
        prices.append({ "location": itemlocation, "seller": seller, "price": price, "available": (int)(available) })
    return prices
def getPriceData(card):
    baseurl = "https://www.cardmarket.com/en/Magic"
    basedir = "__mycache__/mkm/prices"
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    for entry in card["entries"]:
        isFoil = "Y" if entry["isFoil"] else "N"
        productFilter = {
            "productFilter[sellerRatings][]": ["1", "2"],
            "productFilter[idLanguage][]": [entry["idLanguage"]],
            "productFilter[condition][]": ["MT", "NM"],
            "productFilter[isFoil]": isFoil
        }
        carddir = "{}/{}".format(basedir, card["idmkm"])
        if not os.path.exists(carddir):
            os.makedirs(carddir)
        filete = "{}/{}{}.html".format(carddir, entry["idLanguage"], isFoil)
        try:
            with open(filete, "r", encoding="utf-8") as f:
                data = f.read()
        except:
            resp = requests.post("{}/Products/Singles/{}".format(baseurl, card["idmkm"]), productFilter, headers={}, timeout = 10)
            data = resp.text
            with open(filete, "w", encoding="utf-8") as f:
                f.write(data)
        if data != "":
            prices = getPriceDataFromHTML(data)
            if (len(prices) > 0):
                print(prices[0]["price"])
            else:
                print("Not available")
        else:
            pass #relanzar
def getMasterData():
    basedir = "__offlinecache__/mkm/basedata"
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    # siempre pedimos la lista de sets actualizada, asi si falta alguno se pedira
    sys.stdout.write("Obteniendo sets...")
    sys.stdout.flush()
    filete = basedir + "/sets.json"
    try:
        resp = mkm.market_place.expansion(game=1)
        with open(filete, "w") as f:
            f.write(resp.text)
        sets = resp.json()
        sys.stdout.write("última version online\n")
    except:
        try:
            with open(filete) as f:
                sets = json.loads(f.read())
            sys.stdout.write("cache\n")
        except:
            sys.exit("[MKM] No se ha podido obtener los datos de inventario")
    allcards = []
    sys.stdout.write("Obteniendo cartas...")
    sys.stdout.flush()
    for set in sets["expansion"]:
        filete = "{}/{}.json".format(basedir, set["idExpansion"])
        try:
            with open(filete) as f:
                cards = json.loads(f.read())
        except:
            resp = mkm.market_place.expansion_singles(game=1, name=set["name"])
            with open(filete, "w") as f:
                f.write(resp.text)
            cards = resp.json()
        allcards.extend(cards["card"])
    sys.stdout.write("OK\n")
    return allcards

def getCommentByPrice(article):
    #"●▬▬▬▬๑۩ {} ۩๑▬▬▬▬▬●"
    #",.-~*´¨¯¨`*·~-.¸-[{}]-,.-~*´¨¯¨`*·~-.¸"
    #"(╯°□°）╯︵ ┻━┻ {}"
    price = article["price"] / (4 if article["isPlayset"] == "true" else 1)
    if price >= 15:
        comment = "[ Perfect Size and Bubble Envelope ]"
    elif price >= 3:
        comment = "[ Perfect Size ]"
    else:
        comment = "[ You Win ]"
    return '-~*{}*~- from MTG(c) Judge'.format(comment)

def postStock(cards):
    # mkm.stock_management.post_stock(data = {
    #   'article': [
    #     {
    #         'idProduct': 261427,
    #         'idLanguage': 1,
    #         'comments': 'xxxxxxxxx',
    #         'count': 4,
    #         'price': 99.99,
    #         'condition': 'EX',
    #         'isFoil': 'false',
    #         'isSigned': 'false',
    #         'isPlayset': 'false'
    #     }
    #   ]
    # })
    for card in cards:
        if card["set"] != "":
            sys.stdout.write("[{}] {} ({}) ".format("X" if "idmkm" in card else " ", card["name"], card["set"]))
            sys.stdout.flush()
            if "idmkm" in card:
                getPriceData(card)
            else:
                print()
        else:
            print("[·] {} ()".format(card["name"]))
def toPostableArticle(article):
    return {
        "idArticle": article["idArticle"],
        "idLanguage": article["language"]["idLanguage"],
        "comments": article["comments"],
        "count": article["count"],
        "price": article["price"],
        "condition": article["condition"],
        "isFoil": "true" if article["isFoil"] else "false",
        "isSigned": "true" if article["isSigned"] else "false",
        "isPlayset": "true" if article["isPlayset"] else "false"
    }
def updateStockComments():
    stock = mkm.stock_management.get_stock().json()
    articles = []
    for stockitem in stock["article"]:
        article = toPostableArticle(stockitem)
        article["comments"] = getCommentByPrice(article)
        articles.append(article)
    sys.stdout.write("Updating stock...")
    sys.stdout.flush()
    mkm.stock_management.put_stock(data = { "article": articles })
    sys.stdout.write("OK\n")
