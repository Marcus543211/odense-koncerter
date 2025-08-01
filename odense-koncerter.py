import json
import locale
import pickle
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape


locale.setlocale(locale.LC_ALL, "da_DK.utf8")

env = Environment(
    loader=PackageLoader("odense-musik"),
    autoescape=select_autoescape()
)

month_to_no = {"januar": 1, "februar": 2, "marts": 3, "april": 4,
               "maj": 5, "juni": 6, "juli": 7, "august": 8,
               "september": 9, "oktober": 10, "november": 11, "december": 12}


@dataclass
class Concert:
    title: str
    venue: str  # Måske en enum
    date: datetime
    price: str  # Eller int?
    desc: str  # Beskrivelse hvis den eksisterer
    img_src: str
    url: str


def storms() -> list[Concert]:
    """Hent koncerter fra storms pakhus."""
    r = requests.get("https://stormspakhus.dk/events/")
    soup = BeautifulSoup(r.text, features="lxml")
    events = soup.find_all(class_="fl-post-feed-post")
    concerts = []
    current_year = datetime.today().year
    for event in events:
        title = event.find(class_="fl-post-feed-title").a["title"]
        if "koncert" not in title.lower():
            continue
        date_str = event.find(
            class_="fl-post-grid-event-calendar-date").span.string
        date = datetime.strptime(f"{current_year};{date_str}",
                                 "%Y;%B %d @ %H:%M")
        venue = "Storms"
        price = "Gratis"
        desc = event.find(class_="fl-post-feed-content").p.string
        img_src = event.find(class_="fl-post-feed-image").a.img["src"]
        url = event.find(class_="fl-post-feed-title").a["href"]
        concert = Concert(title, venue, date, price, desc, img_src, url)
        concerts.append(concert)
    return concerts


def pd_fetch_page(url, page_no):
    """Hent en enkelt "side" fra posten eller dexter."""
    r = requests.post(
        f"https://{url}/wp-admin/admin-ajax.php",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"action=nkt_event_pagination&page={page_no}&posts_per_page=27&view=box")
    return r.json()


def pd_fetch_pages(url):
    """Hent alle "sider" fra posten eller dexter."""
    # For første side!
    j = pd_fetch_page(url, 1)
    # Antal sider
    page_count = p["data"]["total_pages"]
    # Htmlen som skal behandles
    pages = [j["data"]["html"]]
    # Hent de andre sider
    for i in range(2, page_count+1):
        j = pd_fetch_page(url, i)
        page = j["data"]["html"]
        pages.append(page)
    return pages


def posten() -> list[Concert]:
    """Hent alle koncerter fra posten."""
    pages = pd_fetch_pages("postenlive.dk")
    # Hiv koncerterne ud
    concerts = []
    for page in pages:
        soup = BeautifulSoup(page, features="lxml")
        events = soup.select(".event-box")
        for event in events:
            goop = event.select_one("div > div > div")
            title = goop.select_one(".bde-heading").string.strip()
            date_str = goop.select_one("div div:nth-of-type(3) div").string.strip()
            date = datetime.strptime(date_str.strip(), "%d. %B %Y")
            venue = "Posten"
            price = goop.select_one("div div:nth-of-type(4) span").string.strip()
            desc = goop.select_one("div div:nth-of-type(2)").string.strip()
            img_src = event.find(class_="breakdance-image-object")["src"]
            url = event.div.a["href"]
            concert = Concert(title, venue, date, price, desc, img_src, url)
            concerts.append(concert)
    return concerts


def dexter() -> list[Concert]:
    """Hent alle koncerter fra dexter."""
    pages = pd_fetch_pages("dexter.dk")
    # Hiv koncerterne ud
    concerts = []
    for page in pages:
        soup = BeautifulSoup(page, features="lxml")
        events = soup.select(".event-box")
        for event in events:
            goop = event.select_one("div > div > div")
            title = goop.select_one(".bde-heading").string.strip()
            date_str = goop.select_one("div div:nth-of-type(2) div").string.strip()
            date = datetime.strptime(date_str.strip(), "%d. %B %Y")
            venue = "Dexter"
            price = goop.select_one("div div:nth-of-type(3) span").string.strip()
            desc = goop.select_one("div div:nth-of-type(1)").string.strip()
            img_src = event.find(class_="breakdance-image-object")["src"]
            url = event.div.a["href"]
            concert = Concert(title, venue, date, price, desc, img_src, url)
            concerts.append(concert)
    return concerts


