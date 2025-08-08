import pandas as pd

def filter_residential_buildings(input_csv, output_csv):
    # Read the Zurich building addresses CSV
    df = pd.read_csv(input_csv, sep=';')
    # Filter for residential and partly_residential buildings
    residential_types = ['residential', 'partly_residential']
    residential_df = df[df['BDG_CATEGORY'].isin(residential_types)]
    # Output to new CSV
    residential_df.to_csv(output_csv, index=False, sep=';')

if __name__ == "__main__":
    filter_residential_buildings(
        "Zurich_building addresses.csv",
        "residental-ZH-building-addresses.csv"
    )
