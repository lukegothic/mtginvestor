import csv
import requests
import os
import time
import re
import threading
from queue import Queue
from lxml import html
import sys
import phppgadmin
import math
import copy

basecachedir = "__mycache__"

class FileExpired(Exception):
    pass
# base
class Card:
    def __init__(self, id='',name='',edition=''):
        self.id=id
        self.name=name
        self.edition=edition
    def __iter__(self):
        return { "id": self.id, "name": self.name, "edition": self.edition }
# detalle
class CardDetails:
    def __init__(self, price=0,count=0,foil=False,language='en',condition='NM',seller='',location=''):
        self.price = price
        self.count = count
        self.foil = foil
        self.language = language
        self.condition = condition
        self.seller = seller
        self.location = location
# una carta de un inventario (varias entradas de tipo CardDetails)
class InventoryCard(Card):
    def __init__(self, id='',name='',edition=''):
        super().__init__(id, name, edition)
        self.entries = []
# una carta con inventario
class PriceCard(Card):
    def __init__(self, id='',name='',edition='',details=None):
        super().__init__(id, name, edition)
        self.price = details.price
        self.count = details.count
        self.foil = details.foil
        self.language = details.language
        self.condition = details.condition
    def todict(self):
        return { "id": self.id, "name": self.name, "edition": self.edition, "price": self.price, "count": self.count, "foil": "foil" if self.foil else "", "language": self.language, "condition": self.condition }
# CLASE APARTE
class Proxy:
    url = "https://free-proxy-list.net/"
    def getAll():
        req = requests.get(Proxy.url)
        tree = html.fromstring(req.text)
        proxies = tree.xpath("//table[@id='proxylisttable']/tbody/tr")
        plist = []
        for proxy in proxies:
            plist.append({
                "ip": proxy.xpath("./td[1]/text()")[0],
                "port": proxy.xpath("./td[2]/text()")[0],
                "anonymity": proxy.xpath("./td[5]/text()")[0],
                "secure": proxy.xpath("./td[7]/text()")[0] == "yes"
            })
        return plist
    def getSecure():
        proxies = Proxy.getAll()
        secure = []
        for proxy in proxies:
            if proxy["secure"]:
                secure.append(proxy)
        return secure
class ExchangeRate:
    def get(symbol):
        #TODO: CALCULAR CONVERSION AHORA O MEJOR DESPUES????
        sys.stdout.write("Obteniendo rate {}...".format(symbol))
        sys.stdout.flush()

        #req = requests.get("http://finance.yahoo.com/d/quotes.csv?f=l1d1t1&s=USDEUR=X")
        req = requests.get("http://finance.yahoo.com/d/quotes.csv?f=l1d1t1&s={}".format(symbol))
        rate = req.text.split(",")

        with open("{}/rate_{}_{}_{}.txt".format(basecachedir, symbol, rate[1].replace("/", "-").replace('"', ""), rate[2].replace("\n", "").replace(":", "").replace('"', "")), "w", encoding="utf8") as f:
            f.write(rate[0])
            rate = (float)(rate[0])

        sys.stdout.write("OK [1 = {}]".format(rate))
        print("")
        return rate
class Deckbox:
    cachedir = "{}/deckbox/{}".format(basecachedir, "{}")
    def inventory(usecached):
        cachedir = Deckbox.cachedir.format("inventory")
        sys.stdout.write("Obteniendo inventario {}...".format("lukegothic"))
        sys.stdout.flush()

        req = requests.get("https://deckbox.org/sets/export/125700?format=csv&f=&s=&o=&columns=Image%20URL")
        if not os.path.exists(cachedir):
            os.makedirs(cachedir)
        filename = "{}/{}.csv".format(cachedir, time.strftime("%Y%m%d_%H%M%S"));
        with open(filename, "w") as f:
            f.write(req.text);
        inventory = []
        reID = "(\d*).jpg$"
        sys.stdout.write("OK")
        print("")
        with open(filename) as f:
            reader = csv.DictReader(f, delimiter=",", quotechar='"')
            for row in reader:
                id = re.search(reID, row["Image URL"]).group(1)
                inventorycard = None
                for card in inventory:
                    if (card.id == id):
                        inventorycard = card
                        break
                if (inventorycard is None):
                    inventorycard = InventoryCard(id, row["Name"], row["Edition"])
                    inventory.append(inventorycard)
                inventorycard.entries.append(CardDetails(0,(int)(row["Count"]),True if row["Foil"] == "foil" else False, row["Language"],row["Condition"]))
        return inventory
