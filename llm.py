import ollama
import re


def fix_sql(sql):

    # Remove markdown
    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    # Remove SQL:
    if sql.upper().startswith("SQL"):
        sql = sql[3:].strip(": \n")

    # Execute first query only
    if ";" in sql:
        sql = sql.split(";")[0] + ";"

    # Convert TOP -> LIMIT
    m = re.search(r"TOP\s+(\d+)", sql, re.IGNORECASE)

    if m:

        n = m.group(1)

        sql = re.sub(
            r"TOP\s+\d+",
            "",
            sql,
            flags=re.IGNORECASE
        )

        sql = sql.rstrip(";") + f" LIMIT {n};"

    # YEAR(column) -> column
    sql = re.sub(
        r"YEAR\s*\(\s*([^)]+)\s*\)",
        r"\1",
        sql,
        flags=re.IGNORECASE
    )

    # GETDATE()
    sql = re.sub(
        r"GETDATE\s*\(\)",
        "CURRENT_DATE",
        sql,
        flags=re.IGNORECASE
    )

    # NOW()
    sql = re.sub(
        r"NOW\s*\(\)",
        "CURRENT_TIMESTAMP",
        sql,
        flags=re.IGNORECASE
    )

    # Fix common alias mistake
    sql = re.sub(
        r"SELECT\s+r\.name\s*,\s*c\.name",
        "SELECT r.name AS race_name, c.name AS circuit_name",
        sql,
        flags=re.IGNORECASE
    )

    return sql


def is_valid_sql(sql):

    sql = sql.strip()

    # Must start with SELECT or WITH
    if not re.match(
        r"^(SELECT|WITH)\b",
        sql,
        re.IGNORECASE
    ):
        return False

    # Parentheses must be balanced
    if sql.count("(") != sql.count(")"):
        return False

    # Must end with semicolon
    if not sql.endswith(";"):
        return False

    return True


def is_safe_sql(sql):

    sql_upper = sql.upper()

    forbidden = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "REPLACE"
    ]

    for word in forbidden:

        if re.search(
            rf"\b{word}\b",
            sql_upper
        ):
            return False

    return True


