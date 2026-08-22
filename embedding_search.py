from sentence_transformers import SentenceTransformer
import chromadb

from table_catalog import TABLE_CATALOG


# =========================================================
# Embedding Model
# =========================================================

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


# =========================================================
# ChromaDB
# =========================================================

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="table_catalog"
)


# =========================================================
# Build Table Documents
# =========================================================

documents = {}

for table, info in TABLE_CATALOG.items():

    text = f"""
Table Name:
{table}

Description:
{info["description"]}

Keywords:
{", ".join(info["keywords"])}

Important Columns:
{", ".join(info["important_columns"])}
"""

    documents[table] = text


# =========================================================
# Store Embeddings in ChromaDB
# =========================================================

existing_data = collection.get()

existing_ids = set(existing_data["ids"])


new_tables = []

for table, document in documents.items():

    if table not in existing_ids:
        new_tables.append(table)


if new_tables:

    texts = [documents[table] for table in new_tables]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    ).tolist()

    collection.add(
        ids=new_tables,
        documents=texts,
        embeddings=embeddings
    )

    print("New table embeddings added to ChromaDB:")
    print(new_tables)

else:

    print("All table embeddings already exist in ChromaDB.")


# =========================================================
# Retrieve Relevant Tables
# =========================================================

def retrieve_tables(question, top_k=4):

    question_embedding = model.encode(
        question,
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    tables = results["ids"][0]

    scores = results["distances"][0]

    print("\nRetrieved Tables:")

    for table, score in zip(tables, scores):
        print(f"{table}: {score:.4f}")

    question_lower = question.lower()

    # Keyword boosting
    boosted_tables = set(tables)

    for table in TABLE_CATALOG:

        keywords = TABLE_CATALOG[table]["keywords"]

        for keyword in keywords:

            if keyword.lower() in question_lower:

                boosted_tables.add(table)

                break

    tables = list(boosted_tables)

    return expand_tables(tables)


# =========================================================
# Expand Related Tables
# =========================================================

def expand_tables(tables):

    tables = set(tables)

    # =====================================================
    # Drivers + Constructors need Results as bridge
    # =====================================================

    if "drivers" in tables and "constructors" in tables:
        tables.add("results")

    # =====================================================
    # Results
    # =====================================================

    if "results" in tables:

        tables.update([
            "drivers",
            "races",
            "constructors"
        ])

    # =====================================================
    # Driver Standings
    # =====================================================

    if "driverStandings" in tables:

        tables.update([
            "drivers",
            "races"
        ])

    # =====================================================
    # Constructor Standings
    # =====================================================

    if "constructorStandings" in tables:

        tables.update([
            "constructors",
            "races"
        ])

    # =====================================================
    # Constructor Results
    # =====================================================

    if "constructorResults" in tables:

        tables.update([
            "constructors",
            "races"
        ])

    # =====================================================
    # Qualifying
    # =====================================================

    if "qualifying" in tables:

        tables.update([
            "drivers",
            "constructors",
            "races"
        ])

    # =====================================================
    # Lap Times
    # =====================================================

    if "lapTimes" in tables:

        tables.update([
            "drivers",
            "races"
        ])

    # =====================================================
    # Pit Stops
    # =====================================================

    if "pitStops" in tables:

        tables.update([
            "drivers",
            "races"
        ])

    # =====================================================
    # Status
    # =====================================================

    if "status" in tables:

        tables.add("results")

    # =====================================================
    # Races -> Circuits
    # =====================================================

    if "races" in tables:

        tables.add("circuits")

    return list(tables)


# =========================================================
# Test
# =========================================================

if __name__ == "__main__":

    test_questions = [

        "Show drivers with their constructor names",

        "Show qualifying results",

        "Show pit stops",

        "Show constructor standings",

        "Show Formula 1 seasons"

    ]

    for question in test_questions:

        print("\n" + "=" * 60)

        print("Question:")
        print(question)

        tables = retrieve_tables(question)

        print("\nFinal Relevant Tables:")

        print(tables)
