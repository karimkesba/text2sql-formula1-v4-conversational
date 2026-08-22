import ollama
import re


# =========================================================
# Main Function
# =========================================================

def modify_sql(previous_sql, question):

    prompt = f"""
You are an expert SQLite SQL Engineer.

The user has an EXISTING SQL query and wants to ask a
follow-up question or modify the previous query.

Your job is to modify the EXISTING SQL query.

========================================================
MOST IMPORTANT RULE
========================================================

THE PREVIOUS SQL IS THE SOURCE OF TRUTH.

You MUST preserve the previous SQL logic.

Preserve:

- FROM
- JOIN
- JOIN relationships
- table aliases
- existing WHERE conditions
- existing filters
- existing age conditions
- existing nationality conditions
- existing race conditions
- existing year conditions
- existing date conditions
- existing aggregation logic

When the user says:

- them
- those
- they
- these
- it
- previous
- same
- above

they are referring to the result represented by the PREVIOUS SQL.

Therefore:

ADD the new condition to the previous SQL.

DO NOT start from scratch.

========================================================
VERY IMPORTANT: DO NOT INVENT COLUMNS
========================================================

Never invent a column.

For example:

DO NOT generate:

d.age

drivers.age

ra.age

unless such a column already exists in the previous SQL.

In this Formula 1 database:

drivers contains:

d.dob

The driver age must be calculated using:

CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
)

Therefore, whenever the user asks about:

- age
- older than
- over
- younger than
- under
- youngest
- oldest

use the age calculation above.

NEVER use:

d.age

drivers.age

========================================================
AGE CALCULATION
========================================================

For:

"over 30"

use:

CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) > 30

For:

"under 40"

use:

CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) < 40

For:

"over 30 and under 40"

use BOTH conditions:

CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) > 30

AND

CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) < 40

========================================================
EXISTING CONDITIONS MUST NEVER DISAPPEAR
========================================================

Example previous SQL:

SELECT
    COUNT(DISTINCT d.driverId)
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
AND d.nationality = 'British';

User:

How many of them were over 30?

Correct SQL:

SELECT
    COUNT(DISTINCT d.driverId)
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
AND d.nationality = 'British'
AND CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) > 30;

========================================================
ANOTHER EXAMPLE
========================================================

Previous SQL:

SELECT
    COUNT(DISTINCT d.driverId)
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
AND d.nationality = 'British'
AND CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) > 30;

User:

How many of them were under 40?

Correct SQL:

SELECT
    COUNT(DISTINCT d.driverId)
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
AND d.nationality = 'British'
AND CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) > 30
AND CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
) < 40;

========================================================
ANOTHER EXAMPLE
========================================================

Previous SQL:

SELECT
    d.forename,
    d.surname
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix';

User:

Only show British drivers.

Correct:

SELECT
    d.forename,
    d.surname
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
AND d.nationality = 'British';

========================================================
ANOTHER EXAMPLE
========================================================

Previous SQL:

SELECT
    d.forename,
    d.surname
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix';

User:

Show only the first 10.

Correct:

SELECT
    d.forename,
    d.surname
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
LIMIT 10;

========================================================
ANOTHER EXAMPLE
========================================================

Previous SQL:

SELECT
    d.forename,
    d.surname
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix';

User:

Sort them by oldest.

Correct:

SELECT
    d.forename,
    d.surname
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix'
ORDER BY
    CAST(
        (julianday(ra.date) - julianday(d.dob)) / 365.25
        AS INTEGER
    ) DESC;

========================================================
RULES
========================================================

Return ONLY valid SQLite SQL.

Never explain.

Never use markdown.

Return exactly ONE SQL statement.

Do NOT completely rewrite the query unless necessary.

Preserve the existing query.

Never invent:

- tables
- columns
- aliases
- relationships

Use only tables and columns already present in the query.

If a new column requires another table, add a JOIN only
when the relationship is known.

SQLite syntax only.

Never use:

TOP
YEAR()
GETDATE()
NOW()

Use SQLite syntax.

========================================================
PREVIOUS SQL
========================================================

{previous_sql}

========================================================
USER REQUEST
========================================================

{question}

========================================================
OUTPUT
========================================================

Return ONLY the modified SQL.
"""

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

    sql = fix_modified_sql(
        sql,
        previous_sql
    )

    validate_sql(sql)

    return sql


# =========================================================
# Fix LLM Output
# =========================================================

def fix_modified_sql(sql, previous_sql):

    # -----------------------------------------
    # Remove markdown
    # -----------------------------------------

    sql = sql.replace(
        "```sql",
        ""
    )

    sql = sql.replace(
        "```",
        ""
    )

    sql = sql.strip()


    # -----------------------------------------
    # Remove "SQL:"
    # -----------------------------------------

    if sql.upper().startswith("SQL:"):

        sql = sql[4:].strip()


    elif sql.upper().startswith("SQL"):

        sql = sql[3:].strip(
            ": \n"
        )


    # -----------------------------------------
    # Keep first SQL statement
    # -----------------------------------------

    if ";" in sql:

        sql = (
            sql.split(";")[0]
            + ";"
        )


    # =====================================================
    # IMPORTANT SAFETY FIX
    #
    # If LLM generates d.age, replace it with the
    # correct SQLite age calculation.
    # =====================================================

    age_expression = """
CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
)
""".strip()


    sql = re.sub(
        r"\bd\.age\b",
        age_expression,
        sql,
        flags=re.IGNORECASE
    )


    sql = re.sub(
        r"\bdrivers\.age\b",
        age_expression,
        sql,
        flags=re.IGNORECASE
    )


    # -----------------------------------------
    # TOP -> LIMIT
    # -----------------------------------------

    match = re.search(
        r"\bTOP\s+(\d+)",
        sql,
        re.IGNORECASE
    )

    if match:

        n = match.group(1)

        sql = re.sub(
            r"\bTOP\s+\d+\b",
            "",
            sql,
            flags=re.IGNORECASE
        )

        sql = (
            sql.rstrip(";")
            + f" LIMIT {n};"
        )


    return sql.strip()


# =========================================================
# Validate SQL
# =========================================================

def validate_sql(sql):

    sql_upper = sql.upper()


    # -----------------------------------------
    # Block dangerous SQL
    # -----------------------------------------

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


    for keyword in forbidden:

        if re.search(
            rf"\b{keyword}\b",
            sql_upper
        ):

            raise ValueError(
                f"Unsafe SQL generated: {keyword}"
            )


    # -----------------------------------------
    # Only SELECT / WITH allowed
    # -----------------------------------------

    if not sql.strip().upper().startswith(
        (
            "SELECT",
            "WITH"
        )
    ):

        raise ValueError(
            "LLM generated invalid SQL."
        )


# =========================================================
# Test
# =========================================================

if __name__ == "__main__":

    previous_sql = """
SELECT
    COUNT(DISTINCT d.driverId) AS driver_count
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix';
"""


    questions = [

        "How many of them were British?",

        "How many of them were over 30?",

        "How many of them were under 40?",

        "How many of them were over 35?"

    ]


    for question in questions:

        print(
            "=" * 60
        )

        print(
            "Question:"
        )

        print(
            question
        )


        sql = modify_sql(
            previous_sql,
            question
        )


        print(
            "\nModified SQL:"
        )

        print(
            sql
        )