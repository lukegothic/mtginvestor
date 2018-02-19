import os, re, sys, json, requests, decklist, sqlite3, csv, webbrowser
import utils

basedir = "__mycache__/scryfall"
if (not os.path.exists(basedir)):
    os.makedirs(basedir)
dbdir = "__offlinecache__/scryfall"
if (not os.path.exists(dbdir)):
    os.makedirs(dbdir)
dbfile = "{}/scryfall.db".format(dbdir)
def create_db():
    dbconn = sqlite3.connect(dbfile)
    c = dbconn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sets
             (code text PRIMARY KEY, name text, set_type text, released_at text, block_code text, block text, parent_set_code text, card_count integer, digital integer, foil integer, icon_svg_uri text, search_uri text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cards
             (id text PRIMARY KEY, name text, setcode text, idmkm text, idck text, color text, type text, usd real, eur real, reprint integer, image_uri text, collector_number integer, multiverse_id integer)''')
    dbconn.commit()
    dbconn.close()
def process_sets():
    cachedir = "{}/sets".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    filete = "{}/sets.json".format(cachedir)
    try:
        with open(filete) as f:
            data = f.read()
    except:
        req = requests.get("https://api.scryfall.com/sets")
        data = req.text
        with open(filete, "w") as f:
            f.write(data)
    sets = json.loads(data)
    setsinsert = []
    for set in sets["data"]:
        setsinsert.append(
            (
                set["code"],
                set["name"],
                set["set_type"],
                '{}'.format(set["released_at"]) if "released_at" in set else None,
                '{}'.format(set["block_code"]) if "block_code" in set else None,
                '{}'.format(set["block"].replace("'", "''")) if "block" in set else None,
                '{}'.format(set["parent_set_code"]) if "parent_set_code" in set else None,
                set["card_count"],
                (1 if set["digital"] else 0) if "digital" in set else 0,
                (1 if set["foil"] else 0) if "foil" in set else 0,
                set["icon_svg_uri"],
                set["search_uri"]
            )
        )
    dbconn = sqlite3.connect(dbfile)
    c = dbconn.cursor()
    c.execute("DELETE FROM sets")
    c.executemany('INSERT INTO sets VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', setsinsert)
    dbconn.commit()
    print("Insertados {} de {} sets".format(c.execute("SELECT count(*) as cnt FROM sets").fetchone()[0], len(setsinsert)))
    dbconn.close()
def getCardColor(colors):
    return "C" if len(colors) == 0 else ("M" if len(colors) > 1 else colors[0])
def process_cards():
    #prompt para confirmar
    cachedir = "{}/cards".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    reIDMKM = "https:\/\/www\.cardmarket\.com\/Magic\/Products\/Singles\/(.*?)\?"
    reIDCK = "https:\/\/www\.cardkingdom\.com\/catalog\/item\/(\d*)?\?"
    page = 1
    cardsinsert = []
    while True:
        filete = "{}/{}.json".format(cachedir, page)
        try:
            with open(filete, encoding="utf-8") as f:
                data = f.read()
        except:
            req = requests.get("https://api.scryfall.com/cards?page={}".format(page))
            data = req.text
            with open(filete, "w", encoding="utf-8") as f:
                f.write(data)
        cards = json.loads(data)
        for card in cards["data"]:
            idmkm = re.match(reIDMKM, card["purchase_uris"]["magiccardmarket"])
            idmkm = None if idmkm is None else idmkm.group(1)
            idck = re.match(reIDCK, card["purchase_uris"]["card_kingdom"])
            idck = None if idck is None else idck.group(1)
            # if (not "image_uris" in card):
            #     image_uris = []
            #     if ("card_faces" in card):
            #         for face in card["card_faces"]:
            #             image_uris.append(face["image_uris"]["normal"])
            #     image_uris = ";".join(image_uris)
            # else:
            #     image_uris = card["image_uris"]["normal"]
            try:
                cardsinsert.append(
                    (
                        card["id"],
                        card["name"].split(" // ")[0],
                        card["set"],
                        idmkm,
                        idck,
                        #getCardColor(card["colors"]) if "colors" in card else (";".join(getCardColor(f["colors"]) for f in card["card_faces"])),
                        getCardColor(card["colors"]) if "colors" in card else getCardColor(card["card_faces"][0]["colors"]),
                        #card["type_line"] if "type_line" in card else (";".join(f["type_line"] for f in card["card_faces"])),
                        card["type_line"] if "type_line" in card else card["card_faces"][0]["type_line"],
                        card["usd"] if "usd" in card else None,
                        card["eur"] if "eur" in card else None,
                        1 if card["reprint"] else 0,
                        #card["image_uris"]["normal"] if "image_uris" in card else (";".join(f["image_uris"]["normal"] for f in card["card_faces"])),
                        card["image_uris"]["normal"] if "image_uris" in card else card["card_faces"][0]["image_uris"]["normal"],
                        card["collector_number"],
                        card["multiverse_ids"][0] if "multiverse_ids" in card and len(card["multiverse_ids"]) > 0 else None
                    )
                )
            except:
                print("No insertado: " + card["name"])
                #print("Pagina {}: {}".format(page, phppgadmin.execute(sql[:-1])))
        if (cards["has_more"]):
            page += 1
        else:
            break
    dbconn = sqlite3.connect(dbfile)
    c = dbconn.cursor()
    c.execute("DELETE FROM cards")
    c.executemany('INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', cardsinsert)
    dbconn.commit()
    print("Insertadas {} de {} cartas".format(c.execute("SELECT count(*) as cnt FROM cards").fetchone()[0], len(cardsinsert)))
    dbconn.close()
def getcardprices(cards):
    dbconn = sqlite3.connect(dbfile)
    dbconn.row_factory = sqlite3.Row
    c = dbconn.cursor()
    sql = "SELECT name,min(eur) as price FROM cards WHERE LOWER(name) IN ('{}') GROUP BY name".format("','".join(cards).lower())
    dbcards = c.execute(sql)
    dbcards = dbcards.fetchall()
    dbconn.close()
    return dbcards
def getcards(cards):
    dbconn = sqlite3.connect(dbfile)
    dbconn.row_factory = utils.dict_factory
    c = dbconn.cursor()
    dbcards = c.execute("SELECT c.id, c.name, c.setcode, c.color, c.type, c.eur, c.image_uri, c.collector_number, s.name as setname, s.icon_svg_uri as seticon, s.released_at as setreleasedate FROM cards c LEFT JOIN sets s ON c.setcode = s.code WHERE s.digital = 0 AND LOWER(c.name) IN ('{}') ORDER BY s.released_at".format("','".join(cards).lower()))
    dbcards = dbcards.fetchall()
    dbconn.close()
    return dbcards
def download_images():
    picsdir = "{}/pics".format(basedir)
    if (not os.path.exists(picsdir)):
        os.makedirs(picsdir)
    cards = phppgadmin.query("SELECT image_uri, name, set, collector_number from scr_cards")
    reVersions = "\d*([abcd]+)"
    for c in cards:
        print("{} [{}]".format(c["name"], c["set"]))
        if c["image_uri"] != "":
            setcode = c["set"].upper()
            if setcode == "CON":
                setcode = "CFX"
            setdir = "{}/{}".format(picsdir, setcode)
            if (not os.path.exists(setdir)):
                os.makedirs(setdir)
            # controlar cartas antiguas con varias versiones
            isVersioned = re.match(reVersions, c["collector_number"])
            v = ""
            if "//" not in c["name"] and not isVersioned is None:
                v = isVersioned.group(1)
                if v == "a":
                    v = 1
                elif v == "b":
                    v = 2
                elif v == "c":
                    v = 3
                elif v == "d":
                    v = 4
            # controlar double faced
            faces = []
            if "||" in c["image_uri"]:
                print(c)
                names = c["name"].split(" // ")
                imgs = c["image_uri"].split("||")
                faces.append({ "name": names[0], "img": imgs[0] })
                faces.append({ "name": names[1], "img": imgs[1] })
                print(faces)
            else:
                # TODO: las tierras basicas tienen versiones... no se como hacerlo
                # TODO: si la carta es de flip pero no de transform, nos quedamos sólo con la parte primera del nombre!
                # TODO: EMN graf rats1 ??? por que le pone numero?
                # TODO: estas 3 tienen version 1 y 2
                # Ertai, the Corrupted[PLS]
                # Skyship Weatherlight[PLS]
                # Tahngarth, Talruum Hero[PLS]
                faces.append({ "name": c["name"].replace(" // ", "").replace('"',"").replace(":","").replace("á", "a").replace("à", "a").replace("â", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ö", "o").replace("ú", "u").replace("û", "u").replace("?",""), "img": c["image_uri"] })
            for face in faces:
                filete = "{}/{}{}.full.jpg".format(setdir, face["name"], v)
                try:
                    with open(filete) as f:
                        pass
                except:
                    req = requests.get(face["img"])
                    with open(filete, "wb") as f:
                        f.write(req.content)
        else:
            print("No hay imagen")
def pricedecklist():
    deck = decklist.readdeckfromfile()
    prices = getcardprices(c.replace("'", "''") for c in deck)
    total = 0
    with open("prices.csv", "w") as f:
        for card in deck:
            quantity = deck[card]
            for cp in prices:
                cardnameprice = cp["name"]
                cardprice = cp["price"]
                if card.lower() == cardnameprice.lower():
                    cardtotal = cardprice * quantity
                    f.write("{};{};{:.2f};{:.2f}\n".format(quantity, card, cardprice, cardtotal))
                    total += cardtotal
                    break;
    print("Total = {:.2f} Euros".format(total))
def cardsbyedition():
    deck = decklist.readdeckfromfile()
    cards = getcards(c.replace("'", "''") for c in deck)
    utils.showCardsInViewer(cards)
def menu():
    os.system('cls')
    print("==[ DB retriever ]==")
    print("  1. Get editions")
    print("  2. Get cards")
    print("  3. Get images")
    print("  4. Price deck")
    print("  5. Todas las ediciones de una lista de cartas")
    print("  0. Salir")
    return input("Opcion: ")

create_db()
options = {
    "1": process_sets,
    "2": process_cards,
    "3": download_images,
    "4": pricedecklist,
    "5": cardsbyedition
}
if len(sys.argv) == 2:
    s = sys.argv[1]
    options[s]()
else:
    while True:
        opt = menu()
        if (opt == "0"):
            break
        os.system('cls')
        options[opt]()
        input("PRESIONA UNA TECLA PARA CONTINUAR")

# TODO: cartas relacionadas!!!!
# select s.name, c.name from scr_cards c left join scr_sets s on c.set = s.code
# left join ck_cards ck on c.idck = ck.id
# left join mkm_cards mkm on c.idmkm = mkm.edition || '/' || mkm.id
# where (not mkm.id is null and not ck.id is null) and not s.digital
# order by s.name, c.name


# TODO: las que estan en un lado y no en el otro, arreglar!!!
# select c.id, s.name, c.name, mkm.id, ck.id from scr_cards c left join scr_sets s on c.set = s.code
# left join ck_cards ck on c.idck = ck.id
# left join mkm_cards mkm on c.idmkm = mkm.edition || '/' || mkm.id
# where ((mkm.id is null or ck.id is null) and not (mkm.id is null and ck.id is null)) and not s.digital
# order by s.name, c.name


# TODO: maravilloso, saca en un json cartas de un listado
# TODO: tratamiento previo: generar las cartas como values para meterlas en la tabla temporal
# TODO: y ademas, hacer un join simple para comprobar las que no están
# WITH inputcards (n) AS (VALUES ('Ash Barrens'),('Azorius Guildgate'),('Bloodfell Caves'),('Blossoming Sands'),('Boros Guildgate'),('Cinder Barrens'),('Desert'),('Dimir Guildgate'),('Dismal Backwater'),('Evolving Wilds'),('Forsaken Sanctuary'),('Foul Orchard'),('Golgari Guildgate'),('Gruul Guildgate'),('Highland Lake'),('Izzet Guildgate'),('Jungle Hollow'),('Maze of Ith'),('Meandering River'),('Mishra''s Factory'),('Orzhov Guildgate'),('Rakdos Guildgate'),('Rugged Highlands'),('Scoured Barrens'),('Selesnya Guildgate'),('Simic Guildgate'),('Stone Quarry'),('Strip Mine'),('Submerged Boneyard'),('Swiftwater Cliffs'),('Terramorphic Expanse'),('Thornwood Falls'),('Timber Gorge'),('Tranquil Cove'),('Tranquil Expanse'),('Warped Landscape'),('Wind-Scarred Crag'),('Woodland Stream'),('Act of Treason'),('Adventuring Gear'),('Aerie Ouphes'),('Aether Adept'),('Aethersnipe'),('Agony Warp'),('Aim High'),('Ambuscade'),('Ambush Viper'),('Angelic Purge'),('Arachnus Web'),('Arc Lightning'),('Armillary Sphere'),('Arrest'),('Ashes to Ashes'),('Assault Zeppelid'),('Attended Knight'),('Auger Spree'),('Augur of Bolas'),('Aven Riftwatcher'),('Aven Surveyor'),('Baleful Eidolon'),('Barbed Lightning'),('Basking Rootwalla'),('Battle Screech'),('Beetleback Chief'),('Beetleform Mage'),('Beneath the Sands'),('Blastoderm'),('Blazing Torch'),('Blightning'),('Blinding Beam'),('Bonded Construct'),('Bonds of Faith'),('Bonesplitter'),('Borderland Marauder'),('Borrowed Grace'),('Branching Bolt'),('Brazen Buccaneers'),('Brazen Wolves'),('Burning-Tree Emissary'),('Burst Lightning'),('Butcher Ghoul'),('Byway Courier'),('Cage of Hands'),('Calcite Snapper'),('Call of the Conclave'),('Capsize'),('Carnivorous Death-Parrot'),('Cartouche of Strength'),('Cathodion'),('Cavern Harpy'),('Centaur Healer'),('Chain Lightning'),('Chainer''s Edict'),('Chatter of the Squirrel'),('Citanul Woodreaders'),('Claustrophobia'),('Clay Statue'),('Cloaked Siren'),('Clutch of Currents'),('Coalition Honor Guard'),('Cogwork Librarian'),('Colossal Might'),('Compulsive Research'),('Compulsory Rest'),('Consume Strength'),('Corrupted Zendikon'),('Counterspell'),('Crippling Fatigue'),('Crow of Dark Tidings'),('Crypt Rats'),('Crystallization'),('Cunning Strike'),('Curse of Chains'),('Custodi Squire'),('Daring Skyjek'),('Dauntless Cathar'),('Dead Reveler'),('Dead Weight'),('Deadeye Tormentor'),('Death Denied'),('Deep Analysis'),('Deprive'),('Depths of Desire'),('Deputy of Acquittals'),('Desperate Sentry'),('Devour Flesh'),('Diabolic Edict'),('Dinrova Horror'),('Dire Fleet Hoarder'),('Disfigure'),('Disowned Ancestor'),('Doom Blade'),('Doomed Traveler'),('Drag Under'),('Dragon Fodder'),('Dynacharge'),('Eager Construct'),('Eldrazi Devastator'),('Eldrazi Skyspawner'),('Elephant Ambush'),('Elephant Guide'),('Elite Vanguard'),('Emperor Crocodile'),('Epic Confrontation'),('Errant Ephemeron'),('Esper Cormorants'),('Evincar''s Justice'),('Faceless Butcher'),('Faith''s Fetters'),('Falkenrath Noble'),('Feeling of Dread'),('Fervent Cathar'),('Firebolt'),('Fireslinger'),('Flayer Husk'),('Flurry of Horns'),('Forked Bolt'),('Fortify'),('Frilled Oculus'),('Frostburn Weird'),('Gathan Raiders'),('Gather the Townsfolk'),('Ghastly Demise'),('Ghirapur Gearcrafter'),('Ghitu Slinger'),('Giant Growth'),('Gideon''s Lawkeeper'),('Glint-Sleeve Artisan'),('Gnawing Zombie'),('Goblin Freerunner'),('Goblin Heelcutter'),('Gods Willing'),('Goldmeadow Harrier'),('Gravedigger'),('Gray Merchant of Asphodel'),('Grazing Whiptail'),('Grim Contest'),('Grisly Salvage'),('Grixis Slavedriver'),('Gryff Vanguard'),('Guardian Automaton'),('Guardian Idol'),('Guardian of the Guildpact'),('Gurmag Angler'),('Halimar Wavewatch'),('Harrow'),('Harsh Sustenance'),('Hissing Iguanar'),('Hooting Mandrills'),('Humble'),('Imperiosaur'),('Incinerate'),('Inner-Flame Acolyte'),('Insolent Neonate'),('Into the Roil'),('Isolation Zone'),('Ivy Elemental'),('Izzet Chronarch'),('Jilt'),('Journey to Nowhere'),('Kabuto Moth'),('Keldon Marauders'),('Kingpin''s Pet'),('Kor Skyfisher'),('Kozilek''s Channeler'),('Krenko''s Command'),('Krosan Tusker'),('Kruin Striker'),('Lash Out'),('Last Gasp'),('Leave in the Dust'),('Leonin Bola'),('Lifecraft Cavalry'),('Lightning Bolt'),('Liliana''s Specter'),('Lotus Path Djinn'),('Loyal Pegasus'),('Lurking Automaton'),('Magma Jet'),('Makeshift Mauler'),('Man-o''-War'),('Mana Leak'),('Manticore of the Gauntlet'),('Mardu Hordechief'),('Mardu Skullhunter'),('Maul Splicer'),('Mental Note'),('Midnight Scavengers'),('Mind Stone'),('Minotaur Skullcleaver'),('Miscalculation'),('Mist Raven'),('Mistral Charger'),('Mobile Garrison'),('Mogg Fanatic'),('Mogg Flunkies'),('Mogg War Marshal'),('Moldervine Cloak'),('Momentary Blink'),('Morgue Theft'),('Mulldrifter'),('Nameless Inversion'),('Narcolepsy'),('Necromancer''s Assistant'),('Nessian Asp'),('Nest Robber'),('Nezumi Cutthroat'),('Night''s Whisper'),('Nightscape Familiar'),('Ninja of the Deep Hours'),('Oblivion Ring'),('Oona''s Grace'),('Otherworldly Journey'),('Pacifism'),('Paladin of the Bloodstained'),('Peema Outrider'),('Penumbra Spider'),('Peregrine Drake'),('Perilous Myr'),('Pestermite'),('Pestilence'),('Phantom Nomad'),('Phantom Tiger'),('Pharika''s Chosen'),('Phyrexian Rager'),('Pillory of the Sleepless'),('Pit Fight'),('Pit Keeper'),('Plated Geopede'),('Plover Knights'),('Porcelain Legionnaire'),('Pounce'),('Predatory Nightstalker'),('Preordain'),('Prey Upon'),('Prismatic Strands'),('Pristine Talisman'),('Prophetic Prism'),('Pulse of Murasa'),('Pursue Glory'),('Putrid Leech'),('Pyrotechnics'),('Qasali Pridemage'),('Raise the Alarm'),('Rally the Peasants'),('Rampant Growth'),('Rancor'),('Ranger''s Guile'),('Ray of Command'),('Razorfin Hunter'),('Reckless Charge'),('Recoil'),('Regicide'),('Remove Soul'),('Rend Flesh'),('Rendclaw Trow'),('Renegade Freighter'),('Rift Bolt'),('Rishadan Airship'),('Ronin Houndmaster'),('Runed Servitor'),('Rushing River'),('Sailor of Means'),('Sakura-Tribe Elder'),('Sandsteppe Outcast'),('Sangrite Backlash'),('Sarkhan''s Rage'),('Savage Punch'),('Scatter the Seeds'),('Scion of the Wild'),('Scion Summoner'),('Scourge Devil'),('Screeching Skaab'),('Scuzzback Marauders'),('Search for Tomorrow'),('Searing Blaze'),('Seeker of Insight'),('Seeker of the Way'),('Sentinel Spider'),('Separatist Voidmage'),('Seraph of Dawn'),('Serrated Arrows'),('Shaper Parasite'),('Sheer Drop'),('Shelter'),('Shimmering Glasskite'),('Sigil Blessing'),('Silent Departure'),('Skirk Marauder'),('Skyknight Legionnaire'),('Slash Panther'),('Snakeform'),('Snap'),('Soul Manipulation'),('Soulstinger'),('Sphere of the Suns'),('Spike Jester'),('Spined Thopter'),('Splatter Thug'),('Staggershock'),('Star Compass'),('Stitched Drake'),('Storm Fleet Pyromancer'),('Stormfront Pegasus'),('Stormscape Apprentice'),('Striped Riverwinder'),('Sultai Scavenger'),('Suppression Bonds'),('Sylvan Might'),('Sylvok Lifestaff'),('Tah-Crop Elite'),('Temporal Isolation'),('Tenement Crasher'),('Terminate'),('Test of Faith'),('Thorn of the Black Rose'),('Thornweald Archer'),('Thought Scour'),('Thraben Inspector'),('Thrill-Kill Assassin'),('Thundering Giant'),('Thundering Tanadon'),('Thunderous Wrath'),('Time to Feed'),('Tithe Drinker'),('Totem-Guide Hartebeest'),('Tragic Slip'),('Travel Preparations'),('Treasure Cruise'),('Triplicate Spirits'),('Typhoid Rats'),('Ulamog''s Crusher'),('Ulvenwald Captive // Ulvenwald Abomination'),('Undying Rage'),('Unearth'),('Unmake'),('Vampire Interloper'),('Vault Skirge'),('Viashino Firstblade'),('Vines of Vastwood'),('Voldaren Duelist'),('Vulshok Morningstar'),('Vulshok Sorcerer'),('Vulturous Aven'),('Wakedancer'),('Walker of the Grove'),('Wall of Roots'),('War Flare'),('Warden of Evos Isle'),('Warren Pilferers'),('Wasteland Scorpion'),('Wayfarer''s Bauble'),('Werebear'),('Whitemane Lion'),('Wild Instincts'),('Wild Mongrel'),('Wild Nacatl'),('Wildsize'),('Will-Forged Golem'),('Winds of Rebuke'),('Winged Coatl'),('Wojek Halberdiers'),('Wrecking Ball'),('Wretched Gryff'),('Yavimaya Elder'),('Yotian Soldier'))
# SELECT array_to_json(array_agg(t)) FROM
# (select s.name as set, c.name, c.image_uri from inputcards ic left join scr_cards c on c.name = ic.n left join scr_sets s on c.set = s.code
# where not digital and not c.reprint
# order by s.released_at,c.set,CASE WHEN c.collector_number~E'^\\d+$' THEN c.collector_number::integer ELSE 0 END) t


# ESTO LAS SACA a un HTML
# <html>
# <head>
# 	<style>
# 	img {
# 		width:140px;
# 	}
# 	</style>
# </head>
# <body>
# 	<script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>
# 	<script>
# 		var cards = CARDS;
# 		var set = '';
# 		cards.forEach(function(c) {
# 			if (c.set !== set) {
# 				$("<h3>").html(c.set).appendTo(document.body);
# 				set = c.set;
# 			}
# 			$("<img>").attr({"src": c.image_uri, "title": c.name, "alt": c.name }).appendTo(document.body);
# 		});
# 	</script>
# </body>
