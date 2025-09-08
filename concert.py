import json
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Concert:
    title: str
    venue: str  # Måske en enum
    date: datetime
    price: int | None
    sold_out: bool
    desc: str  # Beskrivelse hvis den eksisterer
    img_url: str
    url: str

    @classmethod
    def from_json(cls, json: dict):
        # Behold alt men parse datoen til en datetime
        concert = json | {"date": datetime.fromisoformat(json["date"])}
        return cls(**concert)

    def as_json(self) -> dict:
        # JSONen kan ikke indeholde en datetime så erstat med streng
        return asdict(self) | {"date": self.date.isoformat()}


def load_concerts(file):
    """Læs koncerter fra JSON fil."""
    concerts_json = json.load(file)
    concerts = [Concert.from_json(c) for c in concerts_json]
    return concerts


def dump_concerts(concerts: list[Concert], file):
    """Skriv koncerter til JSON fil."""
    concerts_json = [concert.as_json() for concert in concerts]
    json.dump(concerts_json, file)

