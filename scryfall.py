import os
import re
import sys
import json
import requests
import phppgadmin

basedir = "__mycache__/scryfall"
if (not os.path.exists(basedir)):
    os.makedirs(basedir)

def process_sets():
    cachedir = "{}/sets".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    phppgadmin("DELETE FROM scr_sets")
    filete = "{}/sets.json".format(cachedir)
    try:
        with open(filete) as f:
            data = f.read()
    except:
        req = requests.get("https://api.scryfall.com/sets")
        data = page.text
        with open(filete, "w") as f:
            f.write(data)
    sets = json.loads(data)
    sql = "INSERT INTO scr_sets(code,name,set_type,released_at,block_code,block,parent_set_code,card_count,digital,foil,icon_svg_uri,search_uri) VALUES"
    for set in sets["data"]:
        sql += "('{}','{}','{}',{},{},{},{},{},{},{},'{}','{}'),".format(set["code"], set["name"].replace("'", "''"), set["set_type"], "'{}'".format(set["released_at"]) if "released_at" in set else "NULL", "'{}'".format(set["block_code"]) if "block_code" in set else "NULL", "'{}'".format(set["block"].replace("'", "''")) if "block" in set else "NULL", "'{}'".format(set["parent_set_code"]) if "parent_set_code" in set else "NULL", set["card_count"], set["digital"] if "digital" in set else "false", set["foil"] if "foil" in set else "false", set["icon_svg_uri"], set["search_uri"])
    print(phppgadmin.execute(sql[:-1]))
def process_cards():
    cachedir = "{}/cards".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    phppgadmin("DELETE FROM scr_cards")
    reIDMKM = "https:\/\/www\.magiccardmarket\.eu\/Products\/Singles\/(.*?)\?"
    reIDCK = "http:\/\/www\.cardkingdom\.com\/catalog\/item\/(\d*)?\?"
    page = 1
    while True:
        filete = "{}/{}.json".format(cachedir, page)
        try:
            with open(filete, encoding="utf-8") as f:
                data = f.read()
        except:
            req = requests.get("https://api.scryfall.com/cards?page={}".format(page))
            data = req.text
            with open(filete, "w", encoding="utf-8") as f:
                f.write(data)
        cards = json.loads(data)
        sql = "INSERT INTO scr_cards(id,name,set,idmkm,idck) VALUES"
        for card in cards["data"]:
            idmkm = re.match(reIDMKM, card["purchase_uris"]["magiccardmarket"])
            idmkm = "NULL" if idmkm is None else "'{}'".format(idmkm.group(1))
            idck = re.match(reIDCK, card["purchase_uris"]["card_kingdom"])
            idck = "NULL" if idck is None else idck.group(1)
            sql += "('{}','{}','{}',{},{}),".format(card["id"],card["name"].replace("'", "''"),card["set"],idmkm,idck)
        print("Pagina {}: {}".format(page, phppgadmin.execute(sql[:-1])))
        if (cards["has_more"]):
            page += 1
        else:
            break
def menu():
    os.system('cls')
    print("==[ DB retriever ]==")
    print("  1. Get editions")
    print("  2. Get cards")
    print("  0. Salir")
    return input("Opcion: ")

options = {
    "1": process_sets,
    "2": process_cards
}
if len(sys.argv) == 2:
    s = sys.argv[1]
    options[s]()
else:
    while True:
        opt = menu()
        if (opt == "0"):
            break
        os.system('cls')
        options[opt]()
        input("PRESIONA UNA TECLA PARA CONTINUAR")


# TODO: cartas relacionadas!!!!
# select s.name, c.name from scr_cards c left join scr_sets s on c.set = s.code
# left join ck_cards ck on c.idck = ck.id
# left join mkm_cards mkm on c.idmkm = mkm.edition || '/' || mkm.id
# where not mkm.id is null and not ck.id is null
# order by s.name, c.name


# TODO: las que estan en un lado y no en el otro, arreglar!!!
# select c.id, s.name, c.name, mkm.id, ck.id from scr_cards c left join scr_sets s on c.set = s.code
# left join ck_cards ck on c.idck = ck.id
# left join mkm_cards mkm on c.idmkm = mkm.edition || '/' || mkm.id
# where (mkm.id is null or ck.id is null) and not (mkm.id is null and ck.id is null)
# order by s.name, c.name
