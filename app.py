import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import time

# Cache data globally to avoid multiple requests
@st.cache_data(show_spinner=False)
def load_data():
    # Define the scope for accessing Google Sheets and Google Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Load credentials directly from Streamlit secrets or from a file
    # creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    # print('Credentials loaded successfully.')

    # Authorize the client to interact with Google Sheets
    client = gspread.authorize(creds)

    # Open the Google Sheet by its name
    sheet = client.open('Worries')

    # Select the first worksheet
    worksheet = sheet.get_worksheet(0)  # Index 0 is the first sheet

    # Fetch all data from the sheet
    data = worksheet.get_all_records()

    return pd.DataFrame(data)

# Display a message to indicate the app is running
print("Connecting to Google Sheets...")

# Add a button to refresh the data
if st.button('Refresh Data'):
    # Clear the cached data
    st.cache_data.clear()
    st.write("Data cache cleared. Reloading data...")

try:
    print("Connecting to Google Sheets...")

    # Load data from Google Sheets (cached)
    df = load_data()

    print('Data fetched successfully from the worksheet and cached.')

    # Filter the data by 'Type'
    worries = df[df['Type'] == 'Worry']
    ambitions = df[df['Type'] == 'Ambition']
    print('Data filtered by Type successfully.')

    # Allow the user to select the Day 0 date
    day_zero = st.date_input("Select Day 0 (Start Date)", datetime.now().date())
    
    # Allow the user to select the number of days until the deadline
    days_until = st.slider("Number of Days Until Deadline Extends", min_value=1, max_value=90, value=7)
    
    # Function to calculate the time dimension (days until deadline)
    def calculate_days_until_deadline(df, day_zero):
        df = df.copy()  # Ensure you're working with a copy of the DataFrame to avoid warnings
        
        # Convert 'Deadline Date' to datetime, handling errors
        df['Deadline Date'] = pd.to_datetime(df['Deadline Date'], errors='coerce').dt.date
        
        # Handle any NaT values that result from failed conversions
        if df['Deadline Date'].isnull().any():
            st.error("Some dates in 'Deadline Date' could not be parsed. Please check the format in your Google Sheet.")
        
        # Calculate days remaining until the deadline based on user-specified day_zero
        df['Days Until Deadline'] = (df['Deadline Date'] - day_zero).apply(lambda x: max(int(x.days), 0) if pd.notnull(x) else None)
        
        return df

    # Apply the function to your worries and ambitions DataFrames
    worries = calculate_days_until_deadline(worries, day_zero)
    ambitions = calculate_days_until_deadline(ambitions, day_zero)

    # Less steep linear function for marker sizes based on days until the deadline
    def linear_size(days_until_deadline, max_size=30, min_size=10, steepness=2):
        # Adjusted linear function: size decreases less steeply with the number of days
        size = max_size - (days_until_deadline * steepness)
        return size.clip(lower=min_size)  # Ensure the size does not go below min_size

    # Calculate marker sizes for worries and ambitions
    worries['Marker Size'] = linear_size(worries['Days Until Deadline'])
    ambitions['Marker Size'] = linear_size(ambitions['Days Until Deadline'])

    # Create the 3D Plotly figure
    fig = make_subplots(specs=[[{'type': 'scatter3d'}]])

    print("Adding 3D scatter plots...")

    # Add worries as scatter points in 3D
    fig.add_trace(go.Scatter3d(
        x=worries['Days Until Deadline'],
        y=worries['Impact/Benefit Value'],
        z=worries['Prob. Value'],
        mode='markers+text',
        text=worries['Description'],
        marker=dict(color='darkred', size=worries['Marker Size']),
        name='Worries'
    ))

    # Add ambitions as scatter points in 3D
    fig.add_trace(go.Scatter3d(
        x=ambitions['Days Until Deadline'],
        y=ambitions['Impact/Benefit Value'],
        z=ambitions['Prob. Value'],
        mode='markers+text',
        text=ambitions['Description'],
        marker=dict(color='darkgreen', size=ambitions['Marker Size']),
        name='Ambitions'
    ))

    # Update layout to improve mobile view and adjust camera perspective
    fig.update_layout(
        title='3D Days Until Deadline - Impact/Benefit - Probability Matrix',
        scene=dict(
            xaxis=dict(title='Days Until Deadline', range=[days_until, 0]),  # Reverse the X-axis
            yaxis=dict(title='Impact/Benefit'),
            zaxis=dict(title='Probability'),
            camera=dict(
                eye=dict(x=2, y=2, z=2)  # Adjust the initial camera position to make the plot less zoomed-in
            )
        ),
        width=1000,
        height=700,
        margin=dict(l=50, r=150, t=50, b=50),
        autosize=True,  # Allow the plot to adjust its size based on the screen size
        scene_dragmode='orbit',  # Enable 3D orbit interaction mode
    )

    print('3D figure layout updated.')

    # Display the 3D graph in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    print('3D Plotly chart displayed in Streamlit.')

    print("This dashboard is automatically updated when your Google Sheet data changes.")

except Exception as e:
    st.error("An error occurred while fetching data from Google Sheets.")
    st.text(str(e))