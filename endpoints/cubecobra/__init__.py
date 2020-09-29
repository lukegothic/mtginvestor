import requests
from utils import decklist

def download_cube(id):
    r = requests.get("https://cubecobra.com/cube/download/plaintext/{}".format(id))
    d = decklist.fromtext(r.text)
    return d

# pauper cube
#download_cube("5d617ac6c2a85f3b75fe95a4")
# mtgo vintage cube
#download_cube("modovintage")