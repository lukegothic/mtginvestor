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

threshold = 0.4
cards = phppgadmin.query("select * from scr_cards where not idmkm is null")
for c in cards:
    #print(c["idmkm"])
    for foil in range(0, 2):
        foilsql = "NOT " if foil == 0 else ""
        sql = "select price from mkm_cardprices where edition || '/' || card = '{}' and {}foil and (select sum(price)/2 from (select price from mkm_cardprices where edition || '/' || card = '{}' and {}foil order by price limit 2) t) - price > price * {} and price >= 0.25 order by price limit 1".format(c["idmkm"], foilsql, c["idmkm"], foilsql, threshold / 2)
        #print(sql)
        result = phppgadmin.query(sql)
        if len(result) > 0:
            print("{} {} => {}e".format(c["idmkm"], "NORMAL" if foil == 0 else "FOIL", result[0]["price"]))
