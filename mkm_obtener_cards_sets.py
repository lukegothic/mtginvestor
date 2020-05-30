from mkmsdk.mkm import Mkm
from mkmsdk.api_map import _API_MAP
import base64

mkm = Mkm(_API_MAP["2.0"]["api"], _API_MAP["2.0"]["api_root"])
# obtener cartas del marketplace
pl = mkm.market_place.product_list()
with open("ckm.zip", "wb") as f:
    pfile = pl.json()["productsfile"]
    bdecoded = base64.b64decode(pfile)
    f.write(bdecoded)

# obtener expansiones
pl = mkm.market_place.expansions(game=1)
with open("ckm.json", "wb") as f:
    f.write(pl.content)
