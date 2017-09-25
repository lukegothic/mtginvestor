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

cachedir = "cache/ck"

def getEditions():
	return ['3rd Edition','4th Edition','5th Edition','6th Edition','7th Edition','8th Edition','9th Edition','10th Edition','2010 Core Set','2011 Core Set','2012 Core Set','2013 Core Set','2014 Core Set','2015 Core Set','Aether Revolt','Alara Reborn','Alliances','Alpha','Amonkhet','Anthologies','Antiquities','Apocalypse','Arabian Nights','Archenemy','Archenemy Nicol Bolas','Avacyn Restored','Battle for Zendikar','Battle Royale','Beatdown','Beta','Betrayers of Kamigawa','Born of the Gods','Card Kingdom Tokens','Champions of Kamigawa','Chronicles','Coldsnap','Collectors Ed','Collectors Ed Intl','Commander','Commander 2013','Commander 2014','Commander 2015','Commander 2016','Commander Anthology','Commander\'s Arsenal','Conflux','Conspiracy','Conspiracy - Take the Crown','Dark Ascension','Darksteel','Deck Builder\'s Toolkit','Deckmaster','Dissension','Dragon\'s Maze','Dragons of Tarkir','Duel Decks Ajani Vs. Nicol Bolas','Duel Decks Anthology','Duel Decks Blessed Vs. Cursed','Duel Decks Divine Vs. Demonic','Duel Decks Elspeth Vs. Kiora','Duel Decks Elspeth Vs. Tezzeret','Duel Decks Elves Vs. Goblins','Duel Decks Garruk Vs. Liliana','Duel Decks Heroes Vs. Monsters','Duel Decks Izzet Vs. Golgari','Duel Decks Jace Vs. Chandra','Duel Decks Jace Vs. Vraska','Duel Decks Knights Vs. Dragons','Duel Decks Mind Vs. Might','Duel Decks Nissa Vs. Ob Nixilis','Duel Decks Phyrexia Vs. The Coalition','Duel Decks Sorin Vs. Tibalt','Duel Decks Speed Vs. Cunning','Duel Decks Venser Vs. Koth','Duel Decks Zendikar Vs. Eldrazi','Duels of the Planeswalkers','Eldritch Moon','Eternal Masters','Eventide','Exodus','Fallen Empires','Fate Reforged','Fifth Dawn','From the Vault Angels','From the Vault Annihilation','From the Vault Dragons','From the Vault Exiled','From the Vault Legends','From the Vault Lore','From the Vault Realms','From the Vault Relics','From the Vault Twenty','Future Sight','Gatecrash','Guildpact','Homelands','Ice Age','Innistrad','Invasion','Journey into Nyx','Judgment','Kaladesh','Khans of Tarkir','Legends','Legions','Lorwyn','Magic Origins','Masterpiece Series Expeditions','Masterpiece Series Inventions','Masterpiece Series Invocations','Mercadian Masques','Mirage','Mirrodin','Mirrodin Besieged','Modern Event Deck','Modern Masters','Modern Masters 2015','Modern Masters 2017','Morningtide','Nemesis','New Phyrexia','Non-English','Oath of the Gatewatch','Odyssey','Onslaught','Planar Chaos','Planechase','Planechase 2012','Planechase Anthology','Planeshift','Portal','Portal 3K','Portal II','Premium Deck Series Fire & Lightning','Premium Deck Series Graveborn','Premium Deck Series Slivers','Promotional','Prophecy','Ravnica','Return to Ravnica','Rise of the Eldrazi','Saviors of Kamigawa','Scars of Mirrodin','Scourge','Shadowmoor','Shadows Over Innistrad','Shards of Alara','Starter 1999','Starter 2000','Stronghold','Tempest','The Dark','Theros','Time Spiral','Timeshifted','Torment','Unglued','Unhinged','Unlimited','Urza\'s Destiny','Urza\'s Legacy','Urza\'s Saga','Vanguard','Visions','Weatherlight','World Championships','Worldwake','Zendikar']

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

for edition in editions:
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
select c.name as card,e.name as edition, p.price
 from ck_cardprices p left join ck_cards c on p.card = c.id left join ck_editions e on c.edition = e.id where e.name in ('Urza''s Destiny','Urza''s Saga','Urza''s Legacy','Mercadian Masques','Nemesis','Prophecy','Invasion','Apocalypse','Planeshift','Odyssey','Torment','Judgment','Onslaught','Legions','Scourge','7th Edition') and p.condition = 'NM' and p.foil = true
union
select c.name as card,e.name as edition, p.price
 from ck_cardprices p left join ck_cards c on p.card = c.id left join ck_editions e on c.edition = e.id where e.name in ('Promotional') and p.condition = 'NM'

order by card

'''
