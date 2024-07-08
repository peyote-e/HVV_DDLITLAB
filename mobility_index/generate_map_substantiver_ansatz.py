# Creates the map of Hamburg which represents where people live and removes all other areas ( Parks, farms,...)

import geopandas as gpd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import MultiPolygon
from shapely.ops import transform
from pyproj import Proj, Transformer

file_path_statistische_gebiete = 'Data/Hamburg_Statistik_Gebiete/statistische_gebiete_json/app_statistische_gebiete_EPSG_4326.json'
file_path_wohngebiet = 'Data/Hamburg_Wohnflaeche/landuse_wohngebiet.geojson'
new_data_set = []
source_crs = 'EPSG:4326'
target_crs = 'EPSG:32632'

# Create a Transformer object for repeated transformations
transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)


def project_and_calculate_area(multi_polygon):
    # Project the MultiPolygon
    projected_multi_poly = transform(lambda x, y: transformer.transform(x, y), multi_polygon)

    # Calculate and return the area (in square meters)
    return projected_multi_poly.area

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

def remove_water(hamburg_map):
    '''
    :param hamburg_map:
    :return: A map of Hamburg without the waterspaces
    '''
    water = gpd.read_file('Data/Hamburg_Wohnflaeche/hamburg-latest-free/gis_osm_water_a_free_1.shp')
    water = water.to_crs(epsg=4326)
    water = gpd.overlay(water, hamburg_map, how='intersection')
    hamburg_map_without_water = gpd.overlay(hamburg_map, water, how='symmetric_difference', keep_geom_type=False)
    return hamburg_map_without_water


def load_landuse_fleachen_zum_entfernen(hamburg_map):
    '''
    :param hamburg_map: Geo data of Hamburg
    :return: A map of the parts of Hamburg where people are not living
    '''

    landuse = hamburg_map
    #plot_statistische_gebiete(landuse, 'landuse.jpg')

    industrial = landuse[landuse.fclass == 'industrial']
    quarry = landuse[landuse.fclass == 'quarry']
    vineyard = landuse[landuse.fclass == 'vineyard']
    military = landuse[landuse.fclass == 'military']
    nature_reserve = landuse[landuse.fclass == 'nature_reserve']
    farmyard = landuse[landuse.fclass == 'farmyard']
    orchard = landuse[landuse.fclass == 'orchard']
    forest = landuse[landuse.fclass == 'forest']
    meadow = landuse[landuse.fclass == 'meadow']
    #scrub = landuse[landuse.fclass == 'scrub']
    park = landuse[landuse.fclass == 'park']

    landuse_nicht_wohngebiet = pd.concat(([park,industrial,quarry,vineyard,military,nature_reserve,farmyard,orchard,forest,meadow]), axis=0)
    #landuse_nicht_wohngebiet.to_file('Data/Hamburg_Wohnflaeche/landuse_kein_wohngebiet.geojson', driver='GeoJSON')
    return landuse_nicht_wohngebiet


def clean_merged_data(merged_df):
    merged_df['statgebiet'] = merged_df.apply(
        lambda row: row['statgebiet_1'] if row['statgebiet_1'] == row['statgebiet_2'] else None, axis=1)

    merged_df['flaeche'] = merged_df.apply(
        lambda row: row['flaeche_1'] if row['flaeche_1'] == row['flaeche_2'] else None, axis=1)

    merged_df['id'] = merged_df.apply(lambda row: row['id_1'] if row['id_1'] == row['id_2'] else None, axis=1)

    merged_df = merged_df.drop(['statgebiet_1', 'statgebiet_2', 'flaeche_1', 'flaeche_2', 'id_1', 'id_2'], axis=1)

    merged_df = merged_df.dropna(subset=['statgebiet', 'flaeche', 'id'])

    return merged_df

def remove_landuse_form_stat_gebiet(stat_gebiet, landuse):
    merged_data = gpd.overlay(stat_gebiet, landuse, how='difference')
    merged_data.to_file('Data/merged_data.geojson', driver='GeoJSON')
    return merged_data

#
def get_size_of_residential_commercial_allotment_statistisches_gebiet():
    '''
     gets the new size of the area where people live
    :return: csv of areas and their size
    '''
    stat_gebiete = load_statistische_gebiete(file_path_statistische_gebiete)
    stat_gebiete = remove_given_statistische_gebiete(stat_gebiete)
    stat_gebiete = remove_outside_part_of_stat_gebiet_73002(stat_gebiete)
    landuse = gpd.read_file('Data/Hamburg_Wohnflaeche/hamburg-latest-free/gis_osm_landuse_a_free_1.shp')
    landuse = landuse.to_crs(epsg=4326)
    stat_gebiete = gpd.overlay(landuse, stat_gebiete, how='intersection')
    stat_gebiete = stat_gebiete.to_crs("EPSG:4326")
    merge_list1 = stat_gebiete['statgebiet'].unique().tolist()
    print(stat_gebiete.statgebiet.value_counts())
    landuse = load_landuse_fleachen_zum_entfernen(stat_gebiete)
    landuse = landuse.to_crs("EPSG:4326")
    #plot_statistische_gebiete(landuse, 'hamburg_landuse_removed.jpg', 'Hamburg Wohnfläche')

    stat_gebiete['geometry'] = stat_gebiete['geometry'].apply(lambda geom: geom if geom.is_valid else geom.buffer(0))
    landuse['geometry'] = landuse['geometry'].apply(lambda geom: geom if geom.is_valid else geom.buffer(0))

    stat_gebiete['geometry'] = stat_gebiete['geometry'].simplify(tolerance=0.001, preserve_topology=True)
    landuse['geometry'] = landuse['geometry'].simplify(tolerance=0.001, preserve_topology=True)

    stat_gebiete['geometry'] = stat_gebiete['geometry'].buffer(0.0001).buffer(-0.0001)
    landuse['geometry'] = landuse['geometry'].buffer(0.0001).buffer(-0.0001)

    subtracted_map = remove_landuse_form_stat_gebiet(stat_gebiete,landuse)

    #filtered_gdf = subtracted_map[subtracted_map['statgebiet'] == '43012']
    #plot_statistische_gebiete(subtracted_map, )

    merge_list = subtracted_map['statgebiet'].unique().tolist()
    unique_values_in_list1 = list(set(merge_list1) - set(merge_list))
    # Find values in list2 that are not in list1
    unique_values_in_list2 = list(set(merge_list) - set(merge_list1))
    print("Values in list1 not in list2:", unique_values_in_list1)
    print("Values in list2 not in list1:", unique_values_in_list2)

    areas = [project_and_calculate_area(mp) for mp in subtracted_map['geometry']]
    #enlarged_area = [enlarge_gebiet(stat) for stat in merge_list]
    subtracted_map['flaeche'] = areas
    grouped_data = subtracted_map.groupby('statgebiet')['flaeche'].sum().reset_index()
    for no_flaeche_value in unique_values_in_list1:
        no_flaeche_data = {'statgebiet': [no_flaeche_value],
                           'flaeche': [0]}

        new_df = pd.DataFrame(no_flaeche_data)

        # Append new_df to the original DataFrame
        grouped_data = grouped_data._append(new_df)

    grouped_data.to_csv('Data/Hamburg_Wohnflaeche/stat_gebiete_mit_flaeche.csv')
    #plot_statistische_gebiete(subtracted_map, 'hamburg_landuse_removed.jpg', 'Hamburg Wohnfläche')
    return grouped_data

