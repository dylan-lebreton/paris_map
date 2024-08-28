import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import pandas as pd

def arrondissements_geojson():
    url = "https://opendata.paris.fr/explore/dataset/arrondissements/download/?format=geojson&timezone=Europe/Berlin&lang=fr"
    response = requests.get(url)
    return response.json()

def arrondissements_dataframe():
    url = "https://opendata.paris.fr/explore/dataset/arrondissements/download/?format=csv&timezone=Europe/Berlin&lang=fr"
    df = pd.read_csv(url, sep=";")
    df = df[['c_ar', 'l_aroff', 'l_ar']].rename(columns={"c_ar": "numero", "l_ar": "nom_1", "l_aroff": "nom_2"}).sort_values("numero").reset_index(drop=True)
    df['Information'] = df['nom_1'].str.replace("Ardt", "Arrondissement") + " (" + df['nom_2'] + ")"
    return df

def metro_dataframe():
    url = "https://data.iledefrance-mobilites.fr/explore/dataset/arrets-lignes/download/?format=csv&timezone=Europe/Berlin&lang=fr"
    df = pd.read_csv(url, sep=";")
    
    # Renommer les modes de transport en français
    mode_translation = {
        'Metro': 'Métro',
        'regionalRail': 'TER',  # Basé sur les observations précédentes
        'LocalTrain': 'Transilien',
        'Tramway': 'Tramway',
        'Bus': 'Bus',
        'RailShuttle': 'Navette ferroviaire',
        'RapidTransit': 'RER',
        'Funicular': 'Funiculaire'
    }
    
    df['mode'] = df['mode'].map(mode_translation)
    df['nom'] = df['mode'] + " " + df['route_long_name']
    df['info'] = df['nom'] + ' - ' + df['stop_name']
    return df

def arrondissements_map():
    fig = px.choropleth_mapbox(arrondissements_dataframe(), geojson=arrondissements_geojson(),
                               locations="numero", featureidkey="properties.c_ar",
                               color="Information", hover_name="Information",
                               mapbox_style="open-street-map", zoom=11, center={"lat": 48.8566, "lon": 2.3522}, opacity=0.5,
                               hover_data={col : False for col in arrondissements_dataframe().columns})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, showlegend=True)
    return fig


def stations_map(stations: pd.DataFrame):
    fig = px.scatter_mapbox(stations, lat="stop_lat", lon="stop_lon", color="nom", hover_name="info", hover_data={col: False for col in stations.columns},
                            mapbox_style="open-street-map", zoom=11, center={"lat": 48.8566, "lon": 2.3522})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, showlegend=True)
    fig.update_traces(marker=dict(size=10))
    return fig

def complete_stations_map(stations: pd.DataFrame):
  fig = arrondissements_map()
  fig_stations = stations_map(stations)
  for trace in fig_stations.data:
      fig.add_trace(trace)
  return fig

stations = metro_dataframe()
stations = stations[((stations['mode'] == 'RER') & (stations['route_long_name'] == "A")) | ((stations['mode'] == 'Métro') & (stations['route_long_name'] == "1"))]
fig = complete_stations_map(stations)
fig.write_html(r"./paris_map.html")
