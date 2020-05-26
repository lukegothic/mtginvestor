import re
import tkinter as tk
from tkinter import filedialog
reCard = "(\d+).{1}(.*)"
def readdeckfromfile():
    root = tk.Tk()
    root.wm_attributes('-topmost', True)
    root.withdraw()
    filepath = filedialog.askopenfilename()
    with open(filepath) as f:
        data = f.readlines()
    cards = {}
    for d in data:
        m = re.match(reCard, d.strip())
        if not m is None:
            quantity = (int)(m.group(1))
            card = m.group(2)
            if not card in cards:
                cards[card] = 0
            cards[card] += quantity
    return cards
