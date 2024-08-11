import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

st.write("Connecting to Google Sheets...")

try:
    # Define the scope for accessing Google Sheets and Google Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Load credentials directly from Streamlit secrets
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    st.write('Credentials loaded successfully.')

    # Authorize the client to interact with Google Sheets
    client = gspread.authorize(creds)
    st.write('Authorized the Google Sheets client.')

    # Open the Google Sheet by its name
    sheet = client.open('Worries')
    st.write('Google Sheet opened successfully.')

    # Select the first worksheet
    worksheet = sheet.get_worksheet(0)  # Index 0 is the first sheet
    st.write('Worksheet selected successfully.')

    # Fetch all data from the sheet
    data = worksheet.get_all_records()
    st.write('Data fetched successfully from the worksheet.')

    # Display a sample of the data
    st.write(data[:5])

except Exception as e:
    st.error("An error occurred while fetching data from Google Sheets.")
    st.text(str(e))
