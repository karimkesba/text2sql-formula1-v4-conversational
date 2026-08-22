import streamlit as st
import sqlite3
import pandas as pd

from llm import generate_sql
from db import get_relevant_schema
from conversation_manager import classify_question
from sql_modifier import modify_sql


# =========================================================
# Streamlit Configuration
# =========================================================

st.set_page_config(
    page_title="Chat with Data",
    layout="wide"
)

st.title("Chat with Formula 1 Database")


# =========================================================
# Session State
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = []


# =========================================================
# Database
# =========================================================

DB_PATH = "C:/Users/Admin/python/chat_with_data/formula_1.sqlite"


# =========================================================
# Question Input
# =========================================================

question = st.text_input(
    "Ask your question:",
    placeholder="Example: Show race names with circuit names"
)


# =========================================================
# Ask
# =========================================================

if st.button("Ask"):

    if not question.strip():

        st.warning("Please enter a question.")

    else:

        history = st.session_state.history

        # =================================================
        # Step 1: Classify Question
        # =================================================

        question_type = classify_question(
            question,
            history
        )

        print("\n" + "=" * 60)
        print("Original Question:")
        print(question)

        print("\nQuestion Type:")
        print(question_type)

        print("=" * 60)


        # =================================================
        # Step 2: Open Database
        # =================================================

        conn = sqlite3.connect(DB_PATH)

        try:

            # =================================================
            # NEW QUESTION
            # =================================================

            if question_type == "new":

                rewritten_question = question

                print("\nNew independent question.")

                # -----------------------------------------
                # Retrieve relevant schema
                # -----------------------------------------

                schema = get_relevant_schema(
                    rewritten_question
                )

                # -----------------------------------------
                # Generate SQL from scratch
                # -----------------------------------------

                sql = generate_sql(
                    rewritten_question,
                    schema
                )


            # =================================================
            # FOLLOW-UP QUESTION
            # =================================================

            elif question_type == "follow_up":

                if not history:

                    raise ValueError(
                        "Follow-up question requires conversation history."
                    )

                # -----------------------------------------
                # Get previous successful SQL
                # -----------------------------------------

                previous = history[-1]

                previous_sql = previous["sql"]

                previous_question = previous.get(
                    "rewritten_question",
                    previous["question"]
                )

                print("\n" + "=" * 60)

                print("Previous Question:")
                print(previous_question)

                print("\nPrevious SQL:")
                print(previous_sql)

                print("\nFollow-up Question:")
                print(question)

                print("=" * 60)

                # -----------------------------------------
                
                
                sql = modify_sql(
                    previous_sql,
                    question
                )

                # -----------------------------------------
                # Keep a readable conversation context
                # -----------------------------------------

                rewritten_question = (
                    f"{previous_question} "
                    f"Follow-up: {question}"
                )


            # =================================================
            # SQL MODIFICATION
            # =================================================

            elif question_type == "sql_modification":

                if not history:

                    raise ValueError(
                        "SQL modification requires conversation history."
                    )

                # -----------------------------------------
                # Get previous SQL
                # -----------------------------------------

                previous = history[-1]

                previous_sql = previous["sql"]

                previous_question = previous.get(
                    "rewritten_question",
                    previous["question"]
                )

                print("\n" + "=" * 60)

                print("Previous Question:")
                print(previous_question)

                print("\nPrevious SQL:")
                print(previous_sql)

                print("\nModification Request:")
                print(question)

                print("=" * 60)

                # -----------------------------------------
                # Modify previous SQL
                # -----------------------------------------

                sql = modify_sql(
                    previous_sql,
                    question
                )

                # -----------------------------------------
                # Preserve previous context
                # -----------------------------------------

                rewritten_question = (
                    f"{previous_question} "
                    f"Modification: {question}"
                )


            # =================================================
            # FALLBACK
            # =================================================

            else:

                rewritten_question = question

                schema = get_relevant_schema(
                    rewritten_question
                )

                sql = generate_sql(
                    rewritten_question,
                    schema
                )


            # =================================================
            # Step 3: Display Question Type
            # =================================================

            st.subheader("Question Type")

            st.info(question_type)


            # =================================================
            # Step 4: Display Rewritten Question
            # =================================================

            if rewritten_question != question:

                st.subheader("Context")

                st.write(
                    rewritten_question
                )


            # =================================================
            # Step 5: Display SQL
            # =================================================

            st.subheader("Generated SQL")

            st.code(
                sql,
                language="sql"
            )


            # =================================================
            # Step 6: Execute SQL
            # =================================================

            df = pd.read_sql_query(
                sql,
                conn
            )


            # =================================================
            # Step 7: Display Results
            # =================================================

            st.subheader("Results")

            st.dataframe(
                df,
                width="stretch"
            )


            # =================================================
            # Step 8: Convert Result To Answer
            # =================================================

            if df.empty:

                answer = "No results found."

            elif df.shape == (1, 1):

                answer = str(
                    df.iloc[0, 0]
                )

            else:

                answer = df.to_string(
                    index=False
                )


            # =================================================
            # Step 9: Display Answer
            # =================================================

            st.subheader("Answer")

            st.write(answer)


            # =================================================
            # Step 10: Save Conversation
            # =================================================

            st.session_state.history.append({

                "question":
                    question,

                "rewritten_question":
                    rewritten_question,

                "sql":
                    sql,

                "answer":
                    answer,

                "question_type":
                    question_type

            })


        except Exception as e:

            st.error(
                f"SQL Error:\n{e}"
            )

            print("\nSQL ERROR:")
            print(e)


        finally:

            conn.close()


# =========================================================
# Conversation History UI
# =========================================================

if st.session_state.history:

    st.sidebar.title(
        "Conversation History"
    )

    for i, item in enumerate(
        st.session_state.history,
        start=1
    ):

        st.sidebar.markdown(
            f"**{i}. {item['question']}**"
        )

        st.sidebar.caption(
            f"Type: {item.get('question_type', 'unknown')}"
        )

        if (
            item["rewritten_question"]
            != item["question"]
        ):

            st.sidebar.caption(
                "Context:"
            )

            st.sidebar.write(
                item["rewritten_question"]
            )

        st.sidebar.code(
            item["sql"],
            language="sql"
        )

        st.sidebar.write(
            f"Answer: {item['answer']}"
        )

        st.sidebar.divider()