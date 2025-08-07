import pandas as pd

input_file = "enriched-zh-part3-enriched.csv"
output_file = "fully-enriched-dataset.csv"

# Read the CSV
# Use the correct separator
# Remove rows where "Year of construction of the building" is blank or NaN

df = pd.read_csv(input_file, sep=";")
filtered_df = df[df["Year of construction of the building"].notna() & (df["Year of construction of the building"] != "")]
filtered_df.to_csv(output_file, sep=";", index=False)
print(f"Filtered dataset written to {output_file}")
