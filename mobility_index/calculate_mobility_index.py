# Calculates the mobility index for a stat. area based on number of times Bus and Train go a day, population of area
# and size of area
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import ast
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# load data (haltestellen/fläche)
def load_stat_gebiet_flaeche_haltestellen(file_path):
    df_fl_ht = pd.read_csv(file_path)
    return df_fl_ht

# load bevölkerungszahlen
def load_bevoelkerungs_data_for_stat_gebiet(file_path):
    df_bev = pd.read_excel(file_path)
    return df_bev

def load_fahrplan(file_path):
    return pd.read_csv(file_path)

def get_bevoelkerungs_anzahl(df, stat_gebiet):
    try:
        population = df.loc[df['Stat_gebiet'] == stat_gebiet, 'Einwohner'].values[0]
        return population
    except IndexError:
        print(f"District ID {stat_gebiet} not found.")
        return None
# adds population to data
def append_data_with_bev_zahl(df_fl_ht, df):
    df_fl_ht['bev_zahl'] = df_fl_ht['statgebiet'].apply(lambda x: get_bevoelkerungs_anzahl(df, int(x)))
    df_fl_ht['bev_zahl'] = pd.to_numeric(df_fl_ht['bev_zahl'], errors='coerce')
    # Replace NaN values with 0
    df_fl_ht['bev_zahl'] = df_fl_ht['bev_zahl'].fillna(0).astype(int)
    df_fl_ht = df_fl_ht[df_fl_ht['bev_zahl'] >= 1]
    df_fl_ht.to_csv('Data/stat_gebiet_flaeche_hvv_stops_bev_zahl_2.csv')

def calculate_bevoelkerungs_dichte_score(row):
    size_score = row['district_size']
    size_score = size_score/10000
    #busstops_score = row['num_bus_stops']
    #subway_score = row['num_subway_stops']
    population_score = row['bev_zahl']
    if population_score == 0 and size_score == 0.0:
        bev_dichte = 0
    elif size_score == 0.0:
        print(row)
    elif population_score == 0:
        bev_dichte = 0

    else:
        bev_dichte = population_score / size_score

    return bev_dichte

def calculate_hvv_angebot_dichte_bev_anzahl(row):
    bus_subway_anzahl_pro_tag = row['bus_subway_fahrplan_pro_tag']
    district_size = row['district_size']
    bev_dichte = row['bev_zahl']
    # hvv Angebots Dichte
    hvv_dichte = bus_subway_anzahl_pro_tag/(district_size/1000)

    # gesamt index
    index = hvv_dichte/bev_dichte
    return index



def calculate_bev_dichte_hvv_points_bev_anzahl(row):
    bev_dichte = row['bev_zahl']
    bus_subway_anzahl_pro_tag = row['bus_subway_fahrplan_pro_tag']
    try:
        public_transport_bev_dichte = bus_subway_anzahl_pro_tag/bev_dichte
    except:
        public_transport_bev_dichte = 0
    return public_transport_bev_dichte

def calculate_bev_dichte_hvv_points_bev_dichte_buckets(row):
    bev_dichte = row['bev_dichte_decile']

    bus_subway_anzahl_pro_tag = row['bus_subway_fahrplan_pro_tag']

    try:
        public_transport_bev_dichte = bus_subway_anzahl_pro_tag/bev_dichte
    except:
        public_transport_bev_dichte = 0
    return public_transport_bev_dichte

def calculate_bev_dichte_hvv_points_bev_dichte_absolut(row):
    bev_dichte = row['bevoelkerungs_dichte']

    bus_subway_anzahl_pro_tag = row['bus_subway_fahrplan_pro_tag']

    try:
        public_transport_bev_dichte = bus_subway_anzahl_pro_tag/bev_dichte
    except:
        public_transport_bev_dichte = 0
    return public_transport_bev_dichte
