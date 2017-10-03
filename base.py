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
class Deckbox:
    cachedir = "{}/deckbox/{}".format(basecachedir, "{}")
    def inventory():
        cachedir = Deckbox.cachedir.format("inventory")
        req = requests.get("https://deckbox.org/sets/export/125700?format=csv&f=&s=&o=&columns=Image%20URL")
        if not os.path.exists(cachedir):
            os.makedirs(cachedir)
        filename = "{}/{}.csv".format(cachedir, time.strftime("%Y%m%d_%H%M%S"));
        with open(filename, "w") as f:
            f.write(req.text);
        inventory = []
        reID = "(\d*).jpg$"
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
            #TODO: integrar con proceso de solicitud de ediciones!
            pass
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
                    name = cardhtml.xpath(".//span[@class='productDetailTitle']/text()")[0]
                    edition = cardhtml.xpath(".//div[@class='productDetailSet']/text()")[0]
                    edition = re.search(reEdition, edition).group(1).strip()
                    editionid = None
                    # traducimos nombre de edicion a id
                    for e in editions:
                        if (e["name"] == edition):
                            editionid = e["id"]
                            break
                    if not editionid is None:
                        edition = editionid
                    else:
                        print("Edicion no encontrada", edition, name)
                        edition = 0
                    price = "{}.{}".format(pricewrapper.xpath(".//div[@class='usdSellPrice']/span[@class='sellDollarAmount']")[0].text_content().replace(",",""), pricewrapper.xpath(".//div[@class='usdSellPrice']/span[@class='sellCentsAmount']")[0].text_content())
                    price = round((float)(price) * usdeur_rate, 2)
                    # credit = "{}.{}".format(pricewrapper.xpath(".//div[@class='creditSellPrice']/span[@class='sellDollarAmount']")[0].text_content().replace(",",""), pricewrapper.xpath(".//div[@class='creditSellPrice']/span[@class='sellCentsAmount']")[0].text_content())
                    # el credit se puede sacar multiplicando por 1.3
                    maxQty = pricewrapper.xpath('.//form/input[@class="maxQty"]')[0].attrib["value"];
                    foil = len(cardhtml.xpath(".//div[@class='foil']")) > 0
                    #TODO: algunas veces se meten repetidas (mirar tokens)
                    inventorycard = None
                    for card in buylist:
                        if (card.name == name and card.edition == edition):
                            inventorycard = card
                            break
                    if (inventorycard is None):
                        inventorycard = InventoryCard(id, name, edition)
                        buylist.append(inventorycard)
                    inventorycard.entries.append(CardDetails(price, maxQty, foil, "en", "NM"))
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

        #TODO: CALCULAR CONVERSION AHORA O MEJOR DESPUES????
        sys.stdout.write("Obteniendo rate USD -> EUR...")
        sys.stdout.flush()

        req = requests.get("http://finance.yahoo.com/d/quotes.csv?f=l1d1t1&s=USDEUR=X")
        usdeur_rate = req.text.split(",")

        with open("{}/usdeur_rate_{}_{}.txt".format(basecachedir, usdeur_rate[1].replace("/", "-").replace('"', ""), usdeur_rate[2].replace("\n", "").replace(":", "").replace('"', "")), "w", encoding="utf8") as f:
            f.write(usdeur_rate[0])
            usdeur_rate = (float)(usdeur_rate[0])

        sys.stdout.write("OK [1 Dollar = {} Euro]".format(usdeur_rate))
        print("")

        baseurl = "https://www.cardkingdom.com/purchasing/mtg_singles?filter%5Bipp%5D=100&filter%5Bsort%5D=name&filter%5Bsearch%5D=mtg_advanced&filter%5Bname%5D=&filter%5Bcategory_id%5D=0&filter%5Bfoil%5D=1&filter%5Bnonfoil%5D=1&filter%5Bprice_op%5D=&filter%5Bprice%5D=&page="
        reEdition = "(.*)\("
        lock = threading.Lock()

        buylist = []
        sys.stdout.write("Obteniendo ediciones CK...")
        sys.stdout.flush()
        editions = CK.getEditions()
        sys.stdout.write("OK [{} ediciones]".format(len(editions)))
        print("")

        q = Queue()
        for i in range(10):
        	t = threading.Thread(target=worker)
        	t.daemon = True
        	t.start()

        start = time.perf_counter()

        npages = 254

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
    def store():
        pass

class MKM:
    baseurl = "https://www.magiccardmarket.eu"
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
            page = requests.get(MKM.baseurl + "/Expansions")
            tree = html.fromstring(page.text)
            xpatheditions = tree.xpath("//a[@class='alphabeticExpansion']")
            for edition in xpatheditions:
                relativeurl = edition.attrib["href"]
                editions.append({
                    "id": relativeurl.replace("/Expansions/", ""),
                    "name": edition.xpath("./div[@class='yearExpansionName']/text()")[0],
                    "url": MKM.baseurl + relativeurl
                })
            if not os.path.exists(offlinecachedir):
                os.makedirs(offlinecachedir)
            sql = "INSERT INTO mkm_editions(id,name,url) VALUES"
            with open(offlinecachefile, "w", newline='\n') as f:
                writer = csv.DictWriter(f, fieldnames=["id", "name", "url"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                for edition in editions:
                    writer.writerow({ "id": edition["id"], "name": edition["name"], "url": edition["url"] })
                    sql += "('{}','{}','{}'),".format(edition["id"], edition["name"].replace("'", "''"), edition["url"])
            sql = sql[:-1]
            #TODO: Actualizar PG a 9.5++
            #sql += " ON CONFLICT (id) DO UPDATE SET name = excluded.name, url = excluded.url"
            phppgadmin.execute(sql)
        return editions
    def getCards():
        pass
