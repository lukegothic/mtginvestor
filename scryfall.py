import os
import re
import sys
import json
import requests
import phppgadmin

basedir = "__mycache__/scryfall"
if (not os.path.exists(basedir)):
    os.makedirs(basedir)

def process_sets():
    cachedir = "{}/sets".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    phppgadmin.execute("DELETE FROM scr_sets")
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
    sql = "INSERT INTO scr_sets(code,name,set_type,released_at,block_code,block,parent_set_code,card_count,digital,foil,icon_svg_uri,search_uri) VALUES"
    for set in sets["data"]:
        sql += "('{}','{}','{}',{},{},{},{},{},{},{},'{}','{}'),".format(set["code"], set["name"].replace("'", "''"), set["set_type"], "'{}'".format(set["released_at"]) if "released_at" in set else "NULL", "'{}'".format(set["block_code"]) if "block_code" in set else "NULL", "'{}'".format(set["block"].replace("'", "''")) if "block" in set else "NULL", "'{}'".format(set["parent_set_code"]) if "parent_set_code" in set else "NULL", set["card_count"], set["digital"] if "digital" in set else "false", set["foil"] if "foil" in set else "false", set["icon_svg_uri"], set["search_uri"])
    print(phppgadmin.execute(sql[:-1]))
def process_cards():
    cachedir = "{}/cards".format(basedir)
    if (not os.path.exists(cachedir)):
        os.makedirs(cachedir)
    phppgadmin.execute("DELETE FROM scr_cards")
    reIDMKM = "https:\/\/www\.cardmarket\.com\/Magic\/Products\/Singles\/(.*?)\?"
    reIDCK = "https:\/\/www\.cardkingdom\.com\/catalog\/item\/(\d*)?\?"
    page = 1
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
        sql = "INSERT INTO scr_cards(id,name,set,idmkm,idck,reprint,image_uri,collector_number,multiverse_id) VALUES"
        for card in cards["data"]:
            idmkm = re.match(reIDMKM, card["purchase_uris"]["magiccardmarket"])
            idmkm = "NULL" if idmkm is None else "'{}'".format(idmkm.group(1))
            idck = re.match(reIDCK, card["purchase_uris"]["card_kingdom"])
            idck = "NULL" if idck is None else idck.group(1)
            sql += "('{}','{}','{}',{},{},{},'{}','{}',{}),".format(card["id"],card["name"].replace("'", "''"),card["set"],idmkm,idck,card["reprint"],card["image_uri"],card["collector_number"],card["multiverse_id"] if "multiverse_id" in card else "NULL")
        print("Pagina {}: {}".format(page, phppgadmin.execute(sql[:-1])))
        if (cards["has_more"]):
            page += 1
        else:
            break

def menu():
    os.system('cls')
    print("==[ DB retriever ]==")
    print("  1. Get editions")
    print("  2. Get cards")
    print("  0. Salir")
    return input("Opcion: ")

options = {
    "1": process_sets,
    "2": process_cards
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
