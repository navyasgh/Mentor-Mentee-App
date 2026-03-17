import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Mentor-Mentee Portal", layout="wide")

st.title("Mentor–Mentee Communication Portal")

# -----------------------------
# Mentor-Mentee Mapping
# -----------------------------
mentor_mentees = {
    "Mentor1": ["Mentee1","Mentee2","Mentee3","Mentee4","Mentee5"],
    "Mentor2": ["Mentee6","Mentee7","Mentee8","Mentee9","Mentee10"]
}

all_users = ["Admin","Mentor1","Mentor2"] + mentor_mentees["Mentor1"] + mentor_mentees["Mentor2"]

# -----------------------------
# Helper Function
# -----------------------------
def get_mentor(mentee):
    mentee = mentee.strip()
    for mentor, mentees in mentor_mentees.items():
        if mentee in [m.strip() for m in mentees]:
            return mentor
    return None

# -----------------------------
# Session State
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -----------------------------
# Database
# -----------------------------
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages(
    sender TEXT,
    receiver TEXT,
    message TEXT,
    time TEXT
)
""")
conn.commit()

# -----------------------------
# Sidebar Login
# -----------------------------
st.sidebar.header("Login")

if not st.session_state.logged_in:

    name = st.sidebar.selectbox("Select User", all_users)

    if name == "Admin":
        role = "Admin"
    elif name in mentor_mentees:
        role = "Mentor"
    else:
        role = "Mentee"

    if st.sidebar.button("Login"):
        st.session_state.logged_in = True
        st.session_state.name = name
        st.session_state.role = role
        st.rerun()

else:
    st.sidebar.success(f"{st.session_state.name} ({st.session_state.role})")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# -----------------------------
# MAIN APP
# -----------------------------
if st.session_state.logged_in:

    user = st.session_state.name
    role = st.session_state.role

    # -----------------------------
    # Mentor Dashboard
    # -----------------------------
    if role == "Mentor":

        st.header("Mentor Dashboard")

        mentees = mentor_mentees[user]

        st.write("### Your Mentees")
        st.table(mentees)

        st.write("### Total Mentees:", len(mentees))

        cursor.execute("SELECT COUNT(*) FROM messages WHERE sender=?", (user,))
        sent_count = cursor.fetchone()[0]

        st.write("### Messages Sent:", sent_count)

        st.divider()

    # -----------------------------
    # Layout
    # -----------------------------
    col1, col2 = st.columns(2)

    # -----------------------------
    # SEND MESSAGE
    # -----------------------------
    with col1:
        st.subheader("Send Message")

        receiver = None

        if role == "Admin":
            receiver = st.selectbox("Select Receiver", all_users)

        elif role == "Mentor":
            receiver = st.selectbox("Select Receiver", mentor_mentees[user])

        elif role == "Mentee":
            mentor = get_mentor(user)
            if mentor:
                receiver = mentor
                st.write(f"Sending to: **{mentor}**")
            else:
                st.error("No mentor assigned!")

        message = st.text_area("Write Message")

        if st.button("Send Message"):

            if not message:
                st.warning("Enter message")

            elif role == "Mentor" and receiver not in mentor_mentees[user]:
                st.error("You can only message your assigned mentees!")

            elif role == "Mentee":
                mentor = get_mentor(user)
                if receiver != mentor:
                    st.error("You can only message your mentor!")
                else:
                    time = datetime.now().strftime("%H:%M")

                    cursor.execute(
                        "INSERT INTO messages VALUES (?,?,?,?)",
                        (user, receiver, message, time)
                    )
                    conn.commit()

                    st.success("Message Sent!")

            elif receiver:
                time = datetime.now().strftime("%H:%M")

                cursor.execute(
                    "INSERT INTO messages VALUES (?,?,?,?)",
                    (user, receiver, message, time)
                )
                conn.commit()

                st.success("Message Sent!")

    # -----------------------------
    # INBOX
    # -----------------------------
    with col2:
        st.subheader("Inbox")

        cursor.execute("SELECT * FROM messages WHERE receiver=?", (user,))
        rows = cursor.fetchall()

        st.write(f"Messages Received: {len(rows)}")

        if rows:
            for row in rows:
                st.info(f"From **{row[0]}** at {row[3]}\n\n{row[2]}")
        else:
            st.write("No messages")

    st.divider()

    # -----------------------------
    # OUTBOX
    # -----------------------------
    st.subheader("📤 Outbox")

    cursor.execute("SELECT * FROM messages WHERE sender=?", (user,))
    sent = cursor.fetchall()

    if sent:
        for row in sent:
            st.write(f"To **{row[1]}** at {row[3]} : {row[2]}")
    else:
        st.write("No sent messages")

    # -----------------------------
    # CLEAR INBOX
    # -----------------------------
    if st.button("🗑 Clear Inbox"):
        cursor.execute("DELETE FROM messages WHERE receiver=?", (user,))
        conn.commit()
        st.success("Inbox Cleared!")

else:
    st.write("Please login from sidebar")