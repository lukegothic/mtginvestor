import requests
from lxml import html
import hashlib
import re
import os

g_session = None
g_debug = False
c_server = {
    "ip": "192.168.1.14",
    "port": "8080",
    "pgport": "5432",
    "db": "magic"
}
cachedir = "__mycache__/phppgadmin"
if not os.path.exists(cachedir):
    os.makedirs(cachedir)

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
def getresults(sql):
    uniqueid = hashlib.sha1(sql.encode()).hexdigest()
    #TODO: detectar si la sesion se ha caido
    if g_session is None:
        connect()
    filete = "{}/{}.html".format(cachedir, uniqueid)
    try:
        with open(filete, "rb") as f:
            data = f.read()
    except:
        response = g_session.post("http://{}:{}/phppgadmin/{}".format(c_server["ip"], c_server["port"], "sql.php"), { "server": "localhost:{}:allow".format(c_server["pgport"]), "database": "magic", "search_path": "public", "query": sql })
        data = response.content
        with open(filete, "wb") as f:
            f.write(data)
    return data
def execute(sql):
    if g_session is None:
        connect()
    response = g_session.post("http://{}:{}/phppgadmin/{}".format(c_server["ip"], c_server["port"], "sql.php"), { "server": "localhost:{}:allow".format(c_server["pgport"]), "database": "magic", "search_path": "public", "query": sql })
    if response.ok:
        with open("phppgadmin_lastquery.html", "wb") as f:
            f.write(response.content)
            tree = html.fromstring(response.content)
            error = tree.xpath("//pre/text()")
            if (len(error) > 0):
                return error[0]
            else:
                try:
                    results = tree.xpath("//body/p[1]/text()")[0]
                    return (int)(re.match("\d*", results).group(0))
                except:
                    return 0
    else:
        connect()
        return execute(sql)
def count(sql):
    return len(query(sql))
def query(sql):
    response = getresults(sql)
    rows = []
    fields = []
    tree = html.fromstring(response)
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
