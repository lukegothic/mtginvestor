from mkmsdk.mkm import mkm
from lxml import html
from queue import Queue
import os, re, sys, csv, time, json, requests, phppgadmin

import time
import re
import threading
from queue import Queue
from lxml import html

lock = threading.Lock()
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
        if seller != "ivan-the-seller":
            prices.append({ "itemlocation": itemlocation, "seller": seller, "price": (float)(price), "available": (int)(available) })
    return prices
def getPriceData_DB(card, queue):
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
            try:
                os.makedirs(carddir)
            except:
                pass
    filete = "{}/{}{}.html".format(carddir, card["idLanguage"], isFoil)
    try:
        with open(filete, "r", encoding="utf-8") as f:
            data = f.read()
    except:
        try:
            resp = requests.post("{}/Products/Singles/{}".format(baseurl, card["idmkm"]), productFilter, headers={}, timeout = 10)
            data = resp.text
            if data != "":
                with lock:
                    try:
                        with open(filete, "w", encoding="utf-8") as f:
                            f.write(data)
                    except:
                        pass
        except:
            data = ""
    if data != "":
        card["prices"] = getPriceDataFromHTML(data)
    else:
        queue.put(card)
    sys.stdout.write("Download progress: %d   \r" % (queue.qsize()) )
def getPriceDataSingle(card):
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
def getPriceData(stockitem, queue):
    baseurl = "https://www.cardmarket.com/en/Magic"
    basedir = "__mycache__/mkm/prices"
    if not os.path.exists(basedir):
        with lock:
            os.makedirs(basedir)
    isFoil = "Y" if stockitem["isFoil"] else "N"
    productFilter = {
        "productFilter[sellerRatings][]": ["1", "2"],
        "productFilter[idLanguage][]": [stockitem["idLanguage"]],
        "productFilter[condition][]": ["MT", "NM"],
        "productFilter[isFoil]": isFoil
    }
    carddir = "{}/{}".format(basedir, stockitem["website"])
    if not os.path.exists(carddir):
        with lock:
            try:
                os.makedirs(carddir)
            except:
                pass
    filete = "{}/{}{}.html".format(carddir, stockitem["idLanguage"], isFoil)
    try:
        with open(filete, "r", encoding="utf-8") as f:
            data = f.read()
    except:
        try:
            resp = requests.post("{}{}".format(baseurl, stockitem["website"]), productFilter, headers={}, timeout = 10)
            data = resp.text
            if data != "":
                with lock:
                    try:
                        with open(filete, "w", encoding="utf-8") as f:
                            f.write(data)
                    except:
                        pass
        except:
            data = ""
    if data != "":
        stockitem["prices"] = getPriceDataFromHTML(data)
    else:
        queue.put(stockitem)
    sys.stdout.write("Download progress: %d   \r" % (queue.qsize()) )
    sys.stdout.flush()
def workerGetPriceData(q):
    while True:
        getPriceData(q.get(), q)
        #sys.stdout.write("{:>4}".format(q.qsize()))
        time.sleep(0.05)
        q.task_done()
def startTGetPriceData(nthreads, q):
    for i in range(nthreads):
        t = threading.Thread(target=workerGetPriceData, args=[q])
        t.daemon = True
        t.start()
def getAllPrices():
    cards = phppgadmin.query("SELECT c.name, s.name as set, c.idmkm, s.isfoil FROM scr_cards c LEFT JOIN (select s1.code, s1.name, s1.set_type, s1.digital, false as isfoil from scr_sets s1 union all select s2.code, s2.name, s2.set_type, s2.digital, true as isfoil from scr_sets s2 where code not in ('lea','leb','2ed','cei','ced','arn','atq','3ed','leg','sum','drk','fem','4ed','ice','chr','hml','all','rqs','mir','mgb','itp','vis','5ed','por','wth','tmp','sth','p02','exo','ugl','usg','ath','6ed','ptk','s99','brb','s00','btd','dkm','phpr') and not foil) s on c.set = s.code WHERE	NOT idmkm IS NULL AND NOT s.digital	AND s.set_type in ('archenemy','commander','conspiracy','core','duel_deck','expansion','from_the_vault','masterpiece','planechase','premium_deck','starter')")
    n = 1000
    # with open("output.csv", "w", newline='\n') as f:
    #     writer = csv.DictWriter(f, fieldnames=["idmkm", "price", "isfoil", "available", "seller", "itemlocation"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #     writer.writeheader()
    q = Queue()
    startTGetPriceData(6, q)
    for i in range((int)(len(cards) / n) + 1):
        print("i=",i)
        cardswprices = cards[i*n:i*n+n]
        try:
            for card in cardswprices:
                card["isFoil"] = True if card["isfoil"] == "TRUE" else False
                card["idLanguage"] = 1
                q.put(card)
            q.join()
        except KeyboardInterrupt:
            sys.exit(1)
        # a csv
        # with open("output.csv", "a", newline='\n') as f:
        #     writer = csv.DictWriter(f, fieldnames=["idmkm", "price", "isfoil", "available", "seller", "itemlocation"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        #     for card in cardswprices:
        #         for price in card["prices"]:
        #             writer.writerow({ "idmkm": card["idmkm"], "price": price["price"], "isfoil": card["isfoil"], "available": price["available"], "seller": price["seller"], "itemlocation": price["itemlocation"] })
        # a db
        sql = ""
        for card in cardswprices:
            for price in card["prices"]:
                sql += "('{}',{},{},{},'{}','{}'),".format(card["idmkm"], price["price"], card["isfoil"], price["available"], price["seller"].replace("'","''"), price["itemlocation"])
        if sql != "":
            affected = phppgadmin.execute("INSERT INTO mkm_cardprices(id,price,foil,available,seller,itemlocation) VALUES" + sql[:-1])
            print("Total prices inserted: {}".format(affected))
    # materialized view completa
    phppgadmin.execute("DROP MATERIALIZED VIEW mkm_cardpricesranked;CREATE MATERIALIZED VIEW mkm_cardpricesranked AS SELECT id, price, foil, available, seller, itemlocation, dense_rank() OVER (PARTITION BY id,foil ORDER BY price ASC),first_value(price) OVER (PARTITION BY id,foil ORDER BY price ASC),lead(price) OVER (PARTITION BY id,foil ORDER BY price ASC) FROM mkm_cardprices WITH DATA; ALTER TABLE mkm_cardpricesranked OWNER TO postgres;")
