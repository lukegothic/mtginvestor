import phppgadmin

a = phppgadmin.query("select * from ck_editions")
for x in a:
    print(x["name"])
