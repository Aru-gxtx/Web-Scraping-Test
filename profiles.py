"""
Write a program that grabs the full HTML from the page at the URL http://olympus.realpython.org/profiles.

Using Beautiful Soup, print out a list of all the links on the page by looking for HTML tags with the name a and retrieving the value taken on by the href attribute of each tag.

The final output should look like this:

http://olympus.realpython.org/profiles/aphrodite
http://olympus.realpython.org/profiles/poseidon
http://olympus.realpython.org/profiles/dionysus
Make sure that you only have one slash (/) between the base URL and the relative URL.
"""

from urllib.request import urlopen

url = "http://olympus.realpython.org/profiles"

page = urlopen(url)

html_bytes = page.read()
html = html_bytes.decode("utf-8")

print(url + html.split("\n")[10].split("profiles")[1].split("\"")[0])
print(url + html.split("\n")[12].split("profiles")[1].split("\"")[0])
print(url + html.split("\n")[14].split("profiles")[1].split("\"")[0])