def asPostableArticle(article):
    return {
        "idProduct": article["idProduct"],
        "idLanguage": article["idLanguage"],
        "comments": article["comments"],
        "count": article["count"],
        "price": article["price"],
        "condition": article["condition"],
        "isFoil": "true" if article["isFoil"] else "false",
        "isSigned": "true" if article["isSigned"] else "false",
        "isPlayset": "true" if article["isPlayset"] else "false"
    }
def updateItemComment(stockitem):
    #"●▬▬▬▬๑۩ {} ۩๑▬▬▬▬▬●"
    #",.-~*´¨¯¨`*·~-.¸-[{}]-,.-~*´¨¯¨`*·~-.¸"
    #"(╯°□°）╯︵ ┻━┻ {}"
    if stockitem["price"] >= 15:
        comment = "[ Perfect Size and Bubble Envelope ]"
    elif stockitem["price"] / (4 if stockitem["isPlayset"] == "true" else 1) >= 3:
        comment = "[ Perfect Size ]"
    else:
        comment = "[ You Win ]"
    stockitem["comments"] = '-~*{}*~- from MTG(c) Judge'.format(comment)
def updateItemPrice(stockitem):
    minprices = { "Rare": 0.19, "Uncommon": 0.09, "Common": 0.05, "Mythic": 0.29, "Token": 0.05, "Special": 0.99 }
    undercut = 0.97
    if len(stockitem["prices"]) > 0:
        filter1 = []
        for price in stockitem["prices"]:
            # pasada 1 para encontrar los precios de espana
            if price["itemlocation"] == "Spain":
                filter1.append(price)
        if len(filter1) == 0:
            filter1 = stockitem["prices"]
        count = (4 if stockitem["isPlayset"] else stockitem["count"])
        filter2 = []
        while len(filter2) == 0:
            #TODO: Considerar si esto es bien o mal, dado que es un factor limitante en la venta, al filtrar tb por location
            #pasada 2 para encontrar los que tienen count >= mi stock
            for price in filter1:
                if price["available"] >= count:
                    filter2.append(price)
            count -= 1
        stockitem["price"] = round(filter2[0]["price"] * undercut, 2)
    else:
        stockitem["price"] = (float)(input("Introduce precio para {}{} [{}]: ".format(stockitem["product"]["name"], "*" if stockitem["isFoil"] else "", stockitem["product"]["expansion"])))
    stockitem["price"] = max(stockitem["price"], minprices[stockitem["rarity"]])
    if stockitem["isPlayset"]:
        stockitem["price"] *= 4
def getItemPrices(stock):
    q = Queue()
    startTGetPriceData(6, q)
    for stockitem in stock:
        q.put(stockitem)
    q.join()
def deleteStock(stock):
    if len(stock) > 0:
        articles = []
        for stockitem in stock:
            articles.append({ "idArticle": stockitem["idArticle"], "count": stockitem["count"] })
        mkm.stock_management.delete_stock( data = { "article": articles } )
def postStock(stock):
    # ESTA MOVIDA ERA PARA OBTENER TODOS LOS PRECIOS DE MIS CARTAS
    # q = Queue()
    # startTGetPriceData(6, q)
    # for card in cards:
    #     if "idmkm" in card:
    #         q.put(card)
    # sys.stdout.write("Obteniendo precios mkm...")
    # q.join()
    # print("FIN")
    # # resumen
    # sum = 0
    # num = 0
    # for card in cards:
    #     if "idmkm" in card:
    #         if len(card["prices"]) > 0:
    #             sum += card["count"] * card["prices"][0]["price"]
    #             num += 1
    #         else:
    #             print("NOPRECIOS", card["name"], card["set"], card["idLanguage"], card["isFoil"])
    #     else:
    #         print("NOLINK", card["name"], card["set"])
    # print(sum, num)
    #
    currentstock = mkm.stock_management.get_stock().json()["article"]
    isUpdate = False
    if stock is None:
        # TODO: esto no funciona, dado que me he cargado el idarticle del postablearticle
        # obtener stock actual para actualizarlo
        isUpdate = True
        master = getMasterData()
        stock = currentstock
        for stockitem in stock:
            for m in master:
                if m["idProduct"] == stockitem["idProduct"]:
                    stockitem["website"] = m["website"]
                    break
            stockitem = asPostableArticle(stockitem)
    getItemPrices(stock)
    articles = []
    for stockitem in stock:
        updateItemPrice(stockitem)
        updateItemComment(stockitem)
        articles.append(asPostableArticle(stockitem))
    sys.stdout.write("Updating stock...")
    sys.stdout.flush()
    if isUpdate:
        mkm.stock_management.put_stock(data = { "article": articles })
    else:
        deleteStock(currentstock)
        mkm.stock_management.post_stock(data = { "article": articles })
    sys.stdout.write("OK\n")
