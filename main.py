import csv
from typing import List
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
import click


@click.command()
@click.option("--bil_path", required=True, help="path to a bilhetagem CSV file.")
def ticketing_to_trips(bil_path):
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

        for card_id, events in per_card.items():
            trips = split_into_trips(events)


@dataclass
class TicketEvent:
    date_time: datetime
    bus_line_code: str
    latitude: float
    longitude: float


def split_into_trips(events: List[TicketEvent]) -> List[List[TicketEvent]]:
    print(events)
    # TODO
    return None


if __name__ == "__main__":
    ticketing_to_trips()
