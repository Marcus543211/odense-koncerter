import locale
import re
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from concert import Concert, load_concerts


locale.setlocale(locale.LC_ALL, "da_DK.utf8")


re_srcset = re.compile(r"([^ ,]+)(?: (\d+)[wx])?")

re_num = re.compile(r"\d+")


def best_from_srcset(srcset: str) -> str:
    """Returner URL til det bedste billede i srcset."""
    matches = re_srcset.findall(srcset)
    # If no width is given it is 1x.
    (_, url) = max((int(width or 1), url) for (url, width) in matches)
    return url


def best_from_img(img) -> str:
    """Returner URL til det bedste billede fra <img>."""
    assert img.name == "img"
    if not img.has_attr("srcset"):
        return img["src"]
    return best_from_srcset(img["srcset"])


def get_price(s: str) -> int:
    """Udvinder prisen fra prisskilt fx "1.295,00 kr"."""
    s = s.lower()
    if "gratis" in s:
        return 0.0
    if "udsolgt" in s:
        return None
    c_s = locale.delocalize(s)
    price = re_num.search(c_s).group()
    return int(price)


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
        venue = "Storms Pakhus"
        price = 0
        desc = event.find(class_="fl-post-feed-content").p.string
        img_url = best_from_img(event.find(class_="fl-post-feed-image").a.img)
        url = event.find(class_="fl-post-feed-title").a["href"]
        concert = Concert(title, venue, date, price, desc, img_url, url)
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
    first_page = pd_fetch_page(url, 1)
    page_count = first_page["data"]["total_pages"]
    pages = [first_page["data"]["html"]]
    # Hent de andre sider
    for i in range(2, page_count+1):
        page = pd_fetch_page(url, i)
        page_html = page["data"]["html"]
        pages.append(page_html)
    return pages


def posten() -> list[Concert]:
    """Hent alle koncerter fra posten."""
    pages = pd_fetch_pages("postenlive.dk")
    # Hiv koncerterne ud
    events = []
    for page in pages:
        soup = BeautifulSoup(page, features="lxml")
        page_events = soup.select(".event-box")
        events.extend(page_events)
    concerts = []
    for event in events:
        goop = event.select_one("div > div > div")
        title = goop.select_one(".bde-heading").string.strip()
        date_str = goop.select_one("div div:nth-of-type(3) div").string.strip()
        date = datetime.strptime(date_str, "%d. %B %Y")
        venue = "Posten"
        price = get_price(goop.select_one("div div:nth-of-type(4) span").string)
        desc = goop.select_one("div div:nth-of-type(2)").string.strip()
        img_url = best_from_img(event.find(class_="breakdance-image-object"))
        url = event.div.a["href"]
        concert = Concert(title, venue, date, price, desc, img_url, url)
        concerts.append(concert)
    return concerts


