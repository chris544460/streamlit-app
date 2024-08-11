import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta

# Display a message to indicate the app is running
st.write("Connecting to Google Sheets...")

try:
    # Define the scope for accessing Google Sheets and Google Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    st.write('Credentials loaded successfully.')

    # # Load credentials directly from Streamlit secrets or from a file
    # creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    # st.write('Credentials loaded successfully.')

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

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    st.write('Data converted to DataFrame successfully.')

    # Filter the data by 'Type'
    worries = df[df['Type'] == 'Worry']
    ambitions = df[df['Type'] == 'Ambition']
    st.write('Data filtered by Type successfully.')

    # Current date
    today = datetime.now().date()

    # Function to calculate the time dimension (days until deadline)
    def calculate_days_until_deadline(df):
        df = df.copy()  # Ensure you're working with a copy of the DataFrame to avoid warnings
        
        # Convert 'Deadline Date' to datetime, handling errors
        df['Deadline Date'] = pd.to_datetime(df['Deadline Date'], errors='coerce').dt.date
        
        # Handle any NaT values that result from failed conversions
        if df['Deadline Date'].isnull().any():
            st.error("Some dates in 'Deadline Date' could not be parsed. Please check the format in your Google Sheet.")
        
        # Calculate days remaining until the deadline
        df['Days Until Deadline'] = (df['Deadline Date'] - today).apply(lambda x: max(int(x.days), 0) if pd.notnull(x) else None)
        
        return df

    # Apply the function to your worries and ambitions DataFrames
    worries = calculate_days_until_deadline(worries)
    ambitions = calculate_days_until_deadline(ambitions)

    # Normalize days until deadline to determine marker size
    def normalize_sizes(days_until_deadline, min_size=5, max_size=20):
        min_days = days_until_deadline.min()
        max_days = days_until_deadline.max()
        # Invert the normalization to make closer deadlines have larger sizes
        normalized_sizes = max_size - (days_until_deadline - min_days) / (max_days - min_days) * (max_size - min_size)
        return normalized_sizes

    # Calculate marker sizes for worries and ambitions
    worries['Marker Size'] = normalize_sizes(worries['Days Until Deadline'])
    ambitions['Marker Size'] = normalize_sizes(ambitions['Days Until Deadline'])

    # Create the 3D Plotly figure
    fig = make_subplots(specs=[[{'type': 'scatter3d'}]])

    st.write("Adding 3D scatter plots...")

    # Define the ranges for the quadrants
    x_mid = 3
    y_mid = 3
    z_min = 0
    z_max = max(worries['Days Until Deadline'].max(), ambitions['Days Until Deadline'].max()) + 1  # Extending slightly above the max Z value

    # Add parallelepipeds for each quadrant
    fig.add_trace(go.Mesh3d(
        x=[0.5, x_mid, x_mid, 0.5, 0.5, x_mid, x_mid, 0.5],
        y=[0.5, 0.5, y_mid, y_mid, 0.5, 0.5, y_mid, y_mid],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        color='lightgreen',
        opacity=0.3,
        name='Low Probability, Low Impact'
    ))

    fig.add_trace(go.Mesh3d(
        x=[x_mid, 5.5, 5.5, x_mid, x_mid, 5.5, 5.5, x_mid],
        y=[0.5, 0.5, y_mid, y_mid, 0.5, 0.5, y_mid, y_mid],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        color='lightcoral',
        opacity=0.3,
        name='High Probability, Low Impact'
    ))

    fig.add_trace(go.Mesh3d(
        x=[0.5, x_mid, x_mid, 0.5, 0.5, x_mid, x_mid, 0.5],
        y=[y_mid, y_mid, 5.5, 5.5, y_mid, y_mid, 5.5, 5.5],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        color='lightblue',
        opacity=0.3,
        name='Low Probability, High Impact'
    ))

    fig.add_trace(go.Mesh3d(
        x=[x_mid, 5.5, 5.5, x_mid, x_mid, 5.5, 5.5, x_mid],
        y=[y_mid, y_mid, 5.5, 5.5, y_mid, y_mid, 5.5, 5.5],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        color='lightsalmon',
        opacity=0.3,
        name='High Probability, High Impact'
    ))

    # Add worries as scatter points in 3D
    fig.add_trace(go.Scatter3d(
        x=worries['Prob. Value'],
        y=worries['Impact/Benefit Value'],
        z=worries['Days Until Deadline'],
        mode='markers+text',
        text=worries['Description'],
        marker=dict(color='darkred', size=worries['Marker Size']),
        name='Worries'
    ))

    # Add ambitions as scatter points in 3D
    fig.add_trace(go.Scatter3d(
        x=ambitions['Prob. Value'],
        y=ambitions['Impact/Benefit Value'],
        z=ambitions['Days Until Deadline'],
        mode='markers+text',
        text=ambitions['Description'],
        marker=dict(color='darkgreen', size=ambitions['Marker Size']),
        name='Ambitions'
    ))

    # Update layout to reflect the 3D nature of the visualization
    fig.update_layout(
        title='3D Probability-Impact/Benefit-Time Matrix',
        scene=dict(
            xaxis=dict(title='Probability'),
            yaxis=dict(title='Impact/Benefit'),
            zaxis=dict(title='Days Until Deadline'),
        ),
        width=1000,
        height=700,
        margin=dict(l=50, r=150, t=50, b=50)
    )

    st.write('3D figure layout updated.')

    # Display the 3D graph in Streamlit
    st.plotly_chart(fig)
    st.write('3D Plotly chart displayed in Streamlit.')

    st.write("This dashboard is automatically updated when your Google Sheet data changes.")

except Exception as e:
    st.error("An error occurred while fetching data from Google Sheets.")
    st.text(str(e))