def kulturmaskinen() -> list[Concert]:
    """Hent alle koncerter fra kulturmaskinen."""
    r = requests.get(
        "https://api.uheadless.com/api"
        "?token=6dc733b1-53a0-4c6a-b469-8ae912316dc4&depth=6&lang=en-us"
        "&postdata=JTdCJTIybGltaXQlMjIlM0E5OTk5OSUyQyUyMnF1ZXJ5JTIyJTNB"
        "JTdCJTIyY29udGVudFR5cGVBbGlhcyUyMiUzQSUyMmJpbGxldHRlbkV2ZW50JT"
        "IyJTJDJTIycGFyZW50SWQlMjIlM0ElN0IlMjJuZSUyMiUzQTEyMDQlN0QlMkMl"
        "MjJwcm9wZXJ0aWVzLmJpbGxldHRlbl9kYXRhLnNob3dzLjAlMjIlM0ElN0IlMj"
        "JleGlzdHMlMjIlM0ExJTdEJTdEJTJDJTIyc29ydEJ5JTIyJTNBJTIycHJvcGVy"
        "dGllcy5iaWxsZXR0ZW5fZGF0YS5zaG93cy4wLnNob3dfdGltZSUyMiUyQyUyMn"
        "NvcnQlMjIlM0ElMjJhc2MlMjIlN0Q")
    events = r.json()
    concerts = []
    for event in events:
        # Frasorter alle events der ikke er musik.
        if event["properties"]["category_value"] != "MUSIK":
            continue
        #if len(event["properties"]["billetten_data"]["shows"]) != 1:
        #    print("Oh no")
        #    pprint(event)
        title = event["properties"]["event_name"]
        date_str = event["properties"]["billetten_data"]["shows"][0]["show_time"]
        date = datetime.fromisoformat(date_str)
        venue = event["properties"]["promoter"]["nodeName"]
        price = event["properties"]["billetten_data"]["shows"][0]["prices"][0]["min_price"]
        desc = event["properties"]["billetten_data"]["event_notes"]
        img_src = event["properties"]["billetten_data"]["event_images"]["large"]
        url = "https://kulturmaskinen.dk/events/" + event["urlSegment"]
        concert = Concert(title, venue, date, price, desc, img_src, url)
        concerts.append(concert)
    return concerts


def liveculture() -> list[Concert]:
    """Hent alle koncerter fra live culture."""
    r = requests.get("https://liveculture.dk/")
    soup = BeautifulSoup(r.text, features="lxml")
    sis = soup.select(".searchItem")
    events = soup.select(".card")
    concerts = []
    for event in events:
        title = event.select_one(".singleBoxTitle").span.string
        # Fjern "gavekort" eventen
        if title == "Gavekort":
            continue
        date_str = event.select_one(".heroLabels__single--date").string
        first_date = date_str.split(" - ")[0]
        date = datetime.strptime(first_date, "%d.%m.%y")
        venue = event.select_one(".heroLabels__single--venue").string
        price = event.select(".ticketButton__time")[0].string
        desc = event.select_one(".singleBoxCity").string
        img_src = event.select_one("a > .cover")["data-src"]
        url = event.a["href"]
        concert = Concert(title, venue, date, price, desc, img_src, url)
        for si in sis:
            if si.div.div.string.strip() == title:
                # Frasorter alt der er comedy
                if not any("Comedy" == tag.string for tag in si.select(".searchTag")):
                    concerts.append(concert)
                    break
    return concerts


def all_concerts() -> list[Concert]:
    """Hent alle koncerter og returner i sorteret kronologisk rækkefølge."""
    concerts = []
    concerts.extend(storms())
    concerts.extend(posten())
    concerts.extend(dexter())
    concerts.extend(kulturmaskinen())
    concerts.extend(liveculture())
    concerts.sort(key=lambda c: c.date)
    return concerts


def main():
    print("Downloader")
    concerts = all_concerts()
    print("Færdig!")
    
    print("Udskriver siden")
    template = env.get_template("index.html")
    now = datetime.now()
    with open("index.html", "w") as f:
        f.write(template.render(concerts=concerts, now=now))
    with open("cache.pickle", "w") as f:
        pickle.dump(concerts, f)
    print("Færdig")


if __name__ == "__main__":
    main()

