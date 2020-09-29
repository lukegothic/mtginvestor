import json, requests, time,threading, sys
from queue import Queue
from endpoints import scryfall
cards = scryfall.bulk_cards("default")
cjson = {}

def do_work(info):
    sys.stdout.write("Restantes: %d   \r" % q.qsize())
    sys.stdout.flush()
    r = requests.get(info["art"])
    with open("output/crops/{}.jpg".format(info["ide"]), "wb") as f:
        f.write(r.content)
def worker():
    while True:
        do_work(q.get())
        q.task_done()
q = Queue()
for i in range(8):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()
for c in cards:
    art = cjson[c["id"]] = (c["image_uris"]["art_crop"] if "image_uris" in c else c["card_faces"][0]["image_uris"]["art_crop"])
    q.put({"art":art, "ide": c["id"]})
q.join()

