import os, webbrowser, time, tempfile
# muestra cartas en visor html
# output: bytes||file
def prepare(cards, template):
    if (len(cards) > 0):
        with open(os.path.abspath("templates/{}.html".format(template))) as f:
            template = f.read()
        template.format(cards = cards)
        if (template == "cardviewer_tappedout"):
            f = template.format(cards = "\n".join("1 {}".format(c["name"]) for c in cards))
        else:
            t = template.format(cards = cards)
        return t
#TODO: cargar bytes en vez de fichero
def show(cards, template="cardviewer"):
    t = prepare(cards, template)
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".html", delete=False) as f:
        f.write(t)
    webbrowser.open("file://{}".format(f.name))
    return t