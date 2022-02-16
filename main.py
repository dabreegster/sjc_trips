import csv
import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore
from typing import List
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import click


# This is some public Mapbox token I copied from somewhere. It works for me now, but it might eventually expire
MAPBOX_TOKEN = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw"


@click.command()
@click.option("--bil_path", required=True, help="path to a bilhetagem CSV file.")
def ticketing_to_journeys(bil_path):
    card_id = "NUMEROCARTAO"

    with open(bil_path) as f:
        per_card = defaultdict(list)
        for row in csv.DictReader(f):
            per_card[row[card_id]].append(
                TicketEvent(
                    # TODO Verify if the data is DD/MM or MM/DD
                    date_time=datetime.strptime(row["DATA"], "%d/%m/%Y %H:%M:%S"),
                    bus_line_code=row["CODLINHA"],
                    latitude=row["LATITUDE"],
                    longitude=row["LONGITUDE"],
                )
            )

        # Draw a dot per starting location, coloring by the number of legs
        dots: List[(float, float, int)] = []

        for card_id, events in per_card.items():
            journeys = split_into_journeys(card_id, events)
            for journey in journeys:
                # TODO latitude/longitude are already floats; not sure why we
                # have to force that again. But without it, plotly blows up
                dots.append(
                    (
                        float(journey.legs[0].latitude),
                        float(journey.legs[0].longitude),
                        len(journey.legs),
                    )
                )

        px.set_mapbox_access_token(MAPBOX_TOKEN)
        df = pd.DataFrame(dots, columns=["latitude", "longitude", "num_leg"])
        fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", color="num_leg")
        fig.show()


@dataclass
class TicketEvent:
    date_time: datetime
    bus_line_code: str
    latitude: float
    longitude: float


@dataclass
class Journey:
    card_id: str
    legs: List[TicketEvent]


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
