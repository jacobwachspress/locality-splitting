"""Interpolate District Boundaries onto other District Boundaries.

Creating a dataframe that matches a district boundary fips with other district
boundaries fips if they are fully contained. This will speed up the census
block interpolation districts because we can assign all blocks within the
subdistrict to the district minimizing the amount of individual geography
matchings required.
"""
import pandas as pd
import geopandas as gpd
import os
from download_census_data import state_fips
from county_district_interpolation import district_attribute
from county_district_interpolation import distribute_label
from county_district_interpolation import get_district_year


def main():
    """Interpolate district boundaries on census block data."""
    fips = state_fips()

    # Iterate over each state
    for state, fips_code in fips.items():
        # Get the base bath to the state folder
        base_path = 'clean_data/' + state + '/'

        # Get the relevant redistricting plans
        files = os.listdir(base_path)
        files = [x for x in files if x[-4:] == '.shp']
        sldl = [x for x in files if 'sldl' in x]
        sldu = [x for x in files if 'sldu' in x]
        cd = [x for x in files if 'cd' in x]

        # Sort and recombine so we interpolate in proper order
        sldl.sort()
        sldu.sort()
        cd.sort()
        files = sldl + sldu + cd

        # Initialize dataframe
        df = pd.DataFrame()

        # Iterate through all redistricting plans
        for ix, base_file in enumerate(files):
            # If we are on the last file do not interpolate
            if ix == len(files) - 1:
                break

            # Create list of other files we will interpolate
            interpolate_files = files[ix + 1:]

            # Load the base file
            df_base = gpd.read_file(base_path + base_file)

            # Define relevant column names
            base_district_year = get_district_year(base_file)
            base_id_col = district_attribute(base_district_year)

            # Create relevant base_cols
            df_base['base'] = base_district_year
            df_base['base_col'] = base_id_col
            df_base['base_value'] = df_base[base_id_col]

            # Set keep columns
            keep_cols = ['base', 'base_col', 'base_value']

            # Iterate through the interpolate files
            for inter_file in interpolate_files:
                # Load the interpolation district file
                df_inter = gpd.read_file(base_path + inter_file)

                # Define relevant column names
                inter_district_year = get_district_year(inter_file)
                inter_id_col = district_attribute(inter_district_year)

                # Print progress
                print(state, base_district_year, inter_district_year)

                # Add to keep columns
                keep_cols.append(inter_district_year)

                # Distribute label
                df_base = distribute_label(df_inter, [inter_id_col], df_base,
                                           [inter_district_year])

                # Check if district is fully contained, otherwise set to None
                for ix, row in df_base.iterrows():
                    base_district = row['geometry']
                    inter_district = df_inter.loc[df_inter[inter_id_col] ==
                                                  row[inter_district_year],
                                                  'geometry'].iloc[0]

                    # If interpolation district does not fully contain  the
                    # base district then we set its value to null
                    intersect = base_district.intersection(inter_district)
                    intersection_area = intersect.area
                    area_ratio = intersection_area / base_district.area
                    if area_ratio < 0.999:
                        df_base.at[ix, inter_district_year] = None

            # Reduce to relevant keep columns
            df_base = df_base[keep_cols]
            df = df.append(df_base)

        # Save dataframe
        df.to_csv(base_path + state + '_district_contains_district.csv',
                  index=False)
    return


if __name__ == "__main__":
    main()
