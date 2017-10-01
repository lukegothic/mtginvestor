import csv
import requests

req = requests.get("https://deckbox.org/sets/export/125700?format=csv&f=&s=&o=&columns=Image%20URL")

with open("test.csv", "w") as f:
    f.write(req.text);
