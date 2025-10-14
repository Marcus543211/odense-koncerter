import concurrent.futures
import io
import locale
from datetime import datetime
from pathlib import Path
from pprint import pprint

import requests
from jinja2 import Environment, PackageLoader, select_autoescape
from PIL import Image

import scrapers
from concert import Concert, load_concerts, dump_concerts


# MUST BE RUN IN SAME DIRECTORY AS THIS FILE


# TODO
# - Genrer ville være fedt
# - Black-list til alt som ikke er koncerter (som systemet ikke fanger selv)
# - Gør så man kan køre programmet fra andre mapper end den filen er i
# - Brug tråde til at lave miniaturer (thumbnails)
# - En attribut der fortæller om koncerter er udsolgte?
# - Nogle steder er der ikke år med i datoen, her antager jeg at det er i år
#   men det kunne også være at det var næste år...
# - En side der lister festivaler i Odense?
# - Links til/En side til de forskellige spillesteder?
# - Nashville nights??


locale.setlocale(locale.LC_ALL, "da_DK.utf8")


def get_image(url) -> Image:
    """Hent billede fra URL."""
    r = requests.get(url, stream=True)
    f = io.BytesIO(r.content)
    return Image.open(f)


def make_thumbnail(concert: Concert) -> str:
    """Hent koncertens billede og gem optimeret miniature. Returner ny URL."""
    name = f"{concert.date.date()} - {concert.venue} - {concert.title}.webp"
    # Fjern alle tegn der ikke må være i filnavne
    escaped_name = name.translate(str.maketrans("", "", "<>:\"/\\|?*"))
    path = Path("images") / escaped_name
    if not path.exists():
        img = get_image(concert.img_url)
        if img.width < 768:
            print(f"WARN: Image < 768px, {name}")
        if img.width < img.height:
            print(f"WARN: Portrait image, {name}")
        img.thumbnail((768, 768))
        img.save(path, "WebP", lossless=False, quality=80)
    concert.img_url = str(path)
    return str(path)


def make_thumbnails(concerts: list[Concert]):
    """Lav miniature til koncerterne og opdater billede-URL'erne."""
    print("Laver thumbnails...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(make_thumbnail, concerts)
    print("Færdig med thumbnails!")


def format_price(f: float) -> str:
    format_str = "%i" if f.is_integer() else "%.2f"
    return locale.format_string(format_str, f, grouping=True) + " kr."


def make_html(out_path, concerts: list[Concert]):
    """Lav en side med de givne koncerter og gem ved stien."""
    print("Udskriver siden...")
    env = Environment(
        loader=PackageLoader("odense-koncerter"),
        autoescape=select_autoescape()
    )
    env.globals["format_price"] = format_price
    template = env.get_template("index.html")
    now = datetime.now()
    with open(out_path, "w") as file:
        file.write(template.render(now=now, concerts=concerts))
    print("Færdig! Siden er udskrevet til", out_path)


def save_concerts(out_path, concerts: list[Concert]):
    """Gem koncerterne som JSON ved stien."""
    print("Gemmer som JSON...")
    with open(out_path, "w") as file:
        dump_concerts(concerts, file)
    print("Færdig! Koncerterne er gemt")


def main():
    concerts = scrapers.all_concerts()
    print()
    # Gemmer før thumbnails for at gemme de oprindelige URL'er til billederne.
    save_concerts("concerts.json", concerts)
    print()
    make_thumbnails(concerts)
    print()
    make_html("index.html", concerts)


if __name__ == "__main__":
    main()

