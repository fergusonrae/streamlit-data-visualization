import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd

lat_long = pd.read_csv("cleaned_data/location_lat_long.csv", index_col=0)[['id', 'latitude', 'longitude', 'latitide_country', 'longitude_country']]
cable = pd.read_csv("cleaned_data/cable.csv", index_col=0)
locations = pd.read_csv("cleaned_data/location.csv", index_col=0)
owners = pd.read_csv("cleaned_data/owner.csv", index_col=0)

location_with_lat_long = locations.merge(lat_long, on='id', how='inner')
assert location_with_lat_long.shape[0] == locations.shape[0]

####################
### data filters ###
####################

min_cable_length = int(cable['length (km)'].min())
max_cable_length = int(cable['length (km)'].max())
length_slider = st.sidebar.slider(
    'Pipeline Length (km)', min_cable_length, max_cable_length, value=(min_cable_length, max_cable_length)
)
filtered_cables = cable[(cable['length (km)'] >= length_slider[0]) & (cable['length (km)'] <= length_slider[1])]
filtered_owners = owners[owners['cable_id'].isin(filtered_cables['cable_id'])]

owner_option = st.sidebar.selectbox(
    'Owner',
    ['All'] + filtered_owners['owner'].drop_duplicates().sort_values().tolist()
)
if owner_option != 'All':
    filtered_owners = filtered_owners[filtered_owners['owner'] == owner_option]
    filtered_cables = cable[cable['cable_id'].isin(filtered_owners['cable_id'])]

cable_option = st.sidebar.selectbox(
    'Cable',
    ['All'] + filtered_cables['cable_name'].drop_duplicates().sort_values().tolist()
)
if cable_option != 'All':
    filtered_cables = cable[cable['cable_name'] == cable_option]
    filtered_owners = filtered_owners[filtered_owners['cable_id'].isin(filtered_cables['cable_id'])]


filtered_locations = location_with_lat_long[location_with_lat_long['cable_id'].isin(filtered_cables['cable_id'])]

################
### Plot Charts ###
################

col1, col2 = st.columns(2, gap='large')

with col1:
    # Select what granularity to view the data
    location_granularity_selectbox = st.selectbox(
        'Location granularity',
        ('Country', 'Lowest Available')
    )

    if location_granularity_selectbox == 'Country':
        filtered_locations = (
            filtered_locations
            .drop(columns=['latitude', 'longitude'])
            .rename(columns={'latitide_country': 'latitude', 'longitude_country': 'longitude'})
        )
    elif location_granularity_selectbox == 'Lowest Available':
        st.text("Granularity varies by location. Use caution as not all data is the same granularity.")

    st.map(filtered_locations[['latitude', 'longitude']])

with col2:
    st.header("A dog")