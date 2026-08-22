# Formula 1 Conversation-Aware Text-to-SQL using Large Language Models



A Text-to-SQL application that allows users to query a Formula 1 SQLite database using natural language.

The system uses a local LLM to generate and modify SQL queries, semantic table retrieval with embeddings, and a Streamlit interface for interactive querying and conversation history.

> **Version 4:** This version introduces **ChromaDB as a vector database for table retrieval** and adds **conversation-aware SQL generation**, allowing follow-up questions and SQL modifications to depend on the previous query.

---

##  What's New in Version 4?

This is the **fourth iteration** of the project.

The main improvements over the previous versions are:

-  **ChromaDB vector database** for storing table embeddings.
-  **Semantic table retrieval** instead of relying only on the full database schema.
-  **Keyword boosting** to improve table retrieval for explicit terms in the question.
-  **Automatic table expansion** based on known database relationships.
-  **Conversation-aware question classification**.
-  Support for **follow-up questions** that depend on the previous result.
-  Support for **SQL modification requests** that modify the previous SQL instead of generating a new query from scratch.
-  SQL cleaning, validation, and safety checks before execution.
-  Conversation history containing the original question, context, SQL, answer, and question type.

---

##  System Workflow

```text
User Question
      │
      ▼
Streamlit Interface
      │
      ▼
Question Classifier
      │
      ├── New Question
      │       │
      │       ▼
      │   Table Retrieval
      │       │
      │       ▼
      │   Relevant Schema
      │       │
      │       ▼
      │   LLM SQL Generation
      │
      ├── Follow-up
      │       │
      │       ▼
      │   Previous SQL
      │       │
      │       ▼
      │   SQL Modifier
      │
      └── SQL Modification
              │
              ▼
          Previous SQL
              │
              ▼
          SQL Modifier

              │
              ▼
        SQL Validation
              │
              ▼
        SQLite Execution
              │
              ▼
        Results + Answer
              │
              ▼
      Conversation History
```

---

##  Main Components

### 1. Streamlit Interface — `app.py`

The main application interface.

It handles:

- User questions.
- Session-based conversation history.
- Question classification.
- Relevant schema retrieval for new questions.
- SQL generation.
- SQL modification for follow-up questions.
- SQL execution against SQLite.
- Displaying generated SQL and results.
- Converting query results into a readable answer.
- Displaying the conversation history in the sidebar.

The application supports three question types:

```text
new
follow_up
sql_modification
```

---

### 2. Conversation Classification — `conversation_manager.py`

This module determines whether the current question is:

#### `new`

An independent question that does not depend on previous conversation.

Example:

```text
How many races were held in Italy?
```

#### `follow_up`

A question that depends on the previous result.

Examples:

```text
How many of them were British?
How many of them were over 30?
Which of them were German?
```

#### `sql_modification`

A request to change the previous query/result.

Examples:

```text
Only show the British drivers.
Sort them by age.
Show only the first 10.
Add constructor name.
```

The classifier uses the local LLM and the recent conversation history to determine the question type.

---

### 3. SQL Generation — `llm.py`

This module generates SQLite SQL for new questions.

The LLM receives:

- The user's question.
- The relevant database schema.
- Database relationships.
- Column rules.
- SQLite-specific rules.
- Examples of valid queries.

The prompt strongly restricts the model from inventing:

- Tables.
- Columns.
- Relationships.
- Aliases.

It also contains specific rules for Formula 1 data, such as calculating driver age from:

```sql
CAST(
    (julianday(ra.date) - julianday(d.dob)) / 365.25
    AS INTEGER
)
```

After generation, the SQL is cleaned and validated.

The module also retries generation if the first SQL query is incomplete or invalid.

---

### 4. SQL Modification — `sql_modifier.py`

This is one of the main additions in Version 4.

Instead of generating a completely new SQL query for a dependent question, the system sends the **previous SQL query** to the LLM and asks it to modify that query.