def dexter() -> list[Concert]:
    """Hent alle koncerter fra dexter."""
    pages = pd_fetch_pages("dexter.dk")
    # Hiv koncerterne ud
    events = []
    for page in pages:
        soup = BeautifulSoup(page, features="lxml")
        page_events = soup.select(".event-box")
        events.extend(page_events)
    concerts = []
    for event in events:
        goop = event.select_one("div > div > div")
        title = goop.select_one(".bde-heading").string.strip()
        date_str = goop.select_one("div div:nth-of-type(2) div").string.strip()
        date = datetime.strptime(date_str, "%d. %B %Y")
        venue = "Dexter"
        price = get_price(goop.select_one("div div:nth-of-type(3) span").string)
        desc = goop.select_one("div div:nth-of-type(1)").string.strip()
        img_url = best_from_img(event.find(class_="breakdance-image-object"))
        url = event.div.a["href"]
        concert = Concert(title, venue, date, price, desc, img_url, url)
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
        title = event["properties"]["event_name"]
        if len(event["properties"]["billetten_data"]["shows"]) != 1:
            print(f"WARN: {title} har flere shows")
        date_str = event["properties"]["billetten_data"]["shows"][0]["show_time"]
        date = datetime.fromisoformat(date_str)
        venue = event["properties"]["promoter"]["nodeName"]
        price = event["properties"]["billetten_data"]["shows"][0]["prices"][0]["min_price"]
        desc = event["properties"]["billetten_data"]["event_notes"]
        img_url = event["properties"]["billetten_data"]["event_images"]["large"]
        url = "https://kulturmaskinen.dk/events/" + event["urlSegment"]
        concert = Concert(title, venue, date, price, desc, img_url, url)
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
        try:
            price_tag = event.select(".ticketButton__time")[0].string
        except IndexError:
            # Af en eller anden grund manglede en koncert en pris...
            price = None
        finally:
            # Nogle koncerter skal man vælge tidspunkt. Der er prisen et andet sted.
            if ":" in price_tag:
                price_tag = event.select_one(".boxtitle__pricing__amount").string
            price = get_price(price_tag)
        desc = event.select_one(".singleBoxCity").string
        img_url = best_from_srcset(event.select_one("a > .cover")["data-srcset"])
        url = event.a["href"]
        concert = Concert(title, venue, date, price, desc, img_url, url)
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
        # Lidt ligegyldig info om hvilken sal i Odeon.
        desc = event.select_one(".mt-6 > span").string
        img_url = "https://odeonodense.dk" + best_from_srcset(event.source["data-srcset"])
        url = "https://odeonodense.dk" + event["href"]
        # Hent koncertsiden for at finde prisen
        pr = requests.get(url)
        psoup = BeautifulSoup(pr.text, features="lxml")
        price = get_price(next(psoup.select_one(".mt-8").strings))
        concert = Concert(title, venue, date, price, desc, img_url, url)
        concerts.append(concert)
    return concerts


def grandhotel() -> list[Concert]:
    """Hent alle koncerter fra Grand Hotel."""
    r = requests.get("https://www.grandodense.dk/event-koncert/")
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")
    events = soup.select(".Preview_block__16Zmu .Preview_block__16Zmu")
    concerts = []
    re_date = re.compile(r"(\d+. \w+ \d+)")
    re_price = re.compile(r"\d+,-")
    for event in events:
        # Fjern begivenheder fra resturanten
        if not event.a["href"].startswith("/event-koncert/"):
            continue
        title = event.h1.string
        date_str = event.find(string=re_date).string
        # Tag kun (første) datoen ignorer alt andet
        date_str = re_date.search(date_str)[0]
        date = datetime.strptime(date_str, "%d. %B %Y")
        venue = "Grand Hotel"
        desc = ""
        # En enkelt event havde en video i stedet for et billede...
        # Meeeen det var ikke en koncert
        if event.img is None:
            print("WARN: No image for", title, "it will not be added")
            continue
        img_url = best_from_img(event.img)
        url = "https://grandodense.dk" + event.a["href"]
        # Hent koncertsiden for at finde prisen
        price = get_price(event.find(string=re_price))
        concert = Concert(title, venue, date, price, desc, img_url, url)
        concerts.append(concert)
    return concerts


def tcbunderground() -> list[Concert]:
    """Hent alle koncerter fra TCB Underground."""
    r = requests.get("https://tcbunderground.com/arrangementer")
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")
    events = soup.select("tbody tr")
    concerts = []
    for event in events:
        # Prisen og billedet er kun på billetsiden
        # Billetsiden kræver dog JS så jeg henter dataen direkte
        url = event.a["href"]
        name = url.split("/")[-2]
        info_url = f"https://checkoutapi.ticketbutler.io/api/events/title/{name}/"
        headers = {"Origin": "https://tcbunderground.ticketbutler.io",
                   "Referer": "https://tcbunderground.ticketbutler.io/"}
        er = requests.get(info_url, headers=headers)
        info = er.json()
        title = info["title"]
        venue = "TCB Underground"
        date_str = info["start_date"]
        date = datetime.fromisoformat(date_str).replace(tzinfo=None)
        # Jeg kunne godt gemme beskrivelsen men jeg bruger det ikke...
        desc = ""
        img_url = info["images"][0]["image"]
        # Hent koncertsiden for at finde prisen
        price = info["ticket_types"][0]["price"]
        concert = Concert(title, venue, date, price, desc, img_url, url)
        concerts.append(concert)
    return concerts


