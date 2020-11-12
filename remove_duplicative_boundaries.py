"""Remove Duplicative Shapefiles.

We load redistricting plans for every year according to the census. However,
plans do not change every year. This prevents unnecessary processing downstream
in the pipeline.
"""
import os
import geopandas as gpd
from download_census_data import state_fips


def main():
    """Remove duplicative boundary shapefiles."""
    # Get list of state fips
    fips = state_fips()

    # Remove duplicative boundaries
    remove_duplicative_boundaries(fips, 'cd')
    remove_duplicative_boundaries(fips, 'county')
    remove_duplicative_boundaries(fips, 'sldl')
    remove_duplicative_boundaries(fips, 'sldu')
    return


def remove_duplicative_boundaries(fips, level):
    """Delete duplicative shapefiles

    Arguments:
        fips: dictionary of states and fips_codes

        level: level of boundaries we are removing duplicates for
            options are 'cd', 'county', 'sldl', and 'sldu'
    """
    # Display step
    print('REMOVING DUPLICATIVE BOUNDARIES:', level.upper(), '\n\n')

    # Iterate through all of the states
    for state, fips_code in fips.items():
        # Get all relevant shapefiles for this state and level
        direc = 'clean_data/' + state + '/'
        files = os.listdir(direc)
        files = [x for x in files if '_' + level + '_' in x]
        files = [x for x in files if '.shp' in x]

        # Sort list to make sure years are aligned
        files.sort()

        # Continue if nebraska lower chamber
        if state == 'NE' and level == 'sldl':
            continue

        # Get the file that we know is an original plan
        keep_geo = files[0]
        df_keep = gpd.read_file(direc + keep_geo)

        # Iterate through files until none are identical
        while files.index(keep_geo) < len(files) - 1:
            # Update the check plan (next element in list to the keep plan)
            keep_ix = files.index(keep_geo)
            check_geo = files[keep_ix + 1]
            df_check = gpd.read_file(direc + check_geo)

            # update status
            print(keep_geo, check_geo)

            # Check if plans are identical
            is_same = is_same_geo_file(df_keep, df_check)

            # if same plan delete the check plan
            if is_same:
                # Delete files
                delete_shapefile(direc + check_geo)

                # Delete file from list
                files.remove(check_geo)

            # if it is not the same plan then set the check to the keep
            else:
                keep_geo = check_geo
                df_keep = df_check
        print(files, '\n')
    return


def delete_shapefile(path):
    """Delete shapefile and all corresponding files."""
    # Get path without the extension
    path_no_ext = path[:-4]

    # Iterate through shapefile extensions
    exts = ['.cpg', '.dbf', '.prj', '.shp', '.shx']
    for ext in exts:
        os.remove(path_no_ext + ext)
    return


def left_geom_bound(geom):
    """Extract a geometries left bound."""
    return geom.bounds[0]


def is_same_geo_file(df1, df2, precision=0.01):
    """Check if two geographic files are the same.

    Arguments:
        df1: first geodataframe to check

        df2: second geodtaframe to check

        precision:
    """
    # If there are errors in intersections they are not the same file
    try:
        # Get geometries and sort accodring to their left most bound
        geos1 = df1.loc[:, 'geometry']
        geos1 = sorted(geos1, key=left_geom_bound)
        geos2 = df2.loc[:, 'geometry']
        geos2 = sorted(geos2, key=left_geom_bound)

        # If both only have one number of geometries its the state
        if len(geos1) == 1 and len(geos2) == 1:
            return True

        # If the don't have the same number of geometries they aren't the same
        if len(geos1) != len(geos2):
            return True

        # Get the intersections between each of the geometries
        r = range(len(geos1))
        inter = [geos1[i].intersection(geos2[i]).area for i in r]

        # Get amount of intersecting area for each plan
        inter1 = [inter[i] / geos1[i].area for i in r]
        inter2 = [inter[i] / geos2[i].area for i in r]

        # Return False if intersecting area is less than expected precision
        # for any geometry otherwise it is the same plan
        for i in inter1 + inter2:
            if abs(i - 1) > precision:
                return False
        return True
    except:
        return False


if __name__ == "__main__":
    main()
