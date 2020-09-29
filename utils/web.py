import requests
from PIL import Image

def getImageFromURI(uri):
    r = requests.get(uri, stream=True)
    image = Image.open(r.raw)
    return image