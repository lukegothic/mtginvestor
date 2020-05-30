from mkmsdk.mkm import Mkm
from mkmsdk.api_map import _API_MAP
import time
from pprint import pprint

def postableArticle(p):
    return {
        "idArticle": p["idArticle"],
        "idLanguage": p["language"]["idLanguage"],
        "comments": p["comments"],
        "count": p["count"],
        "price": p["price"],
        "condition": p["condition"],
        "isFoil": "true" if p["isFoil"] else "false",
        "isSigned": "true" if p["isSigned"] else "false",
        "isPlayset": "true" if p["isPlayset"] else "false"
    }
# 0. setting variables etc
forceupdate = False
articles = None
# 1. obtener stock    
mkm = Mkm(_API_MAP["2.0"]["api"], _API_MAP["2.0"]["api_root"])
products = mkm.stock_management.get_stock().json()
time.sleep(1)
products = products["article"]
productsupdate = []
# 2. cambiar precios
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
                    # TODO: en este caso, poner a los que tienen mas rating primero
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
                    if len(productsupdate) >= 25:
                        time.sleep(5)
                        productsupdate = list(map(postableArticle, productsupdate))
                        r = mkm.stock_management.change_articles(data = { "article": productsupdate } )
                        print("Actualizados 25 articulos")
                        productsupdate = []
                else:
                    print("No hay coincidencias, introduce entrada manual")
            except: # si se cuelga por segunda vez la peticion...
                print("ACTUALIZA MANUAL!!!")
                pprint(p["product"])
                # hmm realmente esto ya no hace falta... no? ya no se cuelga... se podria poner manual la movida
                if len(productsupdate) > 0:
                    time.sleep(15)
                    productsupdate = list(map(postableArticle, productsupdate))
                    r = mkm.stock_management.change_articles(data = { "article": productsupdate } )
                    print("Actualizados {} articulos".format(len(r.json()["updatedArticles"])))
                    productsupdate = []
if len(productsupdate) > 0:
    time.sleep(5)
    productsupdate = list(map(postableArticle, productsupdate))
    r = mkm.stock_management.change_articles(data = { "article": productsupdate } )
    print("Actualizados {} articulos".format(len(r.json()["updatedArticles"])))
# 3. postear por tramos
#maxput = 100
#productsupdate = list(map(postableArticle, productsupdate))
#for i in range(0, len(productsupdate), maxput):
#    r = mkm.stock_management.change_articles(data = { "article": productsupdate[i:i+maxput] } )