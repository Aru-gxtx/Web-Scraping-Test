"""
Write a program that grabs the full HTML from the following URL:

>>> url = "http://olympus.realpython.org/profiles/dionysus"
Then use .find() to display the text following Name: and Favorite Color: (not including any leading spaces or trailing HTML tags that might appear on the same line).
"""

from urllib.request import urlopen

url = "http://olympus.realpython.org/profiles/dionysus"

page = urlopen(url)

html_bytes = page.read()
html = html_bytes.decode("utf-8")

name_index = html.find("<h2>")
start_index = name_index + len("<h2>")
end_index = html.find("</h2>")

name = html[start_index:end_index]

fav_col_index = html.find("<body>")
start_index = fav_col_index + len("<body>")
end_index = html.find("</body>")

fav_col = html[start_index:end_index].split("\n")[14]

print(name)
print(fav_col)