class CK:
    cachedir = "{}/ck/{}".format(basecachedir, "{}")
    def crawlEditions():
        def do_work(edition):
            sys.stdout.write("Ediciones restantes: %d   \r" % q.qsize())
            sys.stdout.flush()
            page = requests.get(edition["url"])
            edition["url"] = page.url
        def worker():
        	while True:
        		do_work(q.get())
        		q.task_done()
        q = Queue()
        for i in range(8):
        	t = threading.Thread(target=worker)
        	t.daemon = True
        	t.start()
        baseurl = "www.cardkingdom.com/catalog/view/"
        page = requests.get("http://www.cardkingdom.com/catalog/magic_the_gathering/by_az")
        tree = html.fromstring(page.text)
        editions = []
        for link in tree.xpath("//a[contains(@href,'" + baseurl + "')]"):
            #TODO: dejar de depender de IDs...por el bien de la humanidad
            href = link.attrib["href"]
            edition = { "id": href[href.rfind("/")+1:], "name": link.text.replace("'", "''"), "url": href }
            editions.append(edition)
            q.put(edition)
        q.join()
        print("")
        sql = "DELETE FROM ck_editions;INSERT INTO ck_editions(id,name,url) VALUES"
        for edition in editions:
            sql += "({},'{}','{}'),".format(edition["id"], edition["name"], edition["url"])
        print(" {} ediciones almacenadas".format(phppgadmin.execute(sql[:-1])))
        return editions
    def getEditions():
        editions = []
        try:
            editions = phppgadmin.query("select id, name, url from ck_editions")
        except:#TODO: capturar excepcion que corresponda
            print ("Using cached editions")
            editions = []
            with open("__offlinecache__/ck/editions.csv") as csvfile:
                reader = csv.DictReader(csvfile, delimiter="|")
                for row in reader:
                    editions.append(row)
        if (len(editions) == 0):
            CK.crawlEditions()
        return editions
    def buylist(writecsv=False):
        #TODO: numero dinamico de paginas
        print("==[ CK BUYLIST  ]==")
        def addCards(pagehtml):
            tree = html.fromstring(pagehtml)
            cardshtml = tree.xpath("//div[contains(@class,'itemContentWrapper')]")
            for cardhtml in cardshtml:
                pricewrapper = cardhtml.xpath(".//span[@class='stylePrice']")
                # si no tiene precio es una premium card de las que hay que preguntar precio
                if len(pricewrapper) == 1:
                    pricewrapper = pricewrapper[0]
                    id = pricewrapper.xpath('.//form/input[@class="product_id"]')[0].attrib["value"];
                    #name = cardhtml.xpath(".//span[@class='productDetailTitle']/text()")[0]
                    #edition = cardhtml.xpath(".//div[@class='productDetailSet']/text()")[0]
                    #edition = re.search(reEdition, edition).group(1).strip()
                    #editionid = None
                    # traducimos nombre de edicion a id
                    # for e in editions:
                    #     if (e["name"] == edition):
                    #         editionid = e["id"]
                    #         break
                    # if not editionid is None:
                    #     edition = editionid
                    # else:
                    #     print("Edicion no encontrada", edition, name)
                    #     edition = 0
                    price = "{}.{}".format(pricewrapper.xpath(".//div[@class='usdSellPrice']/span[@class='sellDollarAmount']")[0].text_content().replace(",",""), pricewrapper.xpath(".//div[@class='usdSellPrice']/span[@class='sellCentsAmount']")[0].text_content())
                    # el credit se puede sacar multiplicando por 1.3
                    maxQty = pricewrapper.xpath('.//form/input[@class="maxQty"]')[0].attrib["value"];
                    foil = len(cardhtml.xpath(".//div[@class='foil']")) > 0
                    #TODO: algunas veces se meten repetidas (mirar tokens)
                    # traducir id de la foil a la normal
                    if foil:
                        for translation in idtranslations:
                            if id == translation["foil"]:
                                id = translation["normal"]
                                break;
                    inventorycard = InventoryCard(id, "", "")
                    inventorycard.entries.append(CardDetails(price, maxQty, foil, "en", "NM"))
                    buylist.append(inventorycard)
        def do_work(page):
            sys.stdout.write("Paginas procesadas: %d%%   \r" % (page * 100 / npages))
            sys.stdout.flush()
            filename = "{}/page{}.html".format(cachedir, page)
            try:
            	f = open(filename, "r", encoding="utf8")
            	data = f.read()
            	f.close()
            except:
                page = requests.get("{}{}".format(baseurl, page))
                data = page.text
                with open(filename, "w", encoding="utf8") as f:
                    f.write(data)
            addCards(data)
        def worker():
        	while True:
        		item = q.get()
        		do_work(item)
        		q.task_done()

        today = time.strftime("%Y%m%d")

        cachedir = CK.cachedir.format("buylist/" + today)

        if not os.path.exists(cachedir):
        	os.makedirs(cachedir)

        baseurl = "https://www.cardkingdom.com/purchasing/mtg_singles?filter%5Bipp%5D=100&filter%5Bsort%5D=name&filter%5Bsearch%5D=mtg_advanced&filter%5Bname%5D=&filter%5Bcategory_id%5D=0&filter%5Bfoil%5D=1&filter%5Bnonfoil%5D=1&filter%5Bprice_op%5D=&filter%5Bprice%5D=&page="
        #reEdition = "(.*)\("
        lock = threading.Lock()

        buylist = []
        #sys.stdout.write("Obteniendo ediciones CK...")
        #sys.stdout.flush()
        #editions = CK.getEditions()
        idtranslations = phppgadmin.query("SELECT foil,normal FROM ck_idtranslator")
        #sys.stdout.write("OK [{} ediciones]".format(len(editions)))
        #print("")

        q = Queue()
        for i in range(10):
        	t = threading.Thread(target=worker)
        	t.daemon = True
        	t.start()

        start = time.perf_counter()

        npages = 258

        for p in range(1, npages):
        	q.put(p)

        q.join()

        print("Crawling finalizado          ")

        if (writecsv):
            print("Guardando .csv en disco...")

            filename = "{}/buylist.csv".format(cachedir);
            with open(filename, "w", newline='\n') as f:
                writer = csv.DictWriter(f, fieldnames=["id", "name", "edition", "price", "count", "foil", "language", "condition"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                for card in buylist:
                    for entry in card.entries:
                        writer.writerow({ "id": card.id, "name": card.name, "edition": card.edition, "price": entry.price, "count": entry.count, "foil": "true" if entry.foil else "false", "language": entry.language, "condition": entry.condition })

        print("==[     END     ]==")

        return buylist
    def inventory():
        pass
class MKM:
    baseurl = "https://www.cardmarket.com/en/Magic"
    cachedir = "{}/mkm/{}".format(basecachedir, "{}")
    maxthreads = 6
    def crawlEditions():
        page = requests.get(MKM.baseurl + "/Expansions")
        tree = html.fromstring(page.text)
        xpatheditions = tree.xpath("//a[@class='alphabeticExpansion']")
        for edition in xpatheditions:
            relativeurl = edition.attrib["href"]
            editions.append({
                "id": relativeurl.replace("/Expansions/", ""),
                "name": edition.xpath("./div[@class='yearExpansionName']/text()")[0],
                "url": MKM.baseurl + relativeurl.replace("/Expansions/", "/Products/Singles/"),
            })
        if not os.path.exists(offlinecachedir):
            os.makedirs(offlinecachedir)
        sql = "DELETE FROM mkm_editions;INSERT INTO mkm_editions(id,name,url) VALUES"
        with open(offlinecachefile, "w", newline='\n') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "url"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for edition in editions:
                writer.writerow({ "id": edition["id"], "name": edition["name"], "url": edition["url"] })
                sql += "('{}','{}','{}'),".format(edition["id"], edition["name"].replace("'", "''"), edition["url"])
        sql = sql[:-1]
        #TODO: Actualizar PG a 9.5++
        #sql += " ON CONFLICT (id) DO UPDATE SET name = excluded.name, url = excluded.url"
        print(phppgadmin.execute(sql))
        return editions
    def getEditions():
        editions = []
        offlinecachedir = "__offlinecache__/mkm"
        offlinecachefile = "{}/editions.csv".format(offlinecachedir)
        try:
            editions = phppgadmin.query("select id, name, url from mkm_editions")
        except: #TODO: capturar excepcion que corresponda
            try:
                with open(offlinecachefile) as csvfile:
                    reader = csv.DictReader(csvfile, delimiter="|")
                    for row in reader:
                        editions.append(row)
            except:
                pass
        if (len(editions) == 0):
            editions = MKM.crawlEditions()
        return editions
    def selectEdition():
        editions = MKM.getEditions()
        if len(sys.argv) == 2:
        	s = sys.argv[1]
        else:
        	for e in range(0, len(editions)):
        		edition = editions[e]
        		print("[{}] {}".format(e, edition["id"]))
        	s = input("Seleccione # o intro para todas: ")
        if s != "":
        	if s == "0":
        		return []
        	else:
        		s = s.split(",")
        		filterededitions = []
        		for e in s:
        			filterededitions.append(editions[(int)(e)])
        		return filterededitions
        else:
        	return editions
    def getCards():
        def do_work(edition):
            pagematch = re.match(rPage, edition["url"])
            if pagematch is None:
                page = 1
            else:
                page = (int)(pagematch.group(2)) + 1
            print("{} [{}]".format(edition["id"], page))
            editiondir = MKM.cachedir.format("cards/" + edition["id"])
            if not os.path.exists(editiondir):
                os.makedirs(editiondir)
            editionpagecache = "{}/{}.html".format(editiondir, page)
            try:
            	f = open(editionpagecache, "r", encoding="utf8")
            	data = f.read()
            	f.close()
            except IOError:
                resp = requests.get("{}{}sortBy=number&sortDir=asc&view=list".format(edition["url"], "?" if page == 1 else "&"))
                data = resp.text
                # Proteccion contra respuestas vacias, encolamos de nuevo la solicitud
                if data != "":
                    with open(editionpagecache, "w", encoding="utf8") as f:
                        f.write(data)
                else:
                    q.put(edition)
            if data != "":
                tree = html.fromstring(data)
                if page == 1:
                    # procesar resto de paginas de la edicion
                    total = tree.xpath("//span[@id='hitCountTop']/text()")
                    if len(total) == 1:
                        total = math.ceil((int)(total[0]) / cpp)
                        for pagen in range(2, total + 1):
                            q.put({ "id": edition["id"], "name": edition["name"], "url": "{}?resultsPage={}".format(edition["url"], pagen - 1) })
                # procesar cartas
                htmlcards = tree.xpath("//table[contains(@class,'MKMTable')]/tbody/tr");
                for c in htmlcards:
                    cardlinkelement = c.xpath("./td[3]/a")[0]
                    cardurl = "{}{}".format(MKM.baseurl, cardlinkelement.attrib["href"])
                    cardid = cardurl[cardurl.rfind("/")+1:]
                    cardname = cardlinkelement.text_content().replace("'","''")
                    cards.append(Card(cardid, cardname, edition["id"]))
        def worker():
            while True:
                do_work(q.get())
                q.task_done()
        cpp = 30
        rPage = "https:\/\/www.magiccardmarket.eu\/Products\/Singles\/(.*?)\?resultsPage=(\d*)"
        editions = MKM.selectEdition()
        cards = []
        q = Queue()
        for i in range(MKM.maxthreads):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
        for edition in editions:
            q.put(edition)
        q.join()
        return cards
    def getPrices(edition=None):
        def do_work(item):
            carddir = MKM.cachedir.format("prices/{}/{}".format(edition["id"], item["card"].id))
            try:
                if not os.path.exists(carddir):
                    os.makedirs(carddir)
            except:
                pass
            cardpagecache = "{}/{}.html".format(carddir, "foil" if item["foil"] else "normal")
            try:
                f = open(cardpagecache, "r", encoding="utf8")
                data = f.read()
                f.close()
            except IOError:
                if item["foil"]:
                    filter = copy.copy(productFilter)
                    filter["productFilter[isFoil]"] = "Y"
                else:
                    filter = productFilter
                try:
                    resp = requests.post("{}/Products/Singles/{}/{}".format(MKM.baseurl, item["card"].edition, item["card"].id), filter, headers={}, timeout = 10)
                    data = resp.text
                except:
                    data = ""
                # Proteccion contra respuestas vacias, encolamos de nuevo la solicitud
                if data != "":
                    with open(cardpagecache, "w", encoding="utf8") as f:
                        f.write(data)
                else:
                    print("Me tiran solicitud, relanzo en 10s")
                    q.put(item, True, 10)
            if data != "":
                tree = html.fromstring(data)
                for row in tree.xpath('//tbody[@id="articlesTable"]/tr[not(@class)]'):
                    itemlocation = row.xpath(".//td[@class='Seller']/span/span/span[@class='icon']")[0].attrib["onmouseover"]
                    itemlocation = re.search(reItemLocation, itemlocation).group(1)
                    seller = row.xpath(".//td[@class='Seller']/span/span/a")[0].attrib["href"].replace("/en/Magic/Users/", "")
                    price = row.xpath(".//td[contains(@class,'st_price')]")[0].text_content().replace(",",".").replace("€","")
                    available = row.xpath(".//td[contains(@class,'st_ItemCount')]")[0].text_content()
                    ppu = re.search(rPPU, price)
                    if not ppu is None:
                        price = ppu.group(1)
                        available = "4"
                    item["card"].entries.append(CardDetails((float)(price),(int)(available),True if item["foil"] else False, "en", "NM", seller, itemlocation))
            sys.stdout.write("Elementos restantes: %d   \r" % q.qsize())
            sys.stdout.flush()
        def worker():
            while True:
                do_work(q.get())
                time.sleep(0.05)
                q.task_done()
        if (edition is None):
            editions = MKM.selectEdition()
        else:
            editions = [edition]
        sql = "select c.id as id, c.name as name, c.edition as edition, e.type as type from editions e left join mkm_cards c on c.edition = e.code_mkm where not e.code_mkm is null"
        if (len(editions) == 1):
            sql += " AND c.edition = '{}'".format(editions[0]["id"])
        dbcards = phppgadmin.query(sql)
        q = Queue()
        for i in range(MKM.maxthreads):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
        cards = []
        productFilter = { "productFilter[sellerRatings][]": ["1", "2"], "productFilter[idLanguage][]": [1], "productFilter[condition][]": ["MT", "NM"] }
        rPPU = '\(PPU: (.*?)\)'
        reItemLocation = "'Item location: (.*)'"
        for dbcard in dbcards:
            card = InventoryCard(dbcard["id"], dbcard["name"], dbcard["edition"])
            cards.append(card)
            q.put({ "card": card, "foil": False })
            if dbcard["type"] == "3":
                q.put({ "card": card, "foil": True })
        q.join()
        print("==[     END     ]==   ")
        return cards
class Gatherer:
    def getEditions():
        return phppgadmin.query("SELECT code as id, name, code_ck, code_mkm FROM editions")
    def normalizeEditions():
        print("TOTAL", len(phppgadmin.query("SELECT code FROM editions")))
        print("CK UPDATES", phppgadmin.execute("UPDATE editions SET code_ck = ck.id FROM ck_editions ck WHERE lower(ck.name) = lower(editions.name)"))
        print("MKM UPDATES", phppgadmin.execute("UPDATE editions SET code_mkm = mkm.id FROM mkm_editions mkm WHERE lower(mkm.name) = lower(editions.name)"))
    def normalizeCards():
        pass