# returns the number of busses and trains in a area
def bus_subway_fahrplan_pro_tag_occ(row):
    bus_stop_fahrplan_count = []
    subway_stop_fahrplan_count = []
    bus_stop_names = row['bus_stop_names']
    bus_stop_list = ast.literal_eval(bus_stop_names)
    subway_stop_names = row['subway_stop_names']
    subway_stop_list = ast.literal_eval(subway_stop_names)
    for bus_stop in bus_stop_list:
        bus_stop_fahrplan_count.append(count_occ_in_fahrplan(bus_stop, df_fahrplan))
    for subway_stop in subway_stop_list:
        subway_stop_fahrplan_count.append(count_occ_in_fahrplan(subway_stop, df_fahrplan))
    bus_anzahl_pro_tag = sum(bus_stop_fahrplan_count)
    subway_anzahl_pro_tag = sum(subway_stop_fahrplan_count)
    bus_subway_anzahl_pro_tag = bus_anzahl_pro_tag + ( 2* subway_anzahl_pro_tag)
    return bus_subway_anzahl_pro_tag

def count_occ_in_fahrplan(hvv_stop, fahrplan):
    # soll die Fahrhäufigkeit anzeigen
    specific_station_count = fahrplan[fahrplan['Nach_NAME'] == hvv_stop].shape[0]
    return specific_station_count

def bucket_bev_anzahl():
    df['bev_dichte'] = df.apply(
        lambda row: row['bev_zahl'] / (row['district_size'] / 1000) if row['district_size'] > 0 else 0, axis=1)

    # Now, categorize 'bev_dichte' into deciles
    df['bev_dichte_decile'] = pd.qcut(df['bev_dichte'], 10,
                                      labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])  # labels=False will assign numbers 0-9 to each decile

    # Optionally, to see how the deciles are distributed
    print(df['bev_dichte_decile'].value_counts())

def calculate_quality_index():
    df['bevoelkerungs_dichte'] = df.apply(calculate_bevoelkerungs_dichte_score, axis=1)
    bucket_bev_anzahl()
    #min_value = df['bevoelkerungs_dichte'].min()
    #max_value = df['bevoelkerungs_dichte'].max()

    #df['bevoelkerungs_dichte_scaled'] = (df['bevoelkerungs_dichte'] - min_value) / (max_value - min_value)

    c = 1000

    df['bus_subway_fahrplan_pro_tag'] = df.apply(bus_subway_fahrplan_pro_tag_occ, axis=1)

    df['index_hvv_angebotbev_anzahl'] = df.apply(calculate_hvv_angebot_dichte_bev_anzahl, axis=1)
    df['log_index_hvv_angebotbev_anzahl'] = np.log1p(c * df['index_hvv_angebotbev_anzahl'])
    '''
    bin_edges = [0, 1 / 15, 2 / 15, 3 / 15, 4 / 15, 5 / 15, 6 / 15, 7 / 15, 8 / 15, 9 / 15, 10 / 15, 11 / 15, 12 / 15,
                 13 / 15, 14 / 15, 1, 10, 20, 40, 60, df['index_hvv_angebotbev_anzahl'].max() + 1]
    bin_labels = ['0-0.067', '0.067-0.133', '0.133-0.2', '0.2-0.267', '0.267-0.333', '0.333-0.4', '0.4-0.467',
                  '0.467-0.533', '0.533-0.6', '0.6-0.667', '0.667-0.733', '0.733-0.8', '0.8-0.867', '0.867-0.933',
                  '0.933-1', '1-10', '10-20', '20-40', '40-60', '60+']

    # Use cut to create bins
    df['index_hvv_angebotbev_anzahl_range'] = pd.cut(df['index_hvv_angebotbev_anzahl'], bins=bin_edges, labels=bin_labels, right=False)
    '''
    df['index_bev_anzahl'] = df.apply(calculate_bev_dichte_hvv_points_bev_anzahl, axis=1)
    df['log_index_bev_anzahl'] = np.log10(df['index_bev_anzahl'])

    df['index_bev_dichte_buckets'] = df.apply(calculate_bev_dichte_hvv_points_bev_dichte_buckets, axis=1)
    df['log_index_bev_dichte_buckets'] = np.log10(df['index_bev_dichte_buckets'])

    df['index_bev_dichte_absolut'] = df.apply(calculate_bev_dichte_hvv_points_bev_dichte_absolut, axis=1)
    df['log_index_bev_dichte_absolut'] = np.log10(df['index_bev_dichte_absolut'])

    #df.to_csv('Data/stat_gebiet_bevoelkerungsdichte.csv')
    df.to_csv('Data/stat_gebiet_flaeche_hvv_stops_bev_zahl_score2.csv')
