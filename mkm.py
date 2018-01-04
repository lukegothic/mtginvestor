from mkmsdk.mkm import mkm
from lxml import html
from queue import Queue
import os, re, sys, time, json, requests

import time
import re
import threading
from queue import Queue
from lxml import html

q = None
lock = threading.Lock()

def getTrendPriceFromHTML(page):
    tree = html.fromstring(page)
    table = tree.xpath("//table[@class='availTable']/tbody/tr")
    return (float)(table[2].xpath(".//td")[1].text_content().replace(",",".").replace("€",""))
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
    if (not card["idmkm"] is None):
        baseurl = "https://www.cardmarket.com/en/Magic"
        basedir = "__mycache__/mkm/prices"
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        isFoil = "Y" if card["isFoil"] else "N"
        productFilter = {
            "productFilter[sellerRatings][]": ["1", "2"],
            "productFilter[idLanguage][]": [card["idLanguage"]],
            "productFilter[condition][]": ["MT", "NM"],
            "productFilter[isFoil]": isFoil
        }
        carddir = "{}/{}".format(basedir, card["idmkm"])
        if not os.path.exists(carddir):
            with lock:
                os.makedirs(carddir)
        filete = "{}/{}{}.html".format(carddir, card["idLanguage"], isFoil)
        try:
            with open(filete, "r", encoding="utf-8") as f:
                data = f.read()
        except:
            resp = requests.post("{}/Products/Singles/{}".format(baseurl, card["idmkm"]), productFilter, headers={}, timeout = 10)
            data = resp.text
            if data != "":
                with open(filete, "w", encoding="utf-8") as f:
                    f.write(data)
        if data != "":
            card["mkmprices"] = getPriceDataFromHTML(data)
            card["mkmprice"] = getTrendPriceFromHTML(data)
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
    if article["price"] >= 15:
        comment = "[ Perfect Size and Bubble Envelope ]"
    elif article["price"] / (4 if article["isPlayset"] == "true" else 1) >= 3:
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
    def worker():
        while True:
            getPriceData(q.get())
            time.sleep(0.05)
            q.task_done()
            sys.stdout.write("{:>4}".format(q.qsize()))
    q = Queue()
    for i in range(6):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
    for card in cards:
        if "idmkm" in card:
            q.put(card)
    sys.stdout.write("Items restantes...")
    sys.stdout.flush()
    q.join()

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
