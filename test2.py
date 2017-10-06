from base import CK
from base import MKM
from base import Gatherer
from queue import Queue
import threading
import requests
from base import Proxy
import phppgadmin
import sys
from lxml import html
import time
import csv

editions = Gatherer.getEditions()
with open("potential.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "edition", "foil", "ck", "mkm", "diff", "pct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
# TODO: DEFINIR LO QUE ES POTENTIAL ---> usar cada seller de manera particular para no tener que buscarlo a mano
for edition in editions:
    if not edition["code_ck"] == 'NULL' and not edition["code_mkm"] == 'NULL':
        cards = phppgadmin.query("select ck.name, mkm.edition, ck.foil, ck.price as ck, mkm.price as mkm, ck.price - mkm.price as diff, ck.price / mkm.price as pct from (select edition, name, foil, price * 0.8 as price, count as available from ck_buylist where edition = {}) CK left join (select c.edition, c.name, p.foil, min(price) price, sum(available) from mkm_cards c left join mkm_cardprices p on c.edition = p.edition and c.id = p.card where c.edition = '{}' group by c.name, c.edition, p.foil) mkm on lower(ck.name) = lower(mkm.name) and ck.foil = mkm.foil where ck.price - mkm.price >= 1 and ck.price / mkm.price >= 1.2".format(edition["code_ck"], edition["code_mkm"]))
        with open("potential.csv", "a") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "edition", "foil", "ck", "mkm", "diff", "pct"], delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for card in cards:
                writer.writerow(card)
