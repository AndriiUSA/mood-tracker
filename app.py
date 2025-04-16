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

# Mood color gradient
custom_colors = [
    "#8B0000",  # -4
    "#B22222",  # -3
    "#CD5C5C",  # -2
    "#F08080",  # -1
    "#D3D3D3",  #  0
    "#90EE90",  # +1
    "#32CD32",  # +2
    "#228B22",  # +3
    "#006400"   # +4
]

time_of_day = st.radio("Time of Day", ["Morning", "Evening"])
mood = st.slider("Mood (from -4 to +4)", -4, 4, 0)

# Color for current mood
mood_index = mood + 4
mood_color = custom_colors[mood_index]

# Large color-changing number
st.markdown(
    f'<div style="font-size: 48px; font-weight: bold; color: {mood_color}; text-align: center;">{mood}</div>',
    unsafe_allow_html=True
)

sleep_hours = st.number_input("How many hours did you sleep?", min_value=0.0, max_value=24.0, step=0.5)
note = st.text_area("Notes (optional)")

if st.button("💾 Save Entry"):
    today = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")
    row = [today, time_of_day, mood, sleep_hours, note]
    sheet.append_row(row)
    st.success("Entry saved! Please reload the app to see updated graph.")

# === Mood Line Chart ===
st.subheader("📈 Mood Trend")

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"])

    today = pd.Timestamp.today().normalize()
    df = df[df["date"].dt.month == today.month]

    time_sort_map = {"Morning": 0, "Evening": 1}
    df["sort_key"] = df["time_of_day"].map(lambda x: time_sort_map.get(x, 1))
    df = df.sort_values(by=["date", "sort_key"]).reset_index(drop=True)

    df["day"] = df["date"].dt.day + df["sort_key"] * 0.5

    fig, ax = plt.subplots(figsize=(14, 6))

    # Line
    ax.plot(df["day"], df["mood"], linestyle="solid", color="#666", linewidth=2, alpha=0.7)

    # Colored dots
    for _, row in df.iterrows():
        mood_index = int(float(row["mood"])) + 4
        color = custom_colors[mood_index]
        ax.scatter(
            row["day"],
            float(row["mood"]),
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
    ax.set_title("Mood Chart (Smoothed Line + Color Points)")
    ax.grid(True, linestyle="dotted", alpha=0.4, zorder=0)
    ax.set_facecolor("#f8f8f8")

    st.pyplot(fig)
else:
    st.info("No data available.")
