import pandas as pd
import requests
import time

ZH_WFS_URL = "https://maps.zh.ch/wfs/OGDZHWFS"  # OGD endpoint
WFS_LAYER = "ms:ogd-0156_arv_basis_np_gn_zonenflaeche_proj_f"  # Nutzungsplanung (Grundnutzung) projektiert

GEO_ADMIN_SEARCH_URL = "https://api3.geo.admin.ch/rest/services/api/SearchServer"


def geocode_address(address):
    """Geocode address to LV95 coordinates using geo.admin.ch"""
    params = {
        'type': 'locations',
        'searchText': address,
        'origins': 'address',
        'limit': 1
    }
    try:
        response = requests.get(GEO_ADMIN_SEARCH_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                attrs = data['results'][0].get('attrs', {})
                east_lv95 = attrs.get('x')
                north_lv95 = attrs.get('y')
                if east_lv95 and north_lv95:
                    return float(east_lv95), float(north_lv95)
    except Exception as e:
        print(f"Error geocoding address '{address}': {e}")
    return None, None

def get_bauzonen(easting, northing, debug=False, idx=None):
    """Query Zurich OGD WFS for Bauzonen info using LV95 coordinates."""
    buffer = 30  # Increased buffer for better matching
    bbox = f"{easting-buffer},{northing-buffer},{easting+buffer},{northing+buffer},EPSG:2056"
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typenames': WFS_LAYER,
        'outputformat': 'application/json; subtype=geojson',
        'bbox': bbox
    }
    try:
        response = requests.get(ZH_WFS_URL, params=params, timeout=15)
        if debug and idx is not None:
            # Print the full request URL for manual inspection
            print(f"[DEBUG] WFS request URL for row {idx}: {response.url}")
            print(f"[DEBUG] WFS status for row {idx}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            if debug and idx is not None:
                print(f"[DEBUG] Row {idx}: {len(features)} features returned")
                if features:
                    print(f"[DEBUG] Row {idx}: Feature property keys: {list(features[0].get('properties', {}).keys())}")
                    for i, feature in enumerate(features):
                        print(f"[DEBUG] Row {idx} Feature {i} properties: {feature.get('properties', {})}")
            if features:
                props = features[0].get('properties', {})
                # Parse Bauzonen info, support both old/new property names
                return props.get('zone_name', props.get('ZONENART_TXT', props.get('ZONENART', '')))
    except Exception as e:
        print(f"Error fetching Bauzonen for {easting},{northing}: {e}")
    return ''



import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def enrich_with_bauzonen(input_csv, output_csv, limit=None):
    df = pd.read_csv(input_csv, sep=';')
    if limit:
        df = df.head(limit)
    import random
    def process_row(idx, row):
        easting = row.get('ADR_EASTING')
        northing = row.get('ADR_NORTHING')
        debug = idx < 5  # Debug first 5 rows
        zone_types = set()
        if pd.notna(easting) and pd.notna(northing):
            buffer = 30
            bbox = f"{float(easting)-buffer},{float(northing)-buffer},{float(easting)+buffer},{float(northing)+buffer},EPSG:2056"
            params = {
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetFeature',
                'typenames': WFS_LAYER,
                'outputformat': 'application/json; subtype=geojson',
                'bbox': bbox
            }
            retries = 0
            while retries < 5:
                try:
                    response = requests.get(ZH_WFS_URL, params=params, timeout=15)
                    if debug:
                        print(f"[DEBUG] WFS request URL for row {idx}: {response.url}")
                        print(f"[DEBUG] WFS status for row {idx}: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        features = data.get('features', [])
                        if debug:
                            print(f"[DEBUG] Row {idx}: {len(features)} features returned")
                            if features:
                                print(f"[DEBUG] Row {idx}: Feature property keys: {list(features[0].get('properties', {}).keys())}")
                                for i, feature in enumerate(features):
                                    print(f"[DEBUG] Row {idx} Feature {i} properties: {feature.get('properties', {})}")
                        for feature in features:
                            props = feature.get("properties", {})
                            zone_type = props.get("typ_zh_bezeichnung")
                            if zone_type:
                                zone_types.add(zone_type)
                        break
                    elif response.status_code in (429, 500, 502, 503, 504):
                        wait = (2 ** retries) + random.uniform(0, 1)
                        print(f"[WARN] Row {idx}: HTTP {response.status_code}, backing off for {wait:.1f}s")
                        time.sleep(wait)
                        retries += 1
                    else:
                        print(f"[ERROR] Row {idx}: HTTP {response.status_code}")
                        break
                except Exception as e:
                    print(f"Error processing row {idx}: {e}")
                    wait = (2 ** retries) + random.uniform(0, 1)
                    time.sleep(wait)
                    retries += 1
        else:
            address = f"{row.get('STN_LABEL', '')} {row.get('ADR_NUMBER', '')}, {row.get('ZIP_LABEL', '')} {row.get('COM_NAME', '')}"
            east_lv95, north_lv95 = geocode_address(address)
            if east_lv95 and north_lv95:
                buffer = 30
                bbox = f"{east_lv95-buffer},{north_lv95-buffer},{east_lv95+buffer},{north_lv95+buffer},EPSG:2056"
                params = {
                    'service': 'WFS',
                    'version': '2.0.0',
                    'request': 'GetFeature',
                    'typenames': WFS_LAYER,
                    'outputformat': 'application/json; subtype=geojson',
                    'bbox': bbox
                }
                retries = 0
                while retries < 5:
                    try:
                        response = requests.get(ZH_WFS_URL, params=params, timeout=15)
                        if debug:
                            print(f"[DEBUG] WFS request URL for row {idx}: {response.url}")
                            print(f"[DEBUG] WFS status for row {idx}: {response.status_code}")
                        if response.status_code == 200:
                            data = response.json()
                            features = data.get('features', [])
                            if debug:
                                print(f"[DEBUG] Row {idx}: {len(features)} features returned")
                                if features:
                                    print(f"[DEBUG] Row {idx}: Feature property keys: {list(features[0].get('properties', {}).keys())}")
                                    for i, feature in enumerate(features):
                                        print(f"[DEBUG] Row {idx} Feature {i} properties: {feature.get('properties', {})}")
                            for feature in features:
                                props = feature.get("properties", {})
                                zone_type = props.get("typ_zh_bezeichnung")
                                if zone_type:
                                    zone_types.add(zone_type)
                            break
                        elif response.status_code in (429, 500, 502, 503, 504):
                            wait = (2 ** retries) + random.uniform(0, 1)
                            print(f"[WARN] Row {idx}: HTTP {response.status_code}, backing off for {wait:.1f}s")
                            time.sleep(wait)
                            retries += 1
                        else:
                            print(f"[ERROR] Row {idx}: HTTP {response.status_code}")
                            break
                    except Exception as e:
                        print(f"Error processing row {idx}: {e}")
                        wait = (2 ** retries) + random.uniform(0, 1)
                        time.sleep(wait)
                        retries += 1
        return ", ".join(zone_types) if zone_types else ""

    bauzonen_list = [None] * len(df)
    max_workers = 10  # Increased for faster enrichment
    print(f"Starting parallel enrichment with {max_workers} threads...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_row, idx, row): idx for idx, row in df.iterrows()}
        completed = 0
        total = len(df)
        for future in as_completed(futures):
            idx = futures[future]
            try:
                bauzonen_list[idx] = future.result()
            except Exception as e:
                print(f"Error in future for row {idx}: {e}")
            completed += 1
            if completed % 100 == 0:
                print(f"Progress: {completed}/{total} rows processed...")
    df['bauzonen'] = bauzonen_list
    df.to_csv(output_csv, index=False, sep=';')
    print(f"Enriched CSV saved to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Zurich residential buildings with Bauzonen info.")
    parser.add_argument('--test', action='store_true', help='Process only 50 buildings and output bauzonen-test.csv')
    args = parser.parse_args()
    if args.test:
        enrich_with_bauzonen(
            "residental-ZH-building-addresses.csv",
            "bauzonen-test.csv",
            limit=50
        )
    else:
        enrich_with_bauzonen(
            "residental-ZH-building-addresses.csv",
            "residental-ZH-building-addresses-bauzonen.csv"
        )
