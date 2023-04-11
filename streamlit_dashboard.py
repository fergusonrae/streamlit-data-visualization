import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd

LAT_LONG_URL = "https://streamlit-clean.s3.amazonaws.com/location_lat_long.csv"
CABLE_URL = "https://streamlit-clean.s3.amazonaws.com/cable.csv"
LOCATIONS_URL = "https://streamlit-clean.s3.amazonaws.com/location.csv"
OWNERS_URL = "https://streamlit-clean.s3.amazonaws.com/owner.csv"

####################
### collect data ###
####################
@st.cache_data
def fetch_and_cache_data(url):
    return pd.read_csv(url, index_col=0)

lat_long = fetch_and_cache_data(LAT_LONG_URL)[['id', 'latitude', 'longitude', 'latitide_country', 'longitude_country']]
cable = fetch_and_cache_data(CABLE_URL)
locations = fetch_and_cache_data(LOCATIONS_URL)
owners = fetch_and_cache_data(OWNERS_URL)

location_with_lat_long = locations.merge(lat_long, on='id', how='inner')
assert location_with_lat_long.shape[0] == locations.shape[0]

####################
### data filters ###
####################

st.sidebar.caption("Select filters from top to bottom")

min_cable_length = int(cable['length (km)'].min())
max_cable_length = int(cable['length (km)'].max())
length_slider = st.sidebar.slider(
    'Pipeline Length (km)', min_cable_length, max_cable_length, value=(min_cable_length, max_cable_length)
)
include_length_nulls = st.sidebar.checkbox("Include cables with missing length", value=True)

cable_length_filter =(cable['length (km)'] >= length_slider[0]) & (cable['length (km)'] <= length_slider[1])
if include_length_nulls:
    filtered_cables = cable[cable_length_filter | cable['length (km)'].isnull()]
else:
    filtered_cables = cable[cable_length_filter]
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

###################
### Plot Charts ###
###################

col1, col2 = st.columns(2, gap='large')

# Map of cable landings
with col1:
    st.subheader("Map of cable landings")

    # Select what granularity to view the data
    location_granularity_selectbox = st.selectbox(
        'Location granularity',
        ('Country', 'Lowest Available')
    )

    if location_granularity_selectbox == 'Country':
        # Change lat/long of locations to be the overall country coordinates
        filtered_locations = (
            filtered_locations
            .drop(columns=['latitude', 'longitude'])
            .rename(columns={'latitide_country': 'latitude', 'longitude_country': 'longitude'})
        )
    elif location_granularity_selectbox == 'Lowest Available':
        # Create alert that data may not be the best
        st.warning("Granularity varies by location. Use caution as not all data is the same granularity.")

    st.map(filtered_locations[['latitude', 'longitude']])

# Bar charts showing counting landing city counts
with col2:
    n_countries = 20

    st.subheader(f"Top {n_countries} countries with the highest count of cable landings")
    st.caption("""
        count: A single cable landing point will be counted multiple times if accessed by multiple cables
        \nnunique: A single cable landing point will be counted only once even if accessed by multiple cables
        """)
    total_counts = (
        filtered_locations
        .groupby('country')
        .agg({'id': ['count', pd.Series.nunique]})
    )
    total_counts.columns = total_counts.columns.droplevel(0)
    total_counts = total_counts.reset_index().sort_values('count', ascending=False).head(n_countries)
    st.bar_chart(total_counts, x='country')
