import csv
import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore
from typing import List
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import click


@click.command()
@click.option("--bil_path", required=True, help="path to a bilhetagem CSV file.")
def ticketing_to_journeys(bil_path):
    """Draw a dot per journey, showing each starting location and colored by the number of legs in the journey."""
    dots = []
    for journey in find_journeys(bil_path):
        # TODO We could filter for journeys ending in a region
        dots.append(
            (
                journey.legs[0].latitude,
                journey.legs[0].longitude,
                len(journey.legs),
            )
        )

    # This is some public Mapbox token I copied from somewhere. It works for me
    # now, but it might eventually expire
    px.set_mapbox_access_token(
        "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw"
    )
    df = pd.DataFrame(dots, columns=["latitude", "longitude", "num_leg"])
    fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", color="num_leg")
    fig.show()


@dataclass
class TicketEvent:
    """One row from the bilhetagem CSV file, only keeping the fields we need."""

    date_time: datetime
    bus_line_code: str
    latitude: float
    longitude: float


@dataclass
class Journey:
    """A journey on public transit made up of at least one leg."""

    card_id: str
    legs: List[TicketEvent]


def find_journeys(bil_path: str) -> List[Journey]:
    """Group ticket events from a CSV file into journeys."""
    card_id = "NUMEROCARTAO"

    journeys = []
    with open(bil_path) as f:
        # Note we collect everything in-memory. It's totally fine for the size
        # of CSV files in the shared data. There are equivalent techniques to
        # performantly handle huge datasets, if we ever need to.
        per_card = defaultdict(list)
        for row in csv.DictReader(f):
            # We could preserve CODVEICULO and other fields if needed
            per_card[row[card_id]].append(
                TicketEvent(
                    date_time=datetime.strptime(row["DATA"], "%d/%m/%Y %H:%M:%S"),
                    bus_line_code=row["CODLINHA"],
                    latitude=float(row["LATITUDE"]),
                    longitude=float(row["LONGITUDE"]),
                )
            )

        for card_id, events in per_card.items():
            journeys.extend(split_into_journeys(card_id, events))

    return journeys


def split_into_journeys(card_id: str, events: List[TicketEvent]) -> List[Journey]:
    """A passenger can board up to four buses in a two-hour window"""
    events.sort(key=lambda event: event.date_time)

    # TODO Can we just use fold?
    journeys = []
    current_journey = Journey(card_id, legs=[events[0]])
    for leg in events[1:]:
        # TODO How's the two-hour window defined -- starting from the first
        # event, or the most recent? (Can somebody ride for a total of 10
        # hours, with 90 minutes between each ticket?)
        if len(current_journey.legs) < 4 and leg.date_time - current_journey.legs[
            0
        ].date_time < timedelta(hours=2):
            current_journey.legs.append(leg)
        else:
            journeys.append(current_journey)
            current_journey = Journey(card_id, legs=[leg])
    journeys.append(current_journey)

    return journeys


if __name__ == "__main__":
    ticketing_to_journeys()
