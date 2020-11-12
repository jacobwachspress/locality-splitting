import geopandas as gpd

df = gpd.read_file('clean_data/CA/CA_county_2000.shp')
df_sldu = gpd.read_file('clean_data/CA/CA_sldu_2013.shp')

county = df.loc[df['COUNTYFP00'] == '003', 'geometry'].iloc[0]
district = df_sldu.loc[df_sldu['SLDUST'] == '001', 'geometry'].iloc[0]
print(district.contains(county))
print(district.intersection(county).area)
print(county.area)
print(district.intersection(county).area / county.area)
