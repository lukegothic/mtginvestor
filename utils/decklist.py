import re
import tkinter as tk
from tkinter import filedialog
reCard = "(\d?)(.*)"
def fromfile(filename=None):
    if filename is None:
        root = tk.Tk()
        root.wm_attributes('-topmost', True)
        root.withdraw()
        filename = filedialog.askopenfilename()
    with open(filename, encoding="utf8") as f:
        data = f.read()
    return fromtext(data)
def fromtext(text):
    cards = {}
    cardlines = text.splitlines()
    for c in cardlines:
        m = re.match(reCard, c.strip())
        if not m is None:
            quantity = (int)(m.group(1)) if m.group(1) != "" else 1
            card = m.group(2).strip()
            if not card in cards:
                cards[card] = 0
            cards[card] += quantity
    return cards
