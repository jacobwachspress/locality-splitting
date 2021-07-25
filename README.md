

```python
import pandas as pd
import metrics
```

## Calculating metrics of locality splitting in political districts ##

In order to calculate population-based splitting metrics, we need to know for every census block which district it is in. Much of this repository is devoted to generating this data in so-called "block equivalency files." Here is an example of such a data set.


```python
PA_block_eq_df = pd.read_csv('clean_data/PA/PA_classifications.csv')
PA_block_eq_df.head()
```

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>GEOID10</th>
      <th>pop</th>
      <th>sldl_2000</th>
      <th>cd_2013</th>
      <th>cd_2018</th>
      <th>sldu_2000</th>
      <th>sldl_2012</th>
      <th>sldl_2018</th>
      <th>cd_2003</th>
      <th>cd_2010</th>
      <th>sldu_2014</th>
      <th>sldl_2010</th>
      <th>sldl_2014</th>
      <th>sldu_2010</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>420350307003003</td>
      <td>57</td>
      <td>076</td>
      <td>5</td>
      <td>12</td>
      <td>34</td>
      <td>76</td>
      <td>76</td>
      <td>5</td>
      <td>5</td>
      <td>25</td>
      <td>76</td>
      <td>76</td>
      <td>35</td>
    </tr>
    <tr>
      <th>1</th>
      <td>420350302001056</td>
      <td>0</td>
      <td>076</td>
      <td>5</td>
      <td>12</td>
      <td>34</td>
      <td>76</td>
      <td>76</td>
      <td>5</td>
      <td>5</td>
      <td>25</td>
      <td>76</td>
      <td>76</td>
      <td>35</td>
    </tr>
    <tr>
      <th>2</th>
      <td>420350301001322</td>
      <td>0</td>
      <td>076</td>
      <td>5</td>
      <td>12</td>
      <td>34</td>
      <td>76</td>
      <td>76</td>
      <td>5</td>
      <td>5</td>
      <td>25</td>
      <td>76</td>
      <td>76</td>
      <td>35</td>
    </tr>
    <tr>
      <th>3</th>
      <td>420350301002207</td>
      <td>0</td>
      <td>076</td>
      <td>5</td>
      <td>12</td>
      <td>34</td>
      <td>76</td>
      <td>76</td>
      <td>5</td>
      <td>5</td>
      <td>25</td>
      <td>76</td>
      <td>76</td>
      <td>35</td>
    </tr>
    <tr>
      <th>4</th>
      <td>420350301001013</td>
      <td>0</td>
      <td>076</td>
      <td>5</td>
      <td>12</td>
      <td>34</td>
      <td>76</td>
      <td>76</td>
      <td>5</td>
      <td>5</td>
      <td>25</td>
      <td>76</td>
      <td>76</td>
      <td>35</td>
    </tr>
  </tbody>
</table>
</div>



This DataFrame has one column for every plan in the state since 2000 (cd = congressional district, sldu = state legislative district upper, sldl = state legislative district lower). If a year is missing, it means the district plan provided to the Census Bureau was identical to the previous year. 

Note that in many applications, generating the block equivalency files will not be necessary. For example, the Census Bureau published a national block equivalency file for congressional districts here https://www.census.gov/geographies/mapping-files/2019/dec/rdo/116-congressional-district-bef.html and state legislative districts here https://www.census.gov/geographies/mapping-files/2018/dec/rdo/2018-state-legislative-bef.html. Furthermore, states will often provide block equivalency files of proposed maps as part of the redistricting process. We wrote code for generating block equivalency files just so that we could score districting plans back to 2000.

In order to determine locality splitting, we also need a block equivalency file of the localities. When the localities are counties, this is easy to generate.


```python
df_county = pd.DataFrame(PA_block_eq_df['GEOID10'])
df_county['county_fips'] = df_county['GEOID10'].astype(str).apply(lambda x: x[2:5])
df_county.head()
```

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>GEOID10</th>
      <th>county_fips</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>420350307003003</td>
      <td>035</td>
    </tr>
    <tr>
      <th>1</th>
      <td>420350302001056</td>
      <td>035</td>
    </tr>
    <tr>
      <th>2</th>
      <td>420350301001322</td>
      <td>035</td>
    </tr>
    <tr>
      <th>3</th>
      <td>420350301002207</td>
      <td>035</td>
    </tr>
    <tr>
      <th>4</th>
      <td>420350301001013</td>
      <td>035</td>
    </tr>
  </tbody>
</table>
</div>



Once we merge up the block equivalency files, we can use a function from metrics.py to calculate a whole ensemble of locality splitting metrics for a plan. Remember that we need to have the populations of the census blocks in a column labeled "pop."


```python
input_df = pd.merge(PA_block_eq_df, df_county, on='GEOID10')
splitting_metrics = metrics.calculate_all_metrics(input_df, 'cd_2018', lclty_str='county_fips')
splitting_metrics
```



    {'plan': 'cd_2018',
     'splits_all': 13,
     'splits_pop': 13,
     'intersections_all': 17,
     'intersections_pop': 17,
     'split_pairs': 0.35155708843835665,
     'conditional_entropy': 0.4732218666363808,
     'sqrt_entropy': 1.2259489228698355,
     'effective_splits': 16.854108898754916,
     'split_pairs_sym': 0.8315438136166731,
     'conditional_entropy_sym': 1.9181791252873452,
     'sqrt_entropy_sym': 3.095251349839012,
     'effective_splits_sym': 1370.9984050936714}


