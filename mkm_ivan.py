from mkmsdk.mkm import Mkm
from mkmsdk.api_map import _API_MAP
import time
from pprint import pprint
import base64
import deckbox, mkm, sys, utils
import decklist
import sqlite3, csv
import json
import traductor

global mkm
mkm = Mkm(_API_MAP["2.0"]["api"], _API_MAP["2.0"]["api_root"])
global mkm_maxpostputdelete
mkm_maxpostputdelete = 100

def insertableArticle(p):
    return {
        "idProduct": p["idProduct"],
        "idLanguage": p["language"]["idLanguage"],
        "comments": p["comments"] if not p["comments"] is None else "",
        "count": p["count"],
        "price": p["price"] if not p["price"] is None else 999.99,
        "condition": p["condition"] if not p["price"] is None else "NM",
        "isFoil": "true" if p["isFoil"] else "false",
        "isSigned": "true" if p["isSigned"] else "false",
        "isPlayset": "true" if p["isPlayset"] else "false"
    }
def updatableArticle(p):
    q = insertableArticle(p)
    q["idArticle"] = p["idArticle"]
    return q
def borrableArticle(p):
    return {
        "idArticle": p["idArticle"],
        "count": p["count"]
    }
def obteneritemsinventario():
    mycards = deckbox.getInventoryRaw()
    #TRADUCIR Y GUARDAR EN FICHERO, MOLA
    (mycards_mkm, mycards_mkm_nontranslated) = traductor.traduce(mycards)
    with open("mkm_stock_management_MYSTOCK.json", "w", encoding="utf8") as f:
        json.dump(mycards_mkm, f)
    with open("mkm_stock_management_MANUAL.json", "w", encoding="utf8") as f:
        json.dump(mycards_mkm_nontranslated, f)
    return mycards_mkm
def actualizarprecios(products):
    forceupdate = False
    articles = None
    productsupdate = []
    for p in products:
        if p["comments"] != "?" and p["comments"] != "mnl":    # ignorar mystery box (y en un futuro las cartas reeditadas, al menos hasta pasados un par de años) tb se ignoran las cartas manuales
            currenttime = time.time()
            lasttime = p["comments"].split("^")
            lasttime = (int)(lasttime[1]) if len(lasttime) > 1 else None
            if lasttime is None or (currenttime - lasttime >= 3600) or forceupdate == True:
                try:
                    try:    # si se cuelga porque no hay articulos
                        time.sleep(0.5)
                        articles = mkm.market_place.articles(product=p["idProduct"], params={ "isFoil": "true" if p["isFoil"] else "false", "idLanguage": p["language"]["idLanguage"], "minCondition": "NM", "minUserScore": 1, "start": 0, "maxResults": 5, "userType": "commercial" }).json()
                    except:
                        time.sleep(0.5)
                        articles = mkm.market_place.articles(product=p["idProduct"], params={ "isFoil": "true" if p["isFoil"] else "false", "idLanguage": p["language"]["idLanguage"], "minCondition": "NM", "minUserScore": 2, "start": 0, "maxResults": 5 }).json()
                        # TODO: en este caso, poner a los que tienen mas rating primero!!!!!!
                    articles = articles["article"]
                    if len(articles) > 0:
                        p["price"] = (articles[0]["price"] - 0.05)
                        if p["price"] >= 15:
                            comment = "[ Perfect Size and Bubble Envelope ]"
                        elif p["price"] >= 3:
                            comment = "[ Perfect Size ]"
                        else:
                            comment = "[ Great Stuff ]"
                        p["comments"] = '~*{}*~ from MTG(c) Judge^{}'.format(comment, (int)(currenttime))
                        productsupdate.append(p)
                        # mejor de poco en poco... el maximo es 100 pero nos aseguramos mandando de 25 en 25
                        if len(productsupdate) >= 25:
                            updatestock(productsupdate)
                            productsupdate = []
                    else:
                        print("No hay coincidencias, introduce entrada manual")
                except: # si se cuelga por segunda vez la peticion...
                    print("ACTUALIZA MANUAL!!!")
                    pprint(p["product"])
                    # hmm realmente esto ya no hace falta... no? ya no se cuelga... se podria poner manual la movida
                    updatestock(productsupdate)
                    productsupdate = []
    updatestock(productsupdate)
    productsupdate = []
def updateprices():   
    # 1. obtener stock    
    products = mkm.stock_management.get_stock().json()
    time.sleep(1)
    products = products["article"]
    backup(products)
    # 2. actualizar precios
    actualizarprecios(products)
def insertstock(products):
    products = list(map(insertableArticle, products))
    noninserted = []
    for i in range(0, len(products), mkm_maxpostputdelete):
        r = mkm.stock_management.add_articles(data = { "article": products[i:i+mkm_maxpostputdelete] } )
        revisa = r.json()
        for i in revisa["inserted"]:
            if i["success"] == False:
                noninserted.append(i)
        time.sleep(1)
        if len(noninserted) > 0:
            with open("mkm_stock_management_NONINSERTED", "a") as f:
                json.dump(noninserted, f)
            noninserted = []
def updatestock(products):
    #add_articles || change_articles
    if len(products) > 0:
        products = list(map(updatableArticle, products))
        for i in range(0, len(products), mkm_maxpostputdelete):
            r = mkm.stock_management.change_articles(data = { "article": products[i:i+mkm_maxpostputdelete] } )
            print("Actualizados {} articulos".format(len(r.json()["updatedArticles"])))
            time.sleep(1)
def deletestock():
    products = mkm.stock_management.get_stock().json()
    products = products["article"]
    backup(products)
    products = list(map(borrableArticle, products))
    for i in range(0, len(products), mkm_maxpostputdelete):
        r = mkm.stock_management.delete_articles(data = { "article": products[i:i+mkm_maxpostputdelete] } )
        time.sleep(1)
def backup(products):
    with open("backup/mkm/stock_management_get_stock_{}.json".format(time.time()), "w", encoding="utf8") as f:
        json.dump(products, f)
def restore(date):
    with open("backup/mkm/stock_management_get_stock_{}.json".format(date),"r",encoding="utf8") as f:
        products = json.load(f)
    insertstock(products)

# OPERACIONES
deletestock() # borrar
#restorestock(1590867184.947326) #recuperar stock
#updateprices() #actualizarprecios
#obteneritemsinventario() #deckbox a mkm
with open("mkm_stock_management_MYSTOCK.json","r", encoding="utf8") as f:
    products = json.load(f)
insertstock(products)