def vearket() -> list[Concert]:
    """Hent alle koncerter fra Odense Værket."""
    r = requests.get("https://odensevaerket.dk/kultur-musikhus/")
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")
    events = soup.select(".products > li")
    concerts = []
    current_year = datetime.today().year
    for event in events:
        title = event.h2.string.removesuffix(" – Entrébillet").split(" – ", 1)[1]
        date_str = event.h2.string.split(" – ")[0]
        date_str = re.sub(r"-\d+", ".", date_str)
        date = datetime.strptime(f"{date_str};{current_year}", "%d. %B;%Y")
        venue = "Odense Værket"
        desc = ""
        img_url = best_from_img(event.img)
        url = event.select_one(".woocommerce-LoopProduct-link")["href"]
        # Her kan jeg se om koncerten er udsolgt.
        #if event.select_one(".berocket_better_labels") is not None:
        price = get_price(event.select_one(".price").text)
        concert = Concert(title, venue, date, price, desc, img_url, url)
        concerts.append(concert)
    return concerts


def studenterhuset() -> list[Concert]:
    """Hent alle koncerter fra Studenterhus Odense."""
    # Vælg rigtig arrangør og kun musik
    data = {"pagenum":0, "ytfiltercategories": "2", "ytfiltercity": "",
            "ytfilterdate": "", "ytfiltersearch": "", "ytfilterarrid": "671"}
    # Man SKAL have de rigtige headers eller vil den ikke gøre noget...
    headers = {"origin": "https://www.yourticket.dk", "referer": "https://www.yourtickets.dk",
               "key": "3-9D8DC9C1-576A-4727-890C-5F140E4D03F5"}
    r = requests.post("https://publicapi.yourticket.dk/Events/GetEventsForOverview",
                      headers=headers, json=data)
    concerts = []
    for event in r.json():
        title = event["Name"].removesuffix(" // Studenterhus Odense")
        date_str = event["StartDate"]
        date = datetime.strptime(date_str, "%d. %B %Y kl. %H:%M")
        venue = "Studenterhus Odense"
        desc = event["ShortDescription"]
        img_url = event["Image"]
        url = "https://www.yourticket.dk" + event["YTRoute"]
        price = event["FromPrice"]
        concert = Concert(title, venue, date, price, desc, img_url, url)
        concerts.append(concert)
    return concerts


def extra() -> list[Concert]:
    """Indlæser de ekstra manuelt indstastede koncerter."""
    try:
        now = datetime.now()
        with open("extra.json", "r") as file:
            concerts = load_concerts(file)
        # Fjern gamle koncerter
        upcoming = [c for c in concerts if c.date >= now]
        return upcoming
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
    print("... fra Grand Hotel")
    concerts.extend(grandhotel())
    print("... fra TCB Underground")
    concerts.extend(tcbunderground())
    print("... fra Odense Værket")
    concerts.extend(vearket())
    print("... fra Studenterhus Odense")
    concerts.extend(studenterhuset())
    print("... fra ekstralisten")
    concerts.extend(extra())
    print(f"Alle koncerter er hentet ({len(concerts)})")
    concerts.sort(key=lambda c: (c.date, c.venue, c.title))
    today = datetime.now().date()
    for c in concerts:
        if c.date.date() < today:
            print(f"WARN: {c.title} is an outdated concert")
    return concerts

