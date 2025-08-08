
import pandas as pd
import requests
import time

API_FIND_URL = "https://api3.geo.admin.ch/rest/services/api/MapServer/find"
LAYER = "ch.bfs.gebaeude_wohnungs_register"
NEW_COLUMNS = [
    "Year of construction of the building",
    "Building area [m2]",
    "Number of floors",
    "Number of apartments"
]

def get_building_info_by_egid(egid):
    params = {
        "layer": LAYER,
        "searchText": str(egid),
        "searchField": "egid",
        "returnGeometry": "false",
        "contains": "false",
        "lang": "en",
        "sr": "2056"
    }
    try:
        r = requests.get(API_FIND_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        # Debug: print full API response for first 5 EGIDs
        if hasattr(get_building_info_by_egid, "debug_count"):
            get_building_info_by_egid.debug_count += 1
        else:
            get_building_info_by_egid.debug_count = 1
        if get_building_info_by_egid.debug_count <= 5:
            print(f"API response for EGID {egid}: {data}")
        for result in results:
            attrs = result.get("attributes", {})
            return {
                "Year of construction of the building": attrs.get("gbauj"),
                "Building area [m2]": attrs.get("garea"),
                "Number of floors": attrs.get("gastw"),
                "Number of apartments": attrs.get("ganzwhg")
            }
    except Exception as e:
        print(f"API error for EGID {egid}: {e}")
    return {col: None for col in NEW_COLUMNS}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enrich Zurich property data with building info from Swiss Federal API.")
    parser.add_argument("--test", action="store_true", help="Run in test mode (first 50 entries)")
    args = parser.parse_args()

    input_file = "enriched-zh-part3.csv"
    output_file = "enriched-zh-part3-enriched.csv"
    df = pd.read_csv(input_file, sep=";")
    egid_col = "BDG_EGID"
    if args.test:
        df = df.head(2000)
        print("Running in test mode: processing first 2000 entries.")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    egids = df[egid_col].tolist()
    enriched = [None] * len(egids)
    print(f"Starting parallel enrichment for {len(egids)} entries...")
    with ThreadPoolExecutor(max_workers=16) as executor:
        future_to_idx = {executor.submit(get_building_info_by_egid, egid): idx for idx, egid in enumerate(egids)}
        for i, future in enumerate(as_completed(future_to_idx)):
            idx = future_to_idx[future]
            try:
                enriched[idx] = future.result()
            except Exception as e:
                print(f"Error processing EGID at index {idx}: {e}")
            if (i+1) % 50 == 0 or (i+1) == len(egids):
                print(f"Processed {i+1}/{len(egids)}")
    for col in NEW_COLUMNS:
        df[col] = [x[col] for x in enriched]
    df.to_csv(output_file, sep=";", index=False)
    print(f"Enriched data written to {output_file}")

if __name__ == "__main__":
    main()
