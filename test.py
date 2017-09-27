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
editions.append(Edition(1, "aaaa", "http://xxxxx"))

def do_work(cardpage):
    cardpage.edition.cards.append("test")

def worker():
	while True:
		item = q.get()
		do_work(item)
		q.task_done()

q = Queue()
for i in range(10):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

for edition in editions:
    q.put(CardPage(edition))
    q.put(CardPage(edition, True))

q.join()

print(editions[0].cards)
