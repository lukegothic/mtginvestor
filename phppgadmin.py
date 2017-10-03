import requests
from lxml import html

g_session = None
g_debug = False
c_server = {
    "ip": "fotoraton.es",
    "port": "8080",
    "pgport": "5432"
}

def connect():
    global g_session
    g_session = requests.Session()
    try:
        if (g_debug):
            print("Connecting to PHPPGADMIN...")
        resp = g_session.get("http://{}:{}/phppgadmin/{}".format(c_server["ip"], c_server["port"], "redirect.php?subject=server&server=localhost%3A{}%3Aallow&".format(c_server["pgport"])), timeout=5)
        tree = html.fromstring(resp.content)
        username = tree.xpath("//input[@name='loginUsername']")[0]
        password = tree.xpath("//input[@id='loginPassword']")[0]
        loginpostdata = {"subject": "server", "server": "localhost:5432:allow", "loginServer": "localhost:5432:allow", "loginUsername": "postgres", "loginSubmit": "Autenticar"}
        loginpostdata[password.attrib["name"]] = "postgres"
        resp = g_session.post("http://{}:{}/phppgadmin/{}".format(c_server["ip"], c_server["port"], "redirect.php"), loginpostdata)
        if (g_debug):
            print("Connected to PHPPGADMIN")
    except Exception as e:
        print("Server not responding")
        raise Exception()

def execute(sql):
    #TODO: detectar si la sesion se ha caido
    if g_session is None:
        connect()

    return g_session.post("http://{}:{}/phppgadmin/{}".format(c_server["ip"], c_server["port"], "sql.php"), { "server": "localhost:{}:allow".format(c_server["pgport"]), "database": "magic", "search_path": "public", "query": sql })

def query(sql):
    #TODO: detectar si la sesion se ha caido
    if g_session is None:
        connect()

    response = g_session.post("http://{}:{}/phppgadmin/{}".format(c_server["ip"], c_server["port"], "sql.php"), { "server": "localhost:{}:allow".format(c_server["pgport"]), "database": "magic", "search_path": "public", "query": sql })
    if g_debug:
        with open("phppgadmin_lastquery.html", "w") as f:
            f.write(response.text)
    rows = []
    fields = []
    tree = html.fromstring(response.content)
    results = tree.xpath("//body/table/tr")
    for r in results:
        cells = r.xpath("./td")
        if (len(cells) == 0):
            #header
            for field in r.xpath("./th"):
                fields.append(field.text_content())
        else:
            row = {}
            for fieldidx in range(len(fields)):
                row[fields[fieldidx]] = cells[fieldidx].text_content()
            rows.append(row)

    return rows
