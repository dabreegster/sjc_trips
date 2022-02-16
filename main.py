import csv
import click


@click.command()
@click.option("--bil_path", required=True, help="path to a bilhetagem CSV file.")
def ticketing_to_trips(bil_path):
    with open(bil_path) as f:
        for row in csv.DictReader(f):
            print(row)


if __name__ == "__main__":
    ticketing_to_trips()
