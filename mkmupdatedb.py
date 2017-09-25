import requests
from lxml import html

s = requests.Session()

resp = s.get("http://fotoraton.es/phppgadmin/redirect.php?subject=server&server=localhost%3A5432%3Aallow&")
tree = html.fromstring(resp.content)

username = tree.xpath("//input[@name='loginUsername']")[0]
password = tree.xpath("//input[@id='loginPassword']")[0]

loginpostdata = {"subject": "server", "server": "localhost:5432:allow", "loginServer": "localhost:5432:allow", "loginUsername": "postgres", "loginSubmit": "Autenticar"}
loginpostdata[password.attrib["name"]] = "postgres"

resp = s.post("http://fotoraton.es/phppgadmin/redirect.php", loginpostdata)

cachedir = "cache/mkm/prices"

def getEditions():
    rootfile = cachedir + "/root.html"

    try:
        f = open(rootfile, "r", encoding="utf8")
        data = f.read()
        f.close()
    except IOError:
        page = requests.get("https://www.magiccardmarket.eu/Expansions")
        data = page.text
        f = open(rootfile, "w", encoding="utf8")
        f.write(data)
        f.close()

    tree = html.fromstring(data)
    return list(map(lambda e: e.attrib["href"].replace("/Expansions/", ""), tree.xpath("//a[@class='alphabeticExpansion']")))

def saveEditionData(edition):
    #TODO: number_lines = sum(1 for line in open(my_file))
    f = open("{}/{}/cards.sql".format(cachedir, edition), "r", encoding="utf8")
    rows = f.read()
    rows = rows[:-1]
    f.close()
    print("{} [{} cards]".format(edition, "999"))
    basefilter = { "server": "localhost:5432:allow", "database": "magic", "search_path": "public", "query": rows }
    resp = s.post("http://fotoraton.es/phppgadmin/sql.php", basefilter)

    f = open("{}/{}/prices.sql".format(cachedir, edition), "r", encoding="utf8")
    rows = f.read()
    rows = rows[:-1]
    f.close()
    print("{} [{} prices]".format(edition, "99999"))
    basefilter = { "server": "localhost:5432:allow", "database": "magic", "search_path": "public", "query": rows }
    resp = s.post("http://fotoraton.es/phppgadmin/sql.php", basefilter)

editions = getEditions()
#hacer = False
for edition in editions:
    #if hacer or edition == "Journey+into+Nyx":
    #    hacer = True
    saveEditionData(edition)

#saveEditionData("Apocalypse")
'''
select c.name, c.edition, p.foil, min(p.price) from mtgtop8_staples s left join mkm_cards c on s.name = c.name left join mkm_cardprices p on c.name = p.card and c.edition = p.edition
where not p.price is null
group by c.name, c.edition, p.foil
order by c.name,min(p.price) desc
'''
#TODO: solucionar esta join
#select * from mtgtop8_staples s left join mkm_cards c on lower(trim(s.name)) = lower(c.name) where c.name is null


'''
select card,edition,min(price)
 from mkm_cardprices where edition in ('Urza%27s+Legacy','Urza%27s+Saga','Urza%27s+Destiny','Mercadian+Masques','Nemesis','Prophey','Invasion','Apocalypse','Planeshift','Odyssey','Torment','Judgment','Onslaught','Legions','Scourge','Seventh+Edition') and foil = true
group by card,edition
union
select card,edition,min(price)
 from mkm_cardprices where edition in ('Judge+Rewards+Promos','Friday+Night+Magic+Promos')
group by card,edition

order by edition,card
'''

'''
select c.name as card,e.name as edition, p.pricefoil
 from ck_cardprices p left join ck_cards c on p.cardid = c.id left join ck_editions e on c.editionid = e.id where e.name in ('Urza''s Destiny','Urza''s Saga','Urza''s Legacy','Mercadian Masques','Nemesis','Prophey','Invasion','Apocalypse','Planeshift','Odyssey','Torment','Judgment','Onslaught','Legions','Scourge','7th Edition') and p.condition = 'NM'

union

select c.name as card,e.name as edition, p.pricefoil
 from ck_cardprices p left join ck_cards c on p.cardid = c.id left join ck_editions e on c.editionid = e.id where e.name = 'Promotional' and p.condition = 'NM'


order by edition,card
'''