The previous SQL is treated as the **source of truth**.

Existing:

- `FROM`
- `JOIN`
- `WHERE`
- filters
- conditions
- aggregation logic

should be preserved unless the user's request requires a modification.

For example:

Previous question:

```text
How many drivers participated in Monaco Grand Prix?
```

Previous SQL:

```sql
SELECT COUNT(DISTINCT d.driverId)
FROM results re
JOIN drivers d
    ON re.driverId = d.driverId
JOIN races ra
    ON re.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix';
```

Follow-up:

```text
How many of them were British?
```

The system modifies the existing query by adding:

```sql
AND d.nationality = 'British'
```

Another follow-up can build on the already modified SQL:

```text
How many of them were over 30?
```

The new condition is added while preserving the previous conditions.

This allows the conversation to behave as a chain of SQL modifications rather than treating every question as independent.

---

### 5. Database Schema Retrieval — `db.py`

`db.py` builds the schema that is provided to the SQL-generating LLM.

Instead of always sending every database table, it calls:

```python
retrieve_tables(question)
```

The returned tables are then used to build a focused schema.

For each relevant table, the module reads its database description when available and includes information such as:

- Column names.
- Data types.
- Column descriptions.
- Value descriptions.

It also includes the known relationships between Formula 1 tables.

This reduces the amount of irrelevant schema information sent to the LLM.

---

### 6. Semantic Table Retrieval — `embedding_search.py`

This module handles table-level semantic retrieval.

The project previously used embeddings directly in memory. In Version 4, the embeddings are stored persistently in **ChromaDB**.

The embedding model is:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Each table is represented by a document containing:

- Table name.
- Table description.
- Keywords.
- Important columns.

These documents are embedded and stored in a ChromaDB collection:

```text
table_catalog
```

The ChromaDB database is persisted locally in:

```text
./chroma_db
```

---

##  Table Retrieval Process

When a new question arrives:

### Step 1 — Embed the question

The question is converted into an embedding using the same Sentence Transformer model.

### Step 2 — Search ChromaDB

The question embedding is compared with the stored table embeddings.

The top relevant tables are retrieved.

### Step 3 — Keyword boosting

Explicit keywords from `TABLE_CATALOG` are also checked against the question.

Matching tables are added to the retrieved set.

This gives the retrieval process both:

- Semantic similarity.
- Explicit keyword matching.

### Step 4 — Expand related tables

The retrieved tables are expanded using known database relationships.

For example:

```text
drivers + constructors
        ↓
     results
```

Because `results` is the bridge between drivers and constructors.

Similarly:

```text
results
   ↓
drivers
races
constructors
```

And:

```text
races
  ↓
circuits
```

The purpose is to make sure the final schema contains the tables required to build valid JOINs, even when those bridge tables were not directly retrieved by semantic search.

---

##  ChromaDB Embedding Storage

The table embeddings are created from the table catalog and stored persistently.

The system first checks which table IDs already exist in ChromaDB.

Only missing tables are embedded and added.

This prevents rebuilding and inserting the same table embeddings every time the application starts.

The overall process is:

```text
TABLE_CATALOG
      │
      ▼
Table Documents
      │
      ▼
Sentence Transformer
      │
      ▼
Embeddings
      │
      ▼
ChromaDB
      │
      ▼
Semantic Retrieval
```

---

##  Table Catalog

`table_catalog.py` contains the metadata used to describe the database tables.

Each table provides information such as:

```text
description
keywords
important_columns
```

This metadata is used to create the documents that are embedded and stored in ChromaDB.

---

##  SQL Validation & Safety

The system performs several checks before executing generated SQL.

### SQL validity

The query must:

- Start with `SELECT` or `WITH`.
- Have balanced parentheses.
- End with a semicolon.
- Contain one SQL statement.

### SQL safety

The system blocks destructive SQL operations such as:

```text
DROP
DELETE
UPDATE
INSERT
ALTER
CREATE
TRUNCATE
REPLACE
```

