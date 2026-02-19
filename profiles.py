from urllib.request import urlopen

url = "http://olympus.realpython.org/profiles"

page = urlopen(url)

html_bytes = page.read()
html = html_bytes.decode("utf-8")

print(url + html.split("\n")[10].split("profiles")[1].split("\"")[0])
print(url + html.split("\n")[12].split("profiles")[1].split("\"")[0])
print(url + html.split("\n")[14].split("profiles")[1].split("\"")[0])