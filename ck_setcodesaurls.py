import threading
from queue import Queue
from lxml import html
import requests
import phppgadmin
import os

class Set:
	def __init__(self, id="0", name="", url=""):
		self.id = id
		self.name = name
		self.url = url

baseurl = "http://www.cardkingdom.com/catalog/view/"
page = requests.get("http://www.cardkingdom.com/catalog/magic_the_gathering/by_az")
tree = html.fromstring(page.text)

sets = []
for link in tree.xpath("//a[contains(@href,'" + baseurl + "')]"):
	sets.append(Set(link.attrib["href"].replace(baseurl, ""), link.text))

print("Total sets:", len(sets))

cachedir = '__mycache__/ck/setcodesaurls'
if not os.path.exists(cachedir):
	os.makedirs(cachedir)

def do_work(data):
	url = baseurl + data.id
	page = requests.get(url)
	data.url = page.url
	print("Set procesado:", data.name)

def worker():
	while True:
		do_work(q.get())
		q.task_done()

q = Queue()
for i in range(10):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

for s in sets:
	q.put(s)

q.join();

sql = "DELETE FROM ck_editions;INSERT INTO ck_editions(id, name, url) VALUES"
for s in sets:
	sql = sql + "({},'{}','{}'),".format(s.id, s.name.replace("'", "''"), s.url)

sql = sql[:len(sql) - 1]

phppgadmin.execute(sql)

print("Done")
