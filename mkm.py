# -*- coding: utf-8 -*-
class CardPrice:
	def __init__(self, price=0, available=0, foil=False):
		self.price = price
		self.available = available
		self.foil = foil
class Card:
	def __init__(self, id=0, code='', edition=''):
		self.id = id
		self.code = code
		self.edition = edition
		self.prices = []

from lxml import html
import requests
import re
import codecs

cards = []
cards.append(Card(52582,"Disallow","Aether+Revolt"))
cards.append(Card(81839,"Whir+of+Invention","Aether+Revolt"))


productFilter = data = { "productFilter[sellerRatings][]": ["1", "2"], "productFilter[idLanguage][]": [1], "productFilter[condition][]": ["MT", "NM"], "productFilter[isFoil]": "Y" }
rBody = '<tbody id=\"articlesTable\">(.*?)<\/tbody>'
rRow = '<tr.*?td class="Price.*?>.*?>.*?>(.*?)<\/div>.*?td class="Available.*?>(.*?)<\/td>.*?\/tr>'
rPPU = '\(PPU: (.*?)\)'
f = open("mkm_prices.sql", "w")
f.close()
for card in cards:
	print("{}[{}]".format(card.code, card.edition))
	filename = "mkmprices/{}_{}.html".format(card.edition, card.code)
	try:
		f = codecs.open(filename, "r", "utf-8")
		data = f.read()
		f.close()
	except IOError:
		page = requests.post("https://www.magiccardmarket.eu/Products/Singles/" + card.edition + "/" + card.code, productFilter)
		data = page.text
		f = codecs.open(filename, "w", "utf-8")
		f.write(data)
		f.close()

	tree = html.fromstring(data)
	for row in tree.xpath('//tbody[@id="articlesTable"]/tr[not(@class)]'):
		price = row.xpath(".//td[contains(@class,'st_price')]")[0].text_content().replace(",",".").replace("€","")
		available = row.xpath(".//td[contains(@class,'st_ItemCount')]")[0].text_content()
		ppu = re.search(rPPU, price)
		if not ppu is None:
			price = ppu.group(1)
			available = "4"
		card.prices.append(CardPrice(price, available))
	if len(card.prices) > 0:
		print("Encontrados {} precios".format(len(card.prices)))
		f = open("mkm_prices.sql", "a")
		f.write("--{}[{}]\n".format(card.code, card.edition))
		for cp in card.prices:
			f.write("INSERT INTO mkm_cardprices(cardid,price,foil,available) VALUES({0},{1},true,{2});\n".format(card.id, cp.price, cp.available))
		f.close()
	else:
		print("Precios no encontrados")

#select 'cards.append(Card('||cast(mkm.id as varchar)||','||chr(34)||mkm.code||chr(34)||','||chr(34)||mkm.setcode||chr(34)||'))' from edhtocardusage c left join mkm_cards mkm on c.name = mkm.name where quantity > 2000 order by setcode
#select id, name,editionid,sum(p.available) available,min(price) pricemin from mkm_cards c inner join mkm_cardprices p on c.id = p.cardid group by id,name,editionid order by available

cachedir = "cache/mkm/prices"

if not os.path.exists(cachedir):
	os.makedirs(cachedir)

lock = threading.Lock()

def do_work(url):
	#analizar url y determinar que hacer con sus contenidos
	filename = "ck/{}/{}{}.html".format(edition.name.replace(":",""), "foil" if edition.foil else "", edition.page)
	try:
		f = codecs.open(filename, "r", "utf-8")
		#todo: invalidar cache si ha pasado 1 dia os.path.getmtime(path)
		data = f.read()
		f.close()
	except IOError:
		page = requests.get("{}?page={}&filter%5Bipp%5D={}".format(edition.url, edition.page, cpp))
		data = page.text
		directory = "ck/{0}".format(edition.name.replace(":",""))
		with lock:
			if not os.path.exists(directory):
				os.makedirs(directory)
		f = codecs.open(filename, "w", "utf-8")
		f.write(data)
		f.close()

def worker():
	while True:
		item = q.get()
		do_work(item)
		q.task_done()

q = Queue()

page = requests.get("https://www.magiccardmarket.eu/Expansions")
tree = html.fromstring(page.text)
editions = tree.xpath("//a[@class='alphabeticExpansion']")
for edition in editions:
	print(edition.attrib["href"].replace("Expansions","Products/Singles"))
	#q.put(edition.attrib["href"].replace("Expansions","Products/Singles"))

'''
https://www.magiccardmarket.eu/Products/Singles/Alara+Reborn
https://www.magiccardmarket.eu/Products/Singles/Alara+Reborn?resultsPage=4
https://www.magiccardmarket.eu/Products/Singles/Alara+Reborn/Talon+Trooper
'''
'''
for i in range(6):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

start = time.perf_counter()

q.join()
'''
print('time:',time.perf_counter() - start)
