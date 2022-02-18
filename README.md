# Transit dataviz examples for São José dos Campos

![Example output](num_legs_viz.gif)

This is a small example of how to transfom public transit ticketing data into a
higher-level structure, and use the result for easier data visualization.

## Running the code

One-time installation:

1. Install [poetry](https://python-poetry.org), a tool that manages Python
	 dependencies much more reproducibly than `pip`, `conda`, etc
2. Clone the repository: `git clone https://github.com/dabreegster/sjc_trips`
3. Enter the directory: `cd sjc_trips`
4. Install dependencies: `poetry install`

Then you can group any BIL CSV file into journeys by running:

`poetry run python main.py --bil_path ~/Downloads/Sharing_files/Data/bil_2019-09-01.csv`

### Working on the code

To auto-format the code: `poetry run black main.py`

To run the type-checker to detect possible problems: `poetry run mypy main.py`

## Summary of recommendations

1.  Transform raw data into a higher-level structure first
2.  Dataframes / 2D tables are not always the best tool
3.  Solve specific use cases, then try to generalize a solution later

## Methodology

The input data represents people (with a unique `card_id`) tapping onto a bus.
(Note the ticket event could happen after the bus leaves the stop.)

| date_time           | card_id | bus_line | lat, lng |
| ------------------- | ------- | -------- | -------- |
| 01/09/2019 00:30:56 | 123     | route 1  | ...      |
| 01/09/2019 00:50:30 | 123     | route 2  | ...      |
| 01/09/2019 09:20:30 | 123     | route 3  | ...      |
| 01/09/2019 00:20:00 | 456     | route 1  | ...      |

But the transit agency only charges per "journey" -- someone can tap onto 4
buses in a two-hour window. So rather than operate on the raw ticket data,
let's transform into a higher-level structure that models the domain better:

```python
@dataclass
class Journey:
    """A journey on public transit made up of at least one leg."""

    card_id: str
    legs: List[TicketEvent]
```

For the example above, we would have 3 journeys taken by 2 people:

```
[
  {
    "card_id": 123,
    "legs": [
      {"date_time": "01/09/2019 00:30:56", "bus_line": "route 1"},
      {"date_time": "01/09/2019 00:50:30", "bus_line": "route 2"},
    ]
  },
  {
    "card_id": 123,
    "legs": [
      {"date_time": "01/09/2019 09:20:30", "bus_line": "route 3"}
    ]
  },
  {
    "card_id": 456,
    "legs": [
      {"date_time": "01/09/2019 00:20:00", "bus_line": "route 1"}
    ]
  }
```

It's much easier to ask questions about journeys than ticketing events. To
figure out where people start multi-leg journeys going to some particular
destination, we can first filter trips by the last `bus_line` --
`journey.legs[-1].bus_line` in Python. (Since we have no data for where a
passenger alights, the position where they boarded their last bus might not be
helpful, but if a particular route serves the destination, we can just use
that.) Then we can look at the boarding location of their first leg, and maybe
even filter for people with at least 2 or 3 legs in their journey.

### Nested data vs dataframes

Note that a journey is expressed with nested fields -- it has a `card_id`, then
a **list** of `legs`. Each `leg` has a `date_time`, `bus_line`, position, etc.
I think it's critical to model a domain with hierarchical data like this
sometimes, because it more naturally maps onto "nouns" or objects in the real
world.

Alternatively, we could force everything into a 2D table or data-frame:

| date_time           | card_id | bus_line | lat, lng | journey_id |
| ------------------- | ------- | -------- | -------- | ---------- |
| 01/09/2019 00:30:56 | 123     | route 1  | ...      | 1          |
| 01/09/2019 00:50:30 | 123     | route 2  | ...      | 1          |
| 01/09/2019 09:20:30 | 123     | route 3  | ...      | 2          |
| 01/09/2019 00:20:00 | 456     | route 1  | ...      | 3          |

If we just make up a new `journey_id` column, that at least expresses the
grouping rule we applied. But if we look at each row individually, we can't
tell which leg of a journey is represented. So let's add two more columns to
represent the sequence number of the leg and the total number of legs:

| date_time           | card_id | bus_line | lat, lng | journey_id | leg_sequence | total_legs |
| ------------------- | ------- | -------- | -------- | ---------- | ------------ | ---------- |
| 01/09/2019 00:30:56 | 123     | route 1  | ...      | 1          | 1            | 2          |
| 01/09/2019 00:50:30 | 123     | route 2  | ...      | 1          | 2            | 2          |
| 01/09/2019 09:20:30 | 123     | route 3  | ...      | 2          | 1            | 1          |
| 01/09/2019 00:20:00 | 456     | route 1  | ...      | 3          | 1            | 1          |

This works, but I find it much more awkward to think this way and write code
accordingly. I don't recommend it.

A barrier to working with nested/hierarchical data is language. From my limited
experience, R doesn't handle nesting well at all. Working with JSON data, for
instance, appears to require "flattening" the data into a dataframe somehow. I
would recommend learning some Python to more easily work with hierarchical
data, and **not** just using `pandas` and `numpy` and other libraries that
force you to think in 2D data-frames.

### Explicit data schemas

Another tip for working with complex or messy data is to explicily write down
the schema for the cleaned-up version of the data. In this example, we used
[Python dataclasses](https://docs.python.org/3/library/dataclasses.html) as a
lightweight option. If you were working with JSON data, you could write a
[schema](https://json-schema.org) such as [this
example](https://github.com/a-b-street/osm2lanes/blob/181efd87ba286149cd074fc47c65c3dff075fd39/data/spec-lanes.json).
Or if you want to save the data in an efficient binary format or work with the
data across multiple languages, consider [protocol
buffers](https://developers.google.com/protocol-buffers/docs/pythontutorial).

You'll reap more benefits of schemas if you work in a language with a static
type system, where the language will prevent you from doing something invalid
with the data, like accessing a field that doesn't exist, or trying to add a
single string to a list of strings. It can be a big up-front investment to
learn another programming language, but Python for example has a compromise of
[optional type hints](https://mypy.readthedocs.io/en/stable/index.html).

### Extending this approach

This particular use case did not take very much time to solve, but imagine it
had. That might not be sustainable if there are many transit agencies, all with
slightly different ticketing data formats, right?

An approach that I find helpful is to transform raw data into a cleaned-up,
standardized format. In this example, that would be the `Journey` object. We
could build a bunch of web dashboards to interactively filter for journeys
starting/ending in different places, happening at certain times, with different
transfer patterns, etc. That dashboard would probably be high-effort to create.
But we do the work once, operating on cleaned-up `Journey` data -- not the
specific ticketing format in one municipality. It should be relatively
low-effort to transform a second area's custom format into the same
higher-level data. I've taken this approach before working with aggregate
origin/destination data between zones, which exists in different formats across
UK and Australia census. Spend a small amount of effort converting each
country's data into a common format, then focus all the work on the common
format.
