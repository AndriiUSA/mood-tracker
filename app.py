import streamlit as st
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Path to data file
DATA_FILE = "mood_data.csv"

# Load or initialize data
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"])
else:
    df = pd.DataFrame(columns=["date", "time_of_day", "mood", "sleep_hours", "note"])

# --- Input Interface ---
st.title("🧠 Mood Tracker")

time_of_day = st.radio("Time of Day", ["Morning", "Evening"])
mood = st.slider("Mood (from -4 to +4)", -4, 4, 0)
sleep_hours = st.number_input("How many hours did you sleep?", min_value=0.0, max_value=24.0, step=0.5)
note = st.text_area("Notes (optional)")

if st.button("💾 Save Entry"):
    new_entry = pd.DataFrame([{
        "date": pd.Timestamp.today().normalize().date(),
        "time_of_day": time_of_day,
        "mood": mood,
        "sleep_hours": sleep_hours,
        "note": note
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("Entry saved!")

# --- Mood Dot Matrix Chart ---
st.subheader("📊 Monthly Mood Matrix (Morning / Evening)")

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"])

    # Filter to current month
    today = pd.Timestamp.today().normalize()
    df = df[df["date"].dt.month == today.month]

    df["day"] = df["date"].dt.day
    df["x_offset"] = df["time_of_day"].apply(lambda t: -0.2 if t == "Morning" else 0.2)

    palette = sns.color_palette("coolwarm", 9)  # from -4 to +4

    fig, ax = plt.subplots(figsize=(14, 6))

    for _, row in df.iterrows():
        mood_index = int(row["mood"]) + 4
        color = palette[mood_index]
        ax.scatter(
            row["day"] + row["x_offset"],
            row["mood"],
            color=color,
            s=100,
            edgecolors="black",
            linewidths=0.5,
            zorder=3
        )

    ax.set_xlim(0.5, 31.5)
    ax.set_xticks(range(1, 32))
    ax.set_ylim(-4.5, 4.5)
    ax.set_yticks(range(-4, 5))
    ax.set_xlabel("Day of Month")
    ax.set_ylabel("Mood")
    ax.set_title("Mood Chart (Morning and Evening)")
    ax.grid(True, linestyle="dotted", alpha=0.4, zorder=0)
    ax.set_facecolor("#f8f8f8")

    st.pyplot(fig)
else:
    st.info("No data to display.")
