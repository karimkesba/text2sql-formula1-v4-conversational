import os
import sqlite3
import pandas as pd
from embedding_search import retrieve_tables


DB_PATH = "C:/Users/Admin/python/chat_with_data/formula_1.sqlite"

DESCRIPTION_PATH = r"D:/Downloads/minidev_0703/minidev/MINIDEV/dev_databases/formula_1/database_description"


def get_schema(selected_tables=None):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name NOT LIKE 'sqlite_%';
    """)

    tables = cursor.fetchall()
    if selected_tables is not None:
        tables = [t for t in tables if t[0] in selected_tables]

    schema = "Database: SQLite\n\n"

    for table in tables:

        table_name = table[0]

        schema += f"Table: {table_name}\n"
        schema += "Columns:\n"

        csv_file = os.path.join(DESCRIPTION_PATH, f"{table_name}.csv")


        if os.path.exists(csv_file):

            try:
              df = pd.read_csv(csv_file, sep=None, engine="python", encoding="utf-8")
            except UnicodeDecodeError:
              df = pd.read_csv(csv_file, sep=None, engine="python", encoding="latin1")


            for _, row in df.iterrows():

                schema += f"- {row['original_column_name']}\n"

                if pd.notna(row.get("data_format")):
                    schema += f"  Type: {row['data_format']}\n"

                if pd.notna(row.get("column_description")):
                    schema += f"  Description: {row['column_description']}\n"

                if (
                    "value_description" in df.columns
                    and pd.notna(row.get("value_description"))
                    and str(row["value_description"]).strip() != ""
                ):
                    schema += f"  Notes: {row['value_description']}\n"

                schema += "\n"

        else:

            cursor.execute(f'PRAGMA table_info("{table_name}")')

            columns = cursor.fetchall()

            for col in columns:
                schema += f"- {col[1]}\n"

            schema += "\n"

    schema += """

==================================================
RELATIONSHIPS
==================================================

races.circuitId = circuits.circuitId

results.raceId = races.raceId
results.driverId = drivers.driverId
results.constructorId = constructors.constructorId

driverStandings.driverId = drivers.driverId
driverStandings.raceId = races.raceId

constructorStandings.constructorId = constructors.constructorId
constructorStandings.raceId = races.raceId

qualifying.driverId = drivers.driverId
qualifying.constructorId = constructors.constructorId
qualifying.raceId = races.raceId

lapTimes.driverId = drivers.driverId
lapTimes.raceId = races.raceId

pitStops.driverId = drivers.driverId
pitStops.raceId = races.raceId

results.statusId = status.statusId
races.raceId = results.raceId

drivers.driverId = results.driverId

constructors.constructorId = results.constructorId

==================================================
IMPORTANT NOTES
==================================================

- Drivers information is stored in drivers.
- Constructors information is stored in constructors.
- Circuits information is stored in circuits.
- Race information is stored in races.
- Race results are stored in results.
- Driver standings are stored in driverStandings.
- Constructor standings are stored in constructorStandings.
- Qualifying data is stored in qualifying.
- Lap times are stored in lapTimes.
- Pit stop data is stored in pitStops.

- The results table is the main table connecting:
    drivers
    constructors
    races

- To connect drivers with constructors, use results.
- To connect drivers with races, use results.
- To connect constructors with races, use results.

- Do NOT assume direct relationships unless listed above.


==================================================
TABLE CONTENT
==================================================

drivers:
Contains driver information only.

constructors:
Contains constructor information only.

circuits:
Contains circuit information only.

races:
Contains race information only.

results:
Contains finishing results.
Does NOT contain race name.
Does NOT contain driver name.
Does NOT contain constructor name.
Does NOT contain circuitId.

status:
Contains race status text.

qualifying:
Contains qualifying times.

lapTimes:
Contains lap times.

pitStops:
Contains pit stop information.

==================================================
RULES
==================================================

- Database engine is SQLite.
- Generate ONLY valid SQLite SQL.
- Return ONLY SQL.
- Never explain.
- Never use markdown.
- Never use TOP.
- Always use LIMIT.
- Never invent tables.
- Never invent columns.
- Use ONLY tables and columns from the schema.
- Use JOIN only when needed.
- Always use the relationships listed above.
- Use aliases when selecting columns with the same name.

Example:

SELECT
    races.name AS race_name,
    circuits.name AS circuit_name
FROM races
JOIN circuits
ON races.circuitId = circuits.circuitId;

"""

    conn.close()

    return schema

def get_relevant_schema(question):

    selected_tables = retrieve_tables(question)
    print("Relevant Tables:", selected_tables)

    return get_schema(selected_tables)

if __name__ == "__main__":

    print(get_relevant_schema(
        "Show drivers with their constructor names"
    ))