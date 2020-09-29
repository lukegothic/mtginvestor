# para usarlo con sqlite3, devuelve consultas en plan dict python
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d