Only read-oriented SQL queries are allowed.

---

##  SQL Cleanup

Generated SQL is cleaned before execution.

The system removes:

- Markdown code fences.
- `SQL:` prefixes.
- Extra SQL statements.

It also handles some common LLM mistakes, such as:

- Converting `TOP N` to SQLite `LIMIT N`.
- Correcting common alias mistakes.
- Converting unsupported date functions where applicable.

The SQL modifier also contains an additional protection for incorrect driver-age references such as:

```text
d.age
drivers.age
```

and replaces them with the correct race-date-based age calculation.

---

##  Conversation Memory

Conversation history is stored in Streamlit session state.

Each successful interaction stores:

```python
{
    "question": ...,
    "rewritten_question": ...,
    "sql": ...,
    "answer": ...,
    "question_type": ...
}
```

This history is used for:

- Classifying later questions.
- Providing context to the classifier.
- Retrieving the previous SQL.
- Modifying the previous SQL for dependent questions.
- Displaying the conversation in the sidebar.

The latest successful SQL becomes the basis for the next SQL modification.

---

##  Database

The project uses a Formula 1 SQLite database containing tables for areas such as:

- Drivers.
- Constructors.
- Races.
- Circuits.
- Results.
- Driver standings.
- Constructor standings.
- Qualifying.
- Lap times.
- Pit stops.
- Status.

The system uses known relationships between these tables to construct valid JOINs.

---

##  Project Structure

```text
chat_with_data/
│
├── app.py
├── conversation_manager.py
├── sql_modifier.py
├── llm.py
├── db.py
├── embedding_search.py
├── table_catalog.py
│
├── formula_1.sqlite
│
└── chroma_db/
```

---

##  Technologies

- **Python**
- **Streamlit**
- **SQLite**
- **Ollama**
- **Gemma 3 4B**
- **Sentence Transformers**
- **ChromaDB**
- **Pandas**

---

##  Version 4 Architecture

Version 4 introduces a **conversational Text-to-SQL architecture** that combines **semantic retrieval, database relationships, and conversation-aware SQL generation**.

*  **ChromaDB Vector Database**
  Stores table embeddings for efficient and persistent semantic retrieval.

*  **Persistent Table Embeddings**
  Generates table embeddings once and stores them for reuse across sessions.

*  **Semantic Table Retrieval**
  Retrieves the most relevant database tables based on the semantic meaning of the user's question.

*  **Keyword Boosting**
  Boosts relevant tables when important keywords from the user's question match table metadata.

*  **Relationship-Based Table Expansion**
  Expands the retrieved tables using database relationships and foreign keys to provide the necessary context for SQL generation.

*  **Conversation Question Classification**
  Determines whether the user's question is a new query or a follow-up to the previous conversation.

*  **Follow-Up Question Handling**
  Uses conversation context to understand incomplete or context-dependent questions.

*  **Previous-SQL-Based Query Modification**
  Modifies the existing SQL query when appropriate instead of generating a completely new query from scratch.

*  **Improved SQL Validation & Safety**
  Validates generated SQL and helps prevent invalid, unsafe, or unsupported database operations.


##  Run the Project

Install the required dependencies:

```bash
pip install streamlit pandas sentence-transformers chromadb ollama
```

Make sure Ollama is installed and the required model is available:

```bash
ollama pull gemma3:4b
```

Then run:

```bash
streamlit run app.py
```

---

##  Example Conversation

```text
User:
How many drivers participated in Monaco Grand Prix?

System:
Generates SQL and returns the result.

User:
How many of them were British?

System:
Classifies the question as follow_up,
takes the previous SQL,
and adds the British nationality condition.

User:
How many of them were over 30?

System:
Uses the modified SQL as the new source,
then adds the age condition.
```

This allows the user to progressively refine a query through natural language.

---
## Author

**Karim Kesba**

AI / Machine Learning Developer


