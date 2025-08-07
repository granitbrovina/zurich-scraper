import pandas as pd
import re

INPUT_CSV = "enriched-zh-addresses-step1.csv"
OUTPUT_CSV = "enriched-zh-part2.CSV"

# Patterns for allowed zones
patterns = [
    r"Wohnzonen \d+ Vollgeschosse",
    r"Wohnzonen mit Gewerbeerleichterung \d+ Vollgeschosse",
    r"Kernzonen",
    r"Zentrumszonen"
]

# Compile regex for matching any allowed zone
zone_regex = re.compile(r"(" + r"|".join(patterns) + r")")

# Read CSV
# Column 18 is 'bauzonen' (index 17)
df = pd.read_csv(INPUT_CSV, sep=';')

# Function to check if all zones in entry are allowed


def contains_target_zone(zones):
    zone_list = [z.strip() for z in str(zones).split(',')]
    # Keep row if any zone matches one of the patterns
    return any(zone_regex.fullmatch(z) for z in zone_list)

filtered_df = df[df['bauzonen'].apply(contains_target_zone)]

filtered_df.to_csv(OUTPUT_CSV, index=False, sep=';')
print(f"Filtered CSV saved to {OUTPUT_CSV} with {len(filtered_df)} entries.")