#calculate_quality_index()

def subway_station_scatter(hamburg_boundary):
    haltestellen = gpd.read_file("Data/HVV/haltepunkte/Haltepunkte_2023.shp")
    haltestellen = haltestellen.to_crs(hamburg_boundary.crs)
    haltestellen = gpd.sjoin(haltestellen, hamburg_boundary, op='within')

    haltestellen['subway_stop'] = ~haltestellen['CODE'].isnull()
    ubahn_sbahn_haltestellen = haltestellen[haltestellen['subway_stop'] == True]


    return ubahn_sbahn_haltestellen


def visulize_scoring():
    gdf = gpd.read_file('Data/Hamburg_Statistik_Gebiete/statistische_gebiete_json/app_statistische_gebiete_EPSG_4326.json')
    scoring = pd.read_csv('Data/stat_gebiet_flaeche_hvv_stops_bev_zahl_score2.csv')
    #scoring = scoring[scoring['statgebiet'] != 96011]
    #scoring = scoring[scoring['statgebiet'] != 5003]
    #scoring = scoring[scoring['statgebiet'] != 3001]
    scoring = scoring[scoring['log_index_hvv_angebotbev_anzahl'] <=2.23]

    ubahn_sbahn_haltestellen = subway_station_scatter(gdf)

    #min_value = scoring['log_index'].min()
    #max_value = scoring['log_index'].max()

    #scoring['scaled_index'] = (scoring['log_index'] - min_value) / (max_value - min_value)

    gdf['statgebiet'] = gdf['statgebiet'].astype(int)
    df['statgebiet'] = df['statgebiet'].astype(int)

    merged_gdf = gdf.merge(scoring, on='statgebiet')

    values = merged_gdf['log_index_hvv_angebotbev_anzahl']
    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=10, color='skyblue', log=True)  # Using a logarithmic scale
    plt.title('Verteilung des Mobilitätsindex')
    plt.xlabel('Index Value')
    plt.ylabel('Frequency (log scale)')
    plt.grid(True)
    plt.savefig('plots_for_report/verteilung_index_unter_mean.jpg')
    plt.show()


    colors = ["blue", "green", "yellow", "orange", "red"]  # More emphasis on initial differences
    cmap = LinearSegmentedColormap.from_list("custom", colors, N=256)
    norm = plt.Normalize(vmin=merged_gdf['log_index_hvv_angebotbev_anzahl'].min(), vmax=merged_gdf['log_index_hvv_angebotbev_anzahl'].max())

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    merged_gdf.plot(column='log_index_hvv_angebotbev_anzahl', cmap=cmap, norm=norm, legend=True, ax=ax)
    ubahn_sbahn_haltestellen.plot(ax=ax, color='black', markersize=10)
    plt.title('Visualization of Log-Scaled Index with Emphasis on Small Differences')
    plt.savefig('plots_for_report/hamburg_hvv_dichte_bev_anzahl_score_hvv_gewichtet_unter_mean.jpg')
    plt.show()

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='log_index_hvv_angebotbev_anzahl', cmap=cmap, norm=norm, legend=True, ax=ax)
    plt.title('Bereiche bei dem der Mobilitäts Index unter dem Mittelwert liegt')
    plt.savefig('plots_for_report/hamburg_mobilitats_index_gewichtet_unter_mean.jpg')
    plt.show()


    '''
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='index_hvv_angebotbev_anzahl_range', cmap='viridis', legend=True, ax=ax, vmin=0, vmax=1)
    ubahn_sbahn_haltestellen.plot(ax=ax, color='red', markersize=10)
    plt.title('Hamburg District Scores with hvv angebot/ population and Underground points')
    plt.savefig('hamburg_hvv_dichte_bev_anzahl_score_mit_ubahn_points.jpg')
    plt.show()

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='index_hvv_angebotbev_anzahl_range', cmap='viridis', legend=True, ax=ax, vmin=0, vmax=1)
    plt.title('Hamburg District Scores with hvv angebot/ population  ')
    plt.savefig('hamburg_hvv_dichte_bev_anzahl_score.jpg')
    plt.show()

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='index_bev_anzahl', cmap='viridis', legend=True, ax=ax, vmin=0, vmax=1)
    ubahn_sbahn_haltestellen.plot(ax=ax, color='red', markersize=10)
    plt.title('Hamburg District Scores with population and Underground points(')
    plt.savefig('hamburg_district_scores_population_subway_points.jpg')
    plt.show()

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='log_index_bev_anzahl', cmap='viridis', legend=True, ax=ax, vmin=0, vmax=1)
    ubahn_sbahn_haltestellen.plot(ax=ax, color='red', markersize=10)
    plt.title('Hamburg District Scores with population and Underground points(log, Scaled)')
    plt.savefig('hamburg_district_scores_population_subway_points_log.jpg')
    plt.show()

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='log_index_bev_anzahl', cmap='viridis', legend=True, ax=ax, vmin=0, vmax=1)
    plt.title('Hamburg District Scores with population (log, Scaled)')
    plt.savefig('hamburg_district_scores_population_log.jpg')
    plt.show()


    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='index_bev_anzahl', cmap='viridis', legend=True, ax=ax, vmin=merged_gdf['index_bev_anzahl'].min(),
                    vmax=merged_gdf['index_bev_anzahl'].max())
    plt.title('Hamburg District Scores with population')
    plt.savefig('hamburg_district_scores_scaled_population.jpg')
    plt.show()


    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='log_index_bev_dichte_buckets', cmap='viridis', legend=True, ax=ax, vmin=0, vmax=1)
    plt.title('Hamburg District Scores with population density buckets (log scaled)')
    plt.savefig('hamburg_district_scores_population_densitiy_buckets_log_scaled.jpg')
    plt.show()


    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='index_bev_dichte_buckets',cmap='viridis', legend=True, ax=ax, vmin=merged_gdf['index_bev_dichte_buckets'].min(),
                    vmax=merged_gdf['index_bev_dichte_buckets'].max())
    plt.title('Hamburg District Scores with population density buckets')
    plt.savefig('hamburg_district_scores_population_densitiy_buckets.jpg')
    plt.show()


    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='log_index_bev_dichte_absolut', cmap='viridis', legend=True, ax=ax, vmin=0, vmax=1)
    plt.title('Hamburg District Scores with population density (log scaled)')
    plt.savefig('hamburg_district_scores_population_densitiy_log_sacled.jpg')
    plt.show()


    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged_gdf.plot(column='index_bev_dichte_absolut', cmap='viridis', legend=True, ax=ax, vmin=merged_gdf['index_bev_dichte_absolut'].min(),
                    vmax=merged_gdf['index_bev_dichte_absolut'].max())
    plt.title('Hamburg District Scores with population density')
    plt.savefig('hamburg_district_scores_population_densitiy.jpg')
    plt.show()




    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    # Plot using a colormap, with vmin and vmax to adjust color intensity
    # vmin and vmax set the range of values that will be colored
    merged_gdf.plot(column='log_index', cmap='viridis', legend=True, ax=ax, vmin=merged_gdf['log_index'].min(),
                    vmax=merged_gdf['log_index'].max())

    plt.title('District Scores')
    plt.show()
    plt.savefig('hamburg_district_scores.png')


    values = merged_gdf['index']
    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=20, color='skyblue', log=True)  # Using a logarithmic scale
    plt.title('Distribution of Index Values')
    plt.xlabel('Index Value')
    plt.ylabel('Frequency (log scale)')
    plt.grid(True)
    plt.show()
    plt.savefig('hamburg_scores_verteilung.png')
'''

def run_calculation_index():
    df = load_bevoelkerungs_data_for_stat_gebiet('Data/Stadtteildaten_Hamburg_filled_nan_correct.xlsx')
    df_fl_ht = load_stat_gebiet_flaeche_haltestellen('Data/stat_gebiet_flaeche_hvv_stops.csv')
    df_fahrplan = load_fahrplan('Data/Fahrplanfahrten_formatiert.csv')
    append_data_with_bev_zahl(df_fl_ht, df)

    # Calculate Qualitäts Index
    # fläche / ((Anzahl Haltestellen (gewichtet) * Fahrhäufigkeit)/Bevölkerungs dichte)
    df = pd.read_csv('Data/stat_gebiet_flaeche_hvv_stops_bev_zahl_2.csv')

    visulize_scoring()