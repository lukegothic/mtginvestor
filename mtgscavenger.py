import requests
# jQuery.get("http://www.mtgscavenger.com/uncommonvalue", function(d) { var a = []; jQuery(d).find("a.cluetip + div a").each((i, img) => a.push(img.href.split("%2F")[6].replace("i.html%3F_from%3DR40%26_nkw%3D", "").replace("%26LH_Complete%3D1%26LH_Sold%3D1%26rt%3Dnc", "").replace(/\+/g, " ").replace(/\%27/g,"'").replace("%C3%86", "AE").replace("%28", "[").replace("%29", "]"))); console.log(a.join("\n")); })
req = requests.get("http://www.mtgscavenger.com/uncommonvalue")
print(req.text)
