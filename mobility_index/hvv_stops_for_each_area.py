# For enlarging the stat. areas to get all close public transport stops

import geopandas as gpd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd


file_path_statistische_gebiete = 'data/Hamburg_Statistik_Gebiete/statistische_gebiete_json/app_statistische_gebiete_EPSG_4326.json'
file_path_wohngebiet = 'data/Hamburg_Wohnflaeche/landuse_wohngebiet.geojson'

def load_statistische_gebiete(file_path):
    gdf = gpd.read_file(file_path)
    return gdf

def load_landuse_wohnflaeche(file_path):
    gdf = gpd.read_file(file_path)
    return gdf

def plot_statistische_gebiete(gdf, path, titel ='Statistische Gebiete von Hamburg'):
    fig, ax = plt.subplots(figsize=(15, 15))
    gdf.plot(ax=ax)
    plt.title(titel)
    # Show the plot
    plt.savefig(path)
    plt.show()

def remove_given_statistische_gebiete(gdf):
    '''
    :param gdf: geo map of Hamburg
    :return: Removes the island of Neuwerk and the area of people working on the sea
    '''
    seefahrt = '106001'
    neuwerk = '105001'
    gdf = gdf[~((gdf['statgebiet'] == seefahrt) | (gdf['statgebiet'] == neuwerk))]
    return gdf

def remove_outside_part_of_stat_gebiet_73002(gdf):
    '''
    There is a stat. area of Hamburg which has a small part over the boardr of Schleswig Holstein
    :param gdf:
    :return: Removes this small part from the stat area 73002
    '''
    statgebiet_to_remove = '73002'
    indices_to_remove = gdf[gdf['statgebiet'] == statgebiet_to_remove].index[1:]
    gdf = gdf.drop(indices_to_remove)
    return gdf


def enlarge_gebiet(stat_gebiet):
    buffer_distance = .003  # Adjust as needed
    enlarged_district = stat_gebiet.copy()
    enlarged_district['geometry'] = enlarged_district['geometry'].buffer(buffer_distance)
    #visualize_the_buffer(stat_gebiet,enlarged_district)
    return enlarged_district

def visualize_the_buffer(stat_gebiet,enlarged_district):
    # Plot the original and enlarged district for visual comparison
    ax = stat_gebiet.plot(color='blue', edgecolor='black')
    enlarged_district.plot(ax=ax, color='none', edgecolor='red', linestyle='dashed')
    # Show the plot
    ax.set_title("Original (Blue) and Enlarged (Red) Districts")
    ax.set_axis_off()
    plt.show()

def find_hvv_stationen(stat_gebiet):
    haltestellen = gpd.read_file('data/HVV/haltepunkte/Haltepunkte_2023.shp')
    haltestellen = haltestellen.to_crs(stat_gebiet.crs)
    haltestell_in_stat_gebiet = gpd.sjoin(haltestellen, stat_gebiet, op='within')

    return haltestell_in_stat_gebiet

def plot_haltestelle_on_enlarged_dist(stat_gebiet,haltestell_in_stat_gebiet, path):
    try:
        fig, ax = plt.subplots(figsize=(10, 10))
        stat_gebiet.plot(ax=ax, color='lightgray', edgecolor='black')
        haltestell_in_stat_gebiet.plot(ax=ax, color='red', markersize=50, label='Bus Stops in District')
        plt.title('Haltestellen in statistsichen Gebiet: 35018 Eimsbüttel')
        plt.legend()
        plt.savefig(path)
        plt.show()
    except:
        print('no haltestellen')

def calc_enlarged_gebiet(enlarged_gebiete):
    enlarged_gebiete = enlarged_gebiete.to_crs(epsg=32633)
    enlarged_gebiete['area'] = enlarged_gebiete.geometry.area

    district_areas = enlarged_gebiete.groupby('statgebiet')['area'].sum().reset_index()

    # Optionally, add this back to the original DataFrame if you need it for each row
    # This method adds the total district area to each row in the original GeoDataFrame
    enlarged_gebiete = enlarged_gebiete.merge(district_areas, on='statgebiet', suffixes=('', '_total'))

    # Step 3: Export your DataFrame with area calculations to a CSV (optional)
    enlarged_gebiete.to_csv('enlarged_areas_with_areas.csv', index=False)

    # Optionally, just save the district areas
    district_areas.to_csv('district_areas.csv', index=False)

def enlarge_stadtteil_add_hhv_haltestelle():
    stat_gebiete_2 = load_statistische_gebiete(file_path_statistische_gebiete)
    wohnflaeche = load_landuse_wohnflaeche(file_path_wohngebiet)
    stat_gebiete = remove_given_statistische_gebiete(wohnflaeche)
    stat_gebiete = remove_outside_part_of_stat_gebiet_73002(stat_gebiete)
    print(len(stat_gebiete))
    statgebiet_list = stat_gebiete['statgebiet'].unique().tolist()
    result_gdf = gpd.GeoDataFrame()
    haltestellen = gpd.GeoDataFrame()
    enlarged_gebiet_gdf = gpd.GeoDataFrame()
    statgebiet_list2 = ['35018']
    for statgebiet in statgebiet_list2:
        haltestelle_in_stat_gebiet_2 = find_hvv_stationen(stat_gebiete_2[stat_gebiete_2.statgebiet == statgebiet])
        if statgebiet == '35018':
            plot_haltestelle_on_enlarged_dist(stat_gebiete_2[stat_gebiete_2.statgebiet == statgebiet],
                                              haltestelle_in_stat_gebiet_2,
                                              'plots_for_report/komplettes_gebiet_haltestellen_35018.jpg')

        haltestelle_in_stat_gebiet = find_hvv_stationen(stat_gebiete[stat_gebiete.statgebiet == statgebiet])
        if statgebiet == '35018':
            plot_haltestelle_on_enlarged_dist(stat_gebiete[stat_gebiete.statgebiet == statgebiet], haltestelle_in_stat_gebiet, 'no_enlarged_gebiet_haltestellen_35018.jpg')
        enlarge_gebiete = enlarge_gebiet(stat_gebiete[stat_gebiete.statgebiet == statgebiet])
        haltestelle_in_stat_gebiet = find_hvv_stationen(enlarge_gebiete)
        if statgebiet == '35018':
            plot_haltestelle_on_enlarged_dist(enlarge_gebiete, haltestelle_in_stat_gebiet,
                                              'plots_for_report/enlarged_gebiet_haltestellen_35018.jpg')
            plot_haltestelle_on_enlarged_dist(stat_gebiete_2[stat_gebiete_2.statgebiet == statgebiet], haltestelle_in_stat_gebiet,
                                              'plots_for_report/more_haltestellen_gebiet_35018.jpg')
        enlarged_gebiet_gdf = gpd.GeoDataFrame(pd.concat([enlarged_gebiet_gdf,enlarge_gebiete], ignore_index=True))
        result_gdf = gpd.GeoDataFrame(pd.concat([result_gdf, enlarge_gebiete], ignore_index=True))
        haltestellen = gpd.GeoDataFrame(pd.concat([haltestellen, haltestelle_in_stat_gebiet], ignore_index=True))


    calc_enlarged_gebiet(enlarged_gebiet_gdf)
    haltestellen.to_file('data/haltestellen_enlarged_wohn_gebiete.geojson', driver='GeoJSON')
    result_gdf.to_file('data/enlarged_wohn_gebiete.geojson', driver='GeoJSON')