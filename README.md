# Real Estate Investment Opportunity Finder - Simple Explanation #

## Step 1: Get all residential buildings and their addresses in Switzerland.(from geo.zh.ch) and filer only buildings from the Zurich canton ##
Initially:<br /> 3,263,310 buildings found throughout all Switzerland<br /><br />
Result:<br /> 385,700 buildings found only in Zurich.

## Step 2: Filter only building types that are partly_residential and residential. ##
Reason:<br />
1.​ Top Tier (Highest Demand & Potential): <coide>partly_residential</code>, residential<br />
2.​ Higher Risk / Avoid for this Strategy: non_residential, other_residential, special, temporary<br /><br />
Results:<br /> 213,955 buildings in Zurich are residential and partly_residental buildings.<br />

## Step 3: Fetch all “bauzonen” data from the public registry and enrich the current data with it. (from maps.zh.ch API requests) ##
Comments:<br /> A solution was found using an alternative API endpoint, and the process
was sped up using multithreading “workers” running in parallel through different VPN locations.

## Step 4: Remove all addresses that don’t have the “bauzonen” information. ##
Results:<br /> 58,760 buildings with public “bauzonen” information in the final document.

## Step 5: Filter buildings that contain only the relevant “bazonen”. ##
Wohnzonen X Vollgeschosse:<br /> Primary residential zones, ideal for investment. Allow
renovations, expansions (up to specified stories), and density increases if quotas met. High
potential for profit via redevelopment.<br /><br />
Wohnzonen mit Gewerbeerleichterung X Vollgeschosse:<br /> Mixed
residential-commercial, suitable for versatile investments. Residential predominant, with
commercial additions possible for added value.<br /><br />
Kernzonen:<br /> Mixed-use preservation zones, permitting residential alongside other uses.
Redevelopment ok if character preserved; good for historic properties with upscale potential.<br /><br />
Zentrumszonen:<br /> Dense mixed zones (residential + commerce/services). Excellent for
redevelopment in urban centers, with opportunities for higher-value conversions.<br /><br />
Results:<br /> The dataset has been updated to contain only 48,344 buildings in ZH that fit
the criteria.<br /><br />

## Step 6: Filter out all addresses that have an apartment format (e.g. Weidlistrasse 6a). ##
Reason:<br /> We do this because this address format refers to apartment buildings, and
searching the government GIS system for these addresses returns a blank result with no useful
information. The real information is stored in addresses that refer to a building, and typically
have only a number (without a letter) next to the street name (e.g. Weidlistrasse 6).<br /><br />
Results:<br /> The dataset has been updated to contain only 41,478 buildings in ZH that fit
our criteria so far.<br />

## Step 7: Enrich the new dataset with more relevant data like year of construction of the building, building area [m2], number of floors, number of apartments. ##
Comments:<br /> Using this APi endpoint MapServer/find, we search the layer
(ch.bfs.gebaeude_wohnungs_register) using the given dataset’s EGID identification number.
This enriches the data with the correct info like year, size, number of floors and apartments.
What is great is this helps us further narrow our dataset. For example, if an entry does not return
the building year, it means that the given address is not a building.<br /><br />
Results:<br /> The dataset has been updated.<br />

## Step 8: Remove all entries that don’t have a building name. ##
Results:<br /> The dataset has been updated to contain only 40,886 buildings in ZH that fit
the criteria.

## Step 9: Take the fully enriched dataset and filter + score the best investment opportunities. ##
Results:<br /> Two new files are created with the final results.<br /> The file named “final_results”
contains 440 investment opportunities with a score of 1-10, including buildings only scoring 6
and above.<br /><br /> The file named “50-best-investment-options” contains the top 50 buildings that
scored the highest in our criteria.<br /><br /><br /><br /><br /><br />

# Conclusion and final thoughts #
​
After downloading the original government dataset with 3,263,310 building addresses,
we have run the data through rigorous filtering and criteria to find the best investment
opportunities. The final result is only 440 buildings, with a list of top 50 opportunities.<br />
​<br />
The scoring was done based on criteria like: allowed vs. existing floors, building age,
optimal size (500–1000 m²), number of apartments, and location.<br />
​
## 1. Allowed vs. Existing Floors (Zoning Potential) ##
What it means:<br /> The script checks the building’s current number of floors against the
maximum allowed by the zoning (“bauzonen”). If the zoning allows more floors than currently
exist, it’s a strong indicator that the property can be expanded, increasing its value and resale
potential.<br /><br />
Scoring:<br /> The greater the difference, the higher the score. This is the most heavily
weighted factor, as adding floors is a direct way to increase property value.<br />

## 2. Building Age ##
What it means:<br /> Older buildings (especially those built before 1985, and even more so
before 1950) are often prime candidates for redevelopment. They may be outdated,
undervalued, or eligible for renovation incentives. Very old buildings can be modernized, often
resulting in significant profit.<br /><br />
Scoring:<br /> Buildings constructed before 1985 get a substantial score boost, with even
higher scores for those built before 1950. The older the building, the higher the score.<br />

## 3. Building Size (Area) ##
What it means:<br /> The script favors buildings with an area between 500 and 1000 m². This
size range is considered optimal for redevelopment: large enough to allow substantial
improvements, but not so large as to be unmanageable or require excessive capital.<br /><br />
Scoring:<br /> Buildings in the optimal size range receive the highest score for this criterion.
Slightly smaller or larger buildings get a moderate boost, while those outside these ranges get a
minimal score.<br />

## 4. Number of Apartments ##
What it means:<br /> More apartments mean more units to sell or rent after redevelopment,
increasing potential profit. However, buildings with very few apartments may be easier to
redevelop (fewer tenants to relocate).<br /><br />
Scoring:<br /> Many apartments (8 or more) get a higher score, several apartments (4–7) get
a moderate score, and few apartments (1–3) get a small score plus a bonus for ease of
redevelopment.<br />

## 5. Location (ZIP Code) ##
What it means:<br /> Properties in prime locations, such as Zurich city (ZIP codes
8000–8099), are in higher demand and have greater resale value.<br /><br />
Scoring:<br /> Buildings in these ZIP codes receive a location bonus.6. Ease of Redevelopment
What it means: Buildings with very few apartments are easier to redevelop, as there are
fewer tenants to manage or relocate.<br /><br />
Bonus scoring:<br /> A small bonus is added for buildings with 2 or fewer apartments.<br />
