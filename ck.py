import threading
from queue import Queue
import time
from lxml import html
import requests
import re
import math
import os
import codecs
import phppgadmin
import pdb
import csv

class FileExpired(Exception):
    pass

class CardPrice:
	def __init__(self, price=0, available=0, condition=0, foil=False):
		self.price = price
		self.available = available
		#condition:NM=1,EX=2,VG=3,G=4
		self.condition = condition
		self.foil = foil

class Card:
	def __init__(self, id=0, name='', foil=False):
		self.id = id
		self.name = name
		self.foil = foil
		self.prices = []

class CardPage:
	def __init__(self, edition=None, foil=False, page=1):
		self.edition = edition
		self.foil = foil
		self.page = page

class Edition:
	def __init__(self, id=0, name='', url=''):
		self.id=id
		self.name=name
		self.url=url
		self.cards = []

exectime = time.time()

editions = []
try:
    dbeditions = phppgadmin.query("select id, name, url from ck_editions")
    #dbeditions = phppgadmin.query("select id, name, url from ck_editions where name = 'Zendikar'")
except:
    print ("Using cached editions")
    dbeditions = []
    with open("__offlinecache__/ck/editions.csv") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="|")
        for row in reader:
            dbeditions.append(row)

for edition in dbeditions:
    editions.append(Edition(edition["id"], edition["name"], edition["url"]))

sales = []

def getCards(page):
	cards = []
	tree = html.fromstring(page)
	cardshtml = tree.xpath('//div[@class="productItemWrapper productCardWrapper "]')
	for cardhtml in cardshtml:
		cardinfo = cardhtml.xpath('.//span[@class="productDetailTitle"]/a')[0]
		#cardinfo.attrib["href"] <- url carta
		isfoil = len(cardhtml.xpath('.//div[@class="productDetailSet"]/div[@class="foil"]')) > 0
		card = Card(0, cardinfo.text, isfoil)
		cardprices = cardhtml.xpath('.//form[@class="addToCartForm"]')
		for cardprice in cardprices:
			card.id = cardprice.xpath('.//input[@class="product_id"]')[0].attrib["value"];
			price = cardprice.xpath('.//span[@class="stylePrice"]')[0].text_content().replace("$", "").replace("\n", "").strip();
			saleprice = re.search(rSale, price)
			if not saleprice is None:
				sales.append("{}{} {}".format(cardinfo.text, " FOIL" if isfoil else "", price))
				price = saleprice.group(1)
			available = cardprice.xpath('.//input[@class="maxQty"]')[0].attrib["value"];
			condition = cardprice.xpath('.//input[@class="style"]')[0].attrib["value"];
			card.prices.append(CardPrice(price, available, condition, isfoil));
		cards.append(card)
	return cards

lock = threading.Lock()

cpp = 60
rCount = 'resultsHeader">.*?of (\d*) results'
rSale = "Sale (.*)"

cachedir = '__mycache__/ck'

if not os.path.exists(cachedir):
	os.makedirs(cachedir)

fileexpirationtime = 12 * 60 * 60

def do_work(cardpage):
    print(cardpage.edition.name, cardpage.page, "(foil)" if cardpage.foil else "")

    directory = "{}/{}".format(cachedir, cardpage.edition.name.replace(":",""))
    filename = "{}/{}{}.html".format(directory, "foil" if cardpage.foil else "", cardpage.page)
    try:
        st = os.stat(filename)
        if (exectime - st.st_ctime > fileexpirationtime):
            raise FileExpired()
        else:
            f = codecs.open(filename, "r", "utf-8")
            data = f.read()
            f.close()
    except (IOError, FileExpired):
        page = requests.get("{}?page={}&filter%5Bipp%5D={}".format(cardpage.edition.url + ("/foils" if cardpage.foil else ""), cardpage.page, cpp))
        data = page.text
        f = codecs.open(filename, "w", "utf-8")
        f.write(data)
        f.close()

    if cardpage.page == 1:
        items = (int)(re.search(rCount, data).group(1))
        paget = math.ceil(items / cpp)
        for pagen in range(2, paget + 1):
            q.put(CardPage(cardpage.edition, cardpage.foil, pagen))

	# parsear html en busca de las cartas
    cards = getCards(data)
	# anadir cartas a la edition
    cardpage.edition.cards.extend(cards)

def worker():
	while True:
		item = q.get()
		do_work(item)
		q.task_done()

# coger los precios de las cartas foil y meterlos en la carta normal
def groupPrices(edition):
	for i, foilcard in reversed(list(enumerate(edition.cards))):
		if (foilcard.foil):
			#buscar la correspondiente no foil
			for normalcard in edition.cards:
				if (not normalcard.foil and normalcard.name == foilcard.name):
					normalcard.prices.extend(foilcard.prices)
					edition.cards.pop(i)
					break

def saveData(edition):
	cardsql = "INSERT INTO ck_cards(id,name,edition) VALUES"
	pricesql = "INSERT INTO ck_cardprices(card,edition,foil,price,available,condition) VALUES"
	for card in edition.cards:
		cardname = card.name.replace("'","''")
		cardsql = cardsql + "({},'{}',{}),".format(card.id, cardname, edition.id)
		for price in card.prices:
			pricesql = pricesql + "({},{},{},{},{},'{}'),".format(card.id, edition.id, "true" if price.foil else "false", price.price, price.available, price.condition)
	editiondir = "{}/{}".format(cachedir, edition.name.replace(":",""))
	cardsfile = "{}/cards.sql".format(editiondir)
	pricesfile = "{}/prices.sql".format(editiondir)
	with open(cardsfile, "w", encoding="utf8") as f:
		f.write(cardsql[:-1])
	with open(pricesfile, "w", encoding="utf8") as f:
		f.write(pricesql[:-1])

	phppgadmin.execute(cardsql[:-1])
	#phppgadmin.execute(pricesql[:-1])

q = Queue()
for i in range(10):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

start = time.perf_counter()

for edition in editions:
	editiondir = "{}/{}".format(cachedir, edition.name.replace(":",""))
	if not os.path.exists(editiondir):
		with lock:
			os.makedirs(editiondir)
	q.put(CardPage(edition))
	q.put(CardPage(edition, True))

q.join()

print("Finished parsing\n")

for edition in editions:
	groupPrices(edition)
	print(edition.name, len(edition.cards))
	saveData(edition)

print("Sales:", sales)
print('time:',time.perf_counter() - start)

#select 'editions.append(Edition('||cast(e.id as varchar)||','||chr(34)||e.name||chr(34)||','||chr(34)||e.url||chr(34)||'))' from ck_editions e
#select id, name,setcode,sum(p.available) available,min(price) pricemin from mkm_cards c inner join mkm_cardprices p on c.id = p.cardid group by id,name,setcode order by available
