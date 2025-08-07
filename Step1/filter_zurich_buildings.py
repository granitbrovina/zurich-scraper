import pandas as pd

def filter_zurich_buildings(input_csv, output_csv):
    # Read the building addresses CSV
    df = pd.read_csv(input_csv, sep=';')
    # Filter for Zurich canton (COM_CANTON == 'ZH')
    zurich_df = df[df['COM_CANTON'] == 'ZH']
    # Output to new CSV
    zurich_df.to_csv(output_csv, index=False, sep=';')

if __name__ == "__main__":
    filter_zurich_buildings(
        "building_addresses.csv",
        "Zurich_building addresses.csv"
    )
