import ollama


def classify_question(question, history):

    # No history = new question
    if not history:
        return "new"


    history_text = ""

    for item in history[-3:]:

        history_text += f"""
Previous Question:
{item["question"]}

Previous SQL:
{item["sql"]}

Previous Answer:
{item["answer"]}

--------------------------------
"""


    prompt = f"""
You are a classifier for a Text-to-SQL system.

Classify the CURRENT QUESTION into exactly ONE:

new
follow_up
sql_modification

==================================================

NEW

Use new when the question is independent.

Example:

Previous:
How many drivers participated in Monaco Grand Prix?

Current:
How many races were held in Italy?

Answer:
new

==================================================

FOLLOW_UP

Use follow_up when the user asks for a new calculation
about the previous result.

Examples:

How many of them were British?

How many of them were over 30?

How many of those were under 40?

Which of them were German?

These questions depend on the previous result.

==================================================

SQL_MODIFICATION

Use sql_modification when the user wants to change
how the previous result is displayed or filtered.

Examples:

Only show the British drivers.

Sort them by age.

Show only the first 10.

Add constructor name.

Group them by nationality.

==================================================

IMPORTANT

Questions containing:

them
those
these
they
which ones
how many of them

are usually follow_up.

==================================================

CONVERSATION

{history_text}

==================================================

CURRENT QUESTION

{question}

==================================================

Return ONLY:

new

follow_up

or

sql_modification
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


    result = response["message"]["content"].strip().lower()


    if result not in {
        "new",
        "follow_up",
        "sql_modification"
    }:

        result = "follow_up"


    return result