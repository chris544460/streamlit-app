import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import logging
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st
import json

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    # Define the scope for accessing Google Sheets and Google Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # # Provide the path to the downloaded JSON credentials file
    # creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    # st.write('Credentials loaded successfully.')

    # Load credentials from Streamlit secrets
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
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

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    st.write('Data converted to DataFrame successfully.')

    # Filter the data by 'Type'
    worries = df[df['Type'] == 'Worry']
    ambitions = df[df['Type'] == 'Ambition']
    st.write('Data filtered by Type successfully.')

    # Define the quadrants
    mid_prob = 3
    mid_impact = 3

    # Create the Plotly figure
    fig = make_subplots()

    # Add the quadrants as shapes
    fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=mid_prob, y1=mid_impact,
                  fillcolor="lightgreen", opacity=0.3, line_width=0)
    fig.add_shape(type="rect", x0=mid_prob, y0=0.5, x1=5.5, y1=mid_impact,
                  fillcolor="lightcoral", opacity=0.3, line_width=0)
    fig.add_shape(type="rect", x0=0.5, y0=mid_impact, x1=mid_prob, y1=5.5,
                  fillcolor="lightblue", opacity=0.3, line_width=0)
    fig.add_shape(type="rect", x0=mid_prob, y0=mid_impact, x1=5.5, y1=5.5,
                  fillcolor="lightsalmon", opacity=0.3, line_width=0)

    # Function to apply alternating offset to avoid label overlap
    def apply_alternating_offset(df, offset=0.15):
        df_sorted = df.sort_values(by=['Impact/Benefit Value'], ascending=False).reset_index(drop=True)
        for i in range(1, len(df_sorted)):
            if abs(df_sorted.loc[i, 'Impact/Benefit Value'] - df_sorted.loc[i-1, 'Impact/Benefit Value']) < offset:
                # Alternate the direction of the offset
                if i % 2 == 0:
                    df_sorted.loc[i, 'Impact/Benefit Value'] += offset  # Move up
                else:
                    df_sorted.loc[i, 'Impact/Benefit Value'] -= offset  # Move down
        return df_sorted

    # Apply alternating offset to worries and ambitions
    worries = apply_alternating_offset(worries)
    ambitions = apply_alternating_offset(ambitions)
    st.write('Applied alternating offset to avoid label overlap.')

    # Add worries as scatter points with dynamic text positioning
    fig.add_trace(go.Scatter(
        x=worries['Prob. Value'],
        y=worries['Impact/Benefit Value'],
        mode='markers+text',
        text=worries['Description'],
        textposition='top center',
        marker=dict(color='darkred', size=10),
        name='Worries'
    ))

    # Add ambitions as scatter points with dynamic text positioning
    fig.add_trace(go.Scatter(
        x=ambitions['Prob. Value'],
        y=ambitions['Impact/Benefit Value'],
        mode='markers+text',
        text=ambitions['Description'],
        textposition='top center',
        marker=dict(color='darkgreen', size=10),
        name='Ambitions'
    ))
    st.write('Added scatter points for worries and ambitions.')

    # Update layout to add more padding and avoid cutting off text
    fig.update_layout(
        title='Probability-Impact/Benefit Matrix',
        xaxis=dict(range=[0.25, 5.75], title='Probability', showgrid=True, zeroline=False),
        yaxis=dict(range=[0.25, 5.75], title='Impact/Benefit', showgrid=True, zeroline=False),
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.1),  # Move the legend further to the right
        width=1000,  # Increase the figure width
        height=700,  # Increase the figure height
        margin=dict(l=50, r=150, t=50, b=50)  # Add more padding on the left and right
    )
    st.write('Figure layout updated.')

    # Display the graph in Streamlit
    st.plotly_chart(fig)
    st.write('Plotly chart displayed in Streamlit.')

    st.write("This dashboard is automatically updated when your Google Sheet data changes.")
    st.write('Streamlit write command executed.')

except Exception as e:
    logging.error(f'An error occurred: {e}')
