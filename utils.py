import requests, time
import os, webbrowser
from PIL import Image, ImageDraw, ImageFont
# para usarlo con sqlite3, devuelve consultas en plan dict python
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
# muestra cartas en visor html
def showCardsInViewer(cards, op="cardviewer"):
    if (len(cards) > 0):
        with open("templates/{}.html".format(op)) as f:
            template = f.read()
        tmphtml = os.path.abspath("tmp_{}.html".format(time.time()))
        with open(tmphtml, "w", encoding="utf8") as f:
            if (op == "cardviewer"):
                f.write(template.format(cards = cards))
            elif (op == "cardviewer_tappedout"):
                f.write(template.format(cards = "\n".join("1 {}".format(c["name"]) for c in cards)))
        webbrowser.open(tmphtml)
    else:
        print("no cards found")
def getImageFromURI(uri):
    r = requests.get(uri, stream=True)
    image = Image.open(r.raw)
    return image
def addTextToImage(image, text):
    width, height = image.size

    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('arial.ttf', 60)
    textwidth, textheight = draw.textsize(text, font)

    # calculate the x,y coordinates of the text
    margin = 5
    x = width - textwidth - margin
    y = height - textheight - margin

    # draw watermark in the bottom right corner
    draw.text((x, y), text, font=font, fill=(255,255,255,255))

    return image
def mergeImages(image1, image2, direction=1): # 1: horizontal, 2: vertical
    w1, h1 = image1.size
    w2, h2 = image2.size
    if direction == 1:
        image = Image.new("RGBA", (w1 + w2, max(h1, h2)))
        image.paste(image1)
        image.paste(image2, (w1, 0))
    else:
        image = Image.new("RGBA", (max(w1, w2), h1 + h2))
        image.paste(image1)
        image.paste(image2, (0, h1))
    return image
def resizeImageBy(image, pct):
    w, h = image.size
    w = (int)(w * pct / 100)
    h = (int)(h * pct / 100)
    return image.resize((w, h))
