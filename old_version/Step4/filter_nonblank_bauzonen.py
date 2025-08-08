import pandas as pd

input_file = "residental-ZH-building-addresses-bauzonen.csv"
output_file = "enriched-zh-addresses-step1.csv"

df = pd.read_csv(input_file, sep=';')
filtered_df = df[df['bauzonen'].notna() & (df['bauzonen'].str.strip() != '')]
filtered_df.to_csv(output_file, index=False, sep=';')
