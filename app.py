import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# === Google Sheets setup ===
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_ID = "1jeFVg8qFl26uGDhXmCvCIRdL6kDTWAjrmiPjceQYsSs"

# Load credentials from Streamlit secrets
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).sheet1

# Load data from Google Sheets
@st.cache_data(ttl=60)
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()

# === Streamlit UI ===
st.title("🧠 Mood Tracker")

time_of_day = st.radio("Time of Day", ["Morning", "Evening"])
mood = st.slider("Mood (from -4 to +4)", -4, 4, 0)
sleep_hours = st.number_input("How many hours did you sleep?", min_value=0.0, max_value=24.0, step=0.5)
note = st.text_area("Notes (optional)")

if st.button("💾 Save Entry"):
    today = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")
    row = [today, time_of_day, mood, sleep_hours, note]
    sheet.append_row(row)
    st.success("Entry saved! Please reload the app to see updated graph.")

# === Dot Chart ===
st.subheader("📊 Monthly Mood Matrix")

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"])

    today = pd.Timestamp.today().normalize()
    df = df[df["date"].dt.month == today.month]

    df["day"] = df["date"].dt.day
    df["x_offset"] = df["time_of_day"].apply(lambda t: -0.2 if t.lower() == "morning" else 0.2)

    # Custom colors from dark red (-4) to light gray (0) to dark green (+4)
    custom_colors = [
        "#8B0000",  # -4 dark red
        "#B22222",  # -3 firebrick
        "#CD5C5C",  # -2 indian red
        "#F08080",  # -1 light coral
        "#D3D3D3",  #  0 light gray
        "#90EE90",  # +1 light green
        "#32CD32",  # +2 lime green
        "#228B22",  # +3 forest green
        "#006400"   # +4 dark green
    ]

    fig, ax = plt.subplots(figsize=(14, 6))

    for _, row in df.iterrows():
        try:
            mood_index = int(float(row["mood"])) + 4
            color = custom_colors[mood_index]
            ax.scatter(
                row["day"] + row["x_offset"],
                float(row["mood"]),
                color=color,
                s=100,
                edgecolors="black",
                linewidths=0.5,
                zorder=3
            )
        except Exception:
            continue

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
    st.info("No data available.")