def generate_sql(question, schema):

    prompt = f"""
You are an expert SQLite SQL Engineer.

Your job is to generate ONE valid SQLite query.

=========================
GENERAL RULES
=========================

Return ONLY SQL.

Never explain.

Never use markdown.

Never use ```.

Generate exactly ONE statement.

Database engine is SQLite.

Never invent:

- tables
- columns
- relationships

Use ONLY the schema below.

Always use LIMIT instead of TOP.

SQLite does NOT support:

YEAR()
GETDATE()
NOW()
AUTO_INCREMENT

Use strftime() when extracting years or dates.

Before generating SQL:

1. Identify ALL tables required.
2. Verify EVERY selected column.
3. Verify EVERY JOIN.
4. Verify EVERY alias.
5. Make sure the SQL is complete.
6. Close every parenthesis.
7. End the SQL with a semicolon.

If a selected column belongs to another table,
JOIN that table first.

Never guess column names.

=========================
COLUMN LOCATION REMINDER
=========================

Race name
-> races.name

Race date
-> races.date

Race time
-> races.time

Circuit name
-> circuits.name

Circuit country
-> circuits.country

Circuit location
-> circuits.location

Driver first name
-> drivers.forename

Driver last name
-> drivers.surname

Driver date of birth
-> drivers.dob

Constructor name
-> constructors.name

Status text
-> status.status

Driver age is NOT stored in a column.

If the question asks for driver age in relation to a race,
you MUST use the race date.

You MUST join:

results -> drivers
results -> races

Driver age at race date:

CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
)

IMPORTANT:

Do NOT calculate driver age using CURRENT_DATE
when the question refers to a specific race.

Do NOT use:

JULIANDAY(d.dob) - JULIANDAY(ra.date)

The correct order is:

JULIANDAY(ra.date) - JULIANDAY(d.dob)

=========================
RESULTS TABLE
=========================

results contains ONLY race results.

results contains:

raceId
driverId
constructorId
position
points
fastestLap
fastestLapTime
fastestLapSpeed
statusId

results DOES NOT contain:

driver
driverName
driver_name
constructor
constructorName
constructor_name
raceName
race_name
name
date
country
location
circuitId

To get driver information:

results.driverId
JOIN drivers.driverId

To get driver name:

drivers.forename
drivers.surname

To get race information:

results.raceId
JOIN races.raceId

To get race name:

races.name

To get constructor information:

results.constructorId
JOIN constructors.constructorId

To get constructor name:

constructors.name

=========================
JOIN RULES
=========================

Drivers + Results:

drivers.driverId = results.driverId

Results + Races:

results.raceId = races.raceId

Results + Constructors:

results.constructorId = constructors.constructorId

Races + Circuits:

races.circuitId = circuits.circuitId

Results + Status:

results.statusId = status.statusId

Never invent direct relationships.


=========================
MANDATORY AGE RULE
=========================

If the SQL calculates driver age using a race date:

YOU MUST JOIN races.

Required structure:

FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId

The age calculation MUST use:

CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
)

If the SQL contains:

ra.date

then the alias ra MUST appear in FROM or JOIN.

INVALID:

FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
WHERE
    julianday(ra.date)

VALID:

FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE
    julianday(ra.date)

If the question refers to a specific race,
the race filter MUST also be preserved.

For example:

WHERE ra.name = 'Monaco Grand Prix'

=========================
ALIAS RULES
=========================

If you use aliases,
use them everywhere.

Correct:

SELECT d.forename
FROM drivers d

Wrong:

SELECT drivers.forename
FROM drivers d

Never reuse aliases.

Recommended aliases:

drivers -> d

results -> re

races -> ra

constructors -> co

circuits -> ci

status -> s

=========================
IMPORTANT
=========================

For EVERY column in SELECT:

Verify that the column exists.

For EVERY table:

Verify that it exists in the schema.

For EVERY JOIN:

Verify the relationship.

For EVERY alias:

Verify that it was defined.

Never use:

results.driver

results.name

results.date

results.constructor_name

results.driver_name

races.driverId

races.constructorId

races.statusId

results.circuitId

=========================
FINAL SQL VALIDATION
=========================

Before returning the SQL, mentally validate it.

For EVERY alias used anywhere in:

SELECT
FROM
JOIN
WHERE
GROUP BY
HAVING
ORDER BY

verify that the alias was declared.

For EVERY column reference:

table_alias.column

verify that:

1. table_alias exists.
2. column exists in that table.
3. the table containing the column is actually joined.

NEVER return SQL containing an undefined alias.

If you use:

ra.date

you MUST have:

JOIN races ra
ON re.raceId = ra.raceId

If you use:

d.dob

you MUST have:

JOIN drivers d
ON re.driverId = d.driverId

=========================
DATABASE SCHEMA
=========================

{schema}

=========================
EXAMPLES
=========================

Question:
How many drivers participated in Monaco Grand Prix?

SQL:

SELECT
    COUNT(DISTINCT d.driverId) AS driver_count
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix';

----------------------------

Question:
Show drivers with constructors

SQL:

SELECT
    d.forename,
    d.surname,
    co.name AS constructor_name
FROM drivers d
JOIN results re
    ON d.driverId = re.driverId
JOIN constructors co
    ON re.constructorId = co.constructorId;

----------------------------

Question:
Show races with circuits

SQL:

SELECT
    ra.name AS race_name,
    ci.name AS circuit_name
FROM races ra
JOIN circuits ci
    ON ra.circuitId = ci.circuitId;

----------------------------

Question:
Show race winners

SQL:

SELECT
    ra.name AS race_name,
    d.forename,
    d.surname
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE re.position = 1;

----------------------------

Question:
How many drivers who participated in Monaco Grand Prix were over 30 years old?

SQL:

SELECT
    COUNT(DISTINCT d.driverId) AS drivers_over_30
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
AND CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) > 30;

----------------------------

Question:
Show race status

SQL:

SELECT
    ra.name AS race_name,
    s.status
FROM results re
JOIN races ra
    ON re.raceId = ra.raceId
JOIN status s
    ON re.statusId = s.statusId;

=========================
QUESTION
=========================

{question}

SQL:
"""

    # =====================================================
    # FIRST GENERATION
    # =====================================================

    response = ollama.chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    sql = response["message"]["content"]

    sql = fix_sql(sql)


    # =====================================================
    # VALIDATE FIRST GENERATION
    # =====================================================

    if not is_valid_sql(sql):

        print("\nInvalid SQL generated.")
        print("First SQL:")
        print(sql)
        print("\nRetrying...\n")

        retry_prompt = f"""
The previous SQL generation was incomplete or invalid.

Question:
{question}

Previous SQL:
{sql}

Generate the COMPLETE correct SQLite query.

Rules:

- Return ONLY SQL.
- No explanation.
- No markdown.
- Exactly ONE SELECT statement.
- Close ALL parentheses.
- End with semicolon.
- Use ONLY the provided schema.
- Verify every column.
- Verify every JOIN.
- Never invent column names.

Schema:

{schema}

Return the complete SQL now.
"""

        retry_response = ollama.chat(
            model="gemma3:4b",
            messages=[
                {
                    "role": "user",
                    "content": retry_prompt
                }
            ]
        )

        sql = retry_response["message"]["content"]

        sql = fix_sql(sql)


    # =====================================================
    # FINAL VALIDATION
    # =====================================================

    if not is_valid_sql(sql):

        raise ValueError(
            f"LLM generated invalid SQL:\n{sql}"
        )


    # =====================================================
    # SAFETY VALIDATION
    # =====================================================

    if not is_safe_sql(sql):

        raise ValueError(
            "Unsafe SQL generated."
        )


    return sql