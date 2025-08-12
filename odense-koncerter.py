import locale
import re
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape


# TODO
# - ODEONs koncerter mangler pris
# - Genrer ville være fedt
# - Mindre billeder... Firefox siger 250 MB for at vise siden!
# - Black-list til alt som ikke er koncerter (som systemet ikke fanger selv)


locale.setlocale(locale.LC_ALL, "da_DK.utf8")


@dataclass
class Concert:
    title: str
    venue: str  # Måske en enum
    date: datetime
    price: str  # Eller int?
    desc: str  # Beskrivelse hvis den eksisterer
    img_src: str
    url: str

    @classmethod
    def from_json(cls, json: dict):
        concert = json | {"date": datetime.fromisoformat(json["date"])}
        return cls(**concert)

    def as_json(self) -> dict:
        return asdict(self) | {"date": self.date.isoformat()}


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
        title = title.removesuffix(" // Gratis Koncert")
        date_str = event.find(
            class_="fl-post-grid-event-calendar-date").span.string
        # Året tilføjes til datoen så den kan parses korrekt.
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
    p = pd_fetch_page(url, 1)
    # Antal sider
    page_count = p["data"]["total_pages"]
    # Htmlen som skal behandles
    pages = [p["data"]["html"]]
    # Hent de andre sider
    for i in range(2, page_count+1):
        p = pd_fetch_page(url, i)
        page = p["data"]["html"]
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
    """Hent koncerter fra Live Culture (undtaget Magasinet og Odeon)."""
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
        # Fjern koncerter fra magasinet; de bliver også hentet fra kulturmaskinen.
        if venue == "Magasinet":
            continue
        # Koncerter fra Odeon hentes seperat.
        if venue == "ODEON":
            continue
        price = event.select(".ticketButton__time")[0].string
        # Nogle koncerter skal man vælge tidspunkt. For dem findes prisen andensteds.
        if ":" in price:
            price = event.select_one(".boxtitle__pricing__amount").string
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


def odeon() -> list[Concert]:
    """Hent alle koncerter fra Odeon."""
    r = requests.get("https://odeonodense.dk/kalender")
    soup = BeautifulSoup(r.text, features="lxml")
    # Her vælger jeg allerede kun koncerter.
    events = soup.find_all("a", {"data-js-filter-item": re.compile(r"koncert")})
    concerts = []
    for event in events:
        title = event.h2.string
        last_date_str = event.select(".text-link")[-1].string.split(" - ")[-1]
        date = datetime.strptime(last_date_str, "%A %d. %b %Y")
        venue = "ODEON"
        price = "???"
        # Lidt ligegyldig info om hvilken sal i Odeon.
        desc = event.select_one(".mt-6 > span").string
        img_src = "https://odeonodense.dk" + event.img["src"]
        url = "https://odeonodense.dk" + event["href"]
        concert = Concert(title, venue, date, price, desc, img_src, url)
        concerts.append(concert)
    return concerts


def extra() -> list[Concert]:
    """Indlæser de ekstra manuelt indstastede koncerter."""
    try:
        with open("extra.json", "r") as f:
            concerts_json = json.load(f)
        concerts = [Concert.from_json(c) for c in concerts_json]        
        return concerts
    except FileNotFoundError:
        return []


def all_concerts() -> list[Concert]:
    """Hent alle koncerterne og returner i kronologisk rækkefølge."""
    print("Henter koncerter")
    concerts = []
    print("... fra Storms")
    concerts.extend(storms())
    print("... fra Posten")
    concerts.extend(posten())
    print("... fra Dexter")
    concerts.extend(dexter())
    print("... fra Kulturmaskinen")
    concerts.extend(kulturmaskinen())
    print("... fra Live Culture")
    concerts.extend(liveculture())
    print("... fra Odeon")
    concerts.extend(odeon())
    print("... fra ekstralisten")
    concerts.extend(extra())
    print(f"Alle koncerter er hentet ({len(concerts)})")
    concerts.sort(key=lambda c: (c.date, c.venue, c.title))
    return concerts


def generate_html(out_path, concerts: list[Concert]):
    """Generer en side med de givne koncerter og gem ved stien."""
    print("Udskriver siden...")
    env = Environment(
        loader=PackageLoader("odense-koncerter"),
        autoescape=select_autoescape()
    )
    template = env.get_template("index.html")
    now = datetime.now()
    with open(out_path, "w") as f:
        f.write(template.render(concerts=concerts, now=now))
    print("Færdig! Siden er udskrevet til", out_path)


def save_as_json(out_path, concerts: list[Concert]):
    """Gem koncerterne som JSON ved stien."""
    print("Gemmer som JSON...")
    concerts_json = [concert.as_json() for concert in concerts]
    with open(out_path, "w") as f:
        json.dump(concerts_json, f)
    print("Færdig! Koncerterne er gemt")


def main():
    concerts = all_concerts()
    print()
    generate_html("index.html", concerts)
    print()
    save_as_json("concerts.json", concerts)


if __name__ == "__main__":
    main()

