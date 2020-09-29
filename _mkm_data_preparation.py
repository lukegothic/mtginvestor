# este archivo obtiene datos de diferentes fuentes y los prepara para ser usados en multiples plataformas y titos
import json, io
from ftplib import FTP_TLS
from endpoints import mkm, scryfall
from utils import decklist, ftp
# MKM
def domkm():
    data = {}
    # precios mkm desde mkm
    mkm_mtg_cards_priceguide_raw = mkm.mtg_cards_priceguide()
    price_guide = {}
    for p in mkm_mtg_cards_priceguide_raw:
        price_guide[(int)(p["idProduct"])] = [
            [(float)(p["Avg. Sell Price"]) if p["Avg. Sell Price"] != "" else None, (float)(p["Low Price Ex+"]) if p["Low Price Ex+"] != "" else None, (float)(p["Trend Price"]) if p["Trend Price"] != "" else None],
            [(float)(p["Foil Sell"]) if p["Foil Sell"] != "" else None, (float)(p["Foil Low"]) if p["Foil Low"] != "" else None, (float)(p["Foil Trend"]) if p["Foil Trend"] != "" else None]
        ]
    data["price_guide"] = price_guide
    # edh_rank desde scryfall
    # lista de nombres => edh_rank
    scryfall_bulk_cards = scryfall.bulk_cards()
    cardname_x_edhrec_rank = []
    for c in scryfall_bulk_cards:
        cardname_x_edhrec_rank.append((c["name"],c["edhrec_rank"] if "edhrec_rank" in c else None))
    data["edh_rank"] = cardname_x_edhrec_rank
    # lista restringidas
    cards = decklist.fromfile(filename="docs/reservedlistcards.txt")
    data["reserved"] = [c for c in cards]
    # upload
    b = bytearray(json.dumps(data, separators=(',', ':')), "utf8")
    ftp.upload(b, "data_prepared.json", ftppath="/nal/apps/mtg/mkm")
#MAIN
domkm()

