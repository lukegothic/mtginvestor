from base import CK
from base import MKM
from base import Gatherer
from queue import Queue
import threading
import requests
from base import Proxy
from base import Proxy2
import phppgadmin
import sys
from lxml import html
import time

proxies = Proxy2.getSecure()

def do_work(proxy):
    try:
        fullip = "http://{}:{}".format(proxy["ip"], proxy["port"])
        req = requests.get("https://www.magiccardmarket.eu/", proxies = { "http": fullip, "https": fullip }, timeout = 3)
        with open(proxy["ip"], "w") as f:
            print(req, req.text, req.status_code)
            f.write(req.text)
    except:
        print("Proxy {} not working".format(proxy["ip"]))
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

for proxy in proxies:
    q.put(proxy)

q.join()
