from generate_map_substantiver_ansatz import get_size_of_residential_commercial_allotment_statistisches_gebiet
from hvv_stops_for_each_area import enlarge_stadtteil_add_hhv_haltestelle
from calculate_mobility_index import run_calculation_index


if __name__ == '__main__':
    get_size_of_residential_commercial_allotment_statistisches_gebiet()
    enlarge_stadtteil_add_hhv_haltestelle()
    run_calculation_index()