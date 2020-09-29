from datetime import datetime
def isodatetodatetime(isodate):
    return datetime.strptime(isodate, '%Y-%m-%dT%H:%M:%S%z')