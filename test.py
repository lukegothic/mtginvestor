import csv
with open("__offlinecache__/editions.csv") as csvfile:
    reader = csv.DictReader(csvfile, delimiter="|")
    for row in reader:
        #print(row['id'], row['name'], row['url'])
        print(row)
