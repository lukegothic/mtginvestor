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

class CardPrice:
	def __init__(self, price=0, available=0, condition=0):
		self.price = price
		self.available = available
		#condition:NM=1,EX=2,VG=3,G=4
		self.condition = condition
class Card:
	def __init__(self, id=0, name='', url=''):
		self.id = id
		self.name = name
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

editions = []
dbeditions = phppgadmin.query("select id, name, url from ck_editions where name = 'Zendikar'")
for edition in dbeditions:
	editions.append(Edition(edition["id"], edition["name"], edition["url"]))

sales = []

def getCards(page):
	cards = []
	tree = html.fromstring(page)
	cardshtml = tree.xpath('//div[@class="productItemWrapper productCardWrapper "]')
	for cardhtml in cardshtml:
		cardinfo = cardhtml.xpath('.//span[@class="productDetailTitle"]/a')[0]
		card = Card(0, cardinfo.text, cardinfo.attrib["href"])
		cardprices = cardhtml.xpath('.//form[@class="addToCartForm"]')
		for cardprice in cardprices:
			card.id = cardprice.xpath('.//input[@class="product_id"]')[0].attrib["value"];
			price = cardprice.xpath('.//span[@class="stylePrice"]')[0].text_content().replace("$", "").replace("\n", "").strip();
			saleprice = re.search(rSale, price)
			if not saleprice is None:
				price = saleprice.group(1)
				sales.append(cardinfo.text)
			available = cardprice.xpath('.//input[@class="maxQty"]')[0].attrib["value"];
			condition = cardprice.xpath('.//input[@class="style"]')[0].attrib["value"];
			card.prices.append(CardPrice(price, available, condition));
		cards.append(card)
	return cards

lock = threading.Lock()

cpp = 60
rCount = 'resultsHeader">.*?of (\d*) results'
rSale = "Sale (.*)"

cachedir = '__mycache__/ck'

if not os.path.exists(cachedir):
	os.makedirs(cachedir)

def do_work(edition):
	print(edition.name)

	directory = "{}/{}".format(cachedir, edition.name.replace(":",""))
	filename = "{}/{}{}.html".format(directory, "foil" if edition.foil else "", edition.page)

	try:
		f = codecs.open(filename, "r", "utf-8")
		#todo: invalidar cache si ha pasado 1 dia os.path.getmtime(path)
		data = f.read()
		f.close()
	except IOError:
		page = requests.get("{}?page={}&filter%5Bipp%5D={}".format(edition.url, edition.page, cpp))
		data = page.text
		f = codecs.open(filename, "w", "utf-8")
		f.write(data)
		f.close()

	if edition.page == 1:
		items = (int)(re.search(rCount, data).group(1))
		paget = math.ceil(items / cpp)
		for pagen in range(2, paget + 1):
			q.put(Edition(edition.id, edition.name, edition.url, edition.foil, pagen))

	cards = getCards(data)
	with lock:
		fcards = open("{}/cards.sql".format(directory), "a", encoding="utf8")
		fprices = open("{}/prices.sql".format(directory), "a", encoding="utf8")
		for card in cards:
			cardname = card.name.replace("'","''")
			fcards.write("({},'{}',{}),".format(card.id, cardname, edition.id))
			for price in card.prices:
				fprices.write("({},{},{},{},{},'{}'),".format(card.id, edition.id, "true" if edition.foil else "false", price.price, price.available, price.condition))
		fcards.close()
		fprices.close()

def worker():
	while True:
		item = q.get()
		do_work(item)
		q.task_done()

def createStructure(edition):
	editiondir = "{}/{}".format(cachedir, edition.name.replace(":",""))
	cardsfile = "{}/cards.sql".format(editiondir)
	pricesfile = "{}/prices.sql".format(editiondir)
	if not os.path.exists(editiondir):
		with lock:
			os.makedirs(editiondir)
	f = open(cardsfile, "w", encoding="utf8")
	f.write("INSERT INTO ck_cards(id,name,edition) VALUES")
	f.close()
	f =	open(pricesfile, "w", encoding="utf8")
	f.write("INSERT INTO ck_cardprices(card,edition,foil,price,available,condition) VALUES")
	f.close()

q = Queue()
for i in range(10):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

start = time.perf_counter()

for edition in editions:
	createStructure(edition)
	q.put(CardPage(edition))
    q.put(CardPage(edition, True))

q.join()

print('time:',time.perf_counter() - start)

#select 'editions.append(Edition('||cast(e.id as varchar)||','||chr(34)||e.name||chr(34)||','||chr(34)||e.url||chr(34)||'))' from ck_editions e
#select id, name,setcode,sum(p.available) available,min(price) pricemin from mkm_cards c inner join mkm_cardprices p on c.id = p.cardid group by id,name,setcode order by available
