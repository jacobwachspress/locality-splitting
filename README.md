


# Metrics of locality splitting in political districts
[![PyPI version](https://badge.fury.io/py/locality-splitting.svg)](https://badge.fury.io/py/locality-splitting)

## Description
This repository contains [Python code](metrics.py) that implements a number of metrics for quantifying locality (e.g. county, community of interest) splitting in districting plans. The metrics implemented are:
- Geography-based
	- Number of localities split
	- Number of locality-district intersections
- Population-based
	- Effective splits<sup>1</sup>
	- Conditional entropy<sup>2</sup>
	- Square root entropy<sup>3</sup>
	- Split pairs<sup>4</sup>

Options are provided to ignore zero-population regions and to calculate symmetric splitting scores.

A description of the metrics (with formulas) can be found in this [working paper](metrics_description_working_paper.pdf).

## Installation
If using pip, do `pip install locality-splitting`

## Example use
The required input is a pandas DataFrame with a row for each unit (usually census block or precinct) used to build the districts. The DataFrame must have a column denoting each unit's **population, district, and locality.** For U.S. Census provides a table with census blocks and their corresponding districts, called "block equivalency files." We have provided code to download block equivalency files from the U.S. Census website for the congressional and state legislative (upper and lower chamber) plans used in the 2012, 2014, 2016, and 2018 elections. 

```python 
from locality_splitting import block_equivalency_file as bef
year = 2018
plan_type = 'cd'
df = bef.get_block_equivalency_file(year, plan_type)

df.head(10)
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>BLOCKID</th>
      <th>cd_2018</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>011290440001080</td>
      <td>01</td>
    </tr>
    <tr>
      <th>1</th>
      <td>011290440001010</td>
      <td>01</td>
    </tr>
    <tr>
      <th>2</th>
      <td>011290440001092</td>
      <td>01</td>
    </tr>
    <tr>
      <th>3</th>
      <td>011290440001091</td>
      <td>01</td>
    </tr>
    <tr>
      <th>4</th>
      <td>011290440001090</td>
      <td>01</td>
    </tr>
    <tr>
      <th>5</th>
      <td>011290440001089</td>
      <td>01</td>
    </tr>
    <tr>
      <th>6</th>
      <td>011290440001088</td>
      <td>01</td>
    </tr>
    <tr>
      <th>7</th>
      <td>011290440001087</td>
      <td>01</td>
    </tr>
    <tr>
      <th>8</th>
      <td>011290440001086</td>
      <td>01</td>
    </tr>
    <tr>
      <th>9</th>
      <td>011290440001085</td>
      <td>01</td>
    </tr>
  </tbody>
</table>
</div>

Next we have to pick a state and merge in populations from the census API. We will use Pennsylvania as an example, which has FIPS code 42. State FIPS codes can be looked up [here](https://www.nrcs.usda.gov/wps/portal/nrcs/detail/?cid=nrcs143_013696).

```python
fips_code = '42'
df_pop = bef.merge_state_census_block_pops(fips_code, df)
df_pop.head(10)
```

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>BLOCKID</th>
      <th>pop</th>
      <th>cd_2018</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>420010301011000</td>
      <td>6</td>
      <td>13</td>
    </tr>
    <tr>
      <th>1</th>
      <td>420010301011001</td>
      <td>30</td>
      <td>13</td>
    </tr>
    <tr>
      <th>2</th>
      <td>420010301011002</td>
      <td>15</td>
      <td>13</td>
    </tr>
    <tr>
      <th>3</th>
      <td>420010301011003</td>
      <td>77</td>
      <td>13</td>
    </tr>
    <tr>
      <th>4</th>
      <td>420010301011004</td>
      <td>27</td>
      <td>13</td>
    </tr>
    <tr>
      <th>5</th>
      <td>420010301011005</td>
      <td>25</td>
      <td>13</td>
    </tr>
    <tr>
      <th>6</th>
      <td>420010301011006</td>
      <td>12</td>
      <td>13</td>
    </tr>
    <tr>
      <th>7</th>
      <td>420010301011007</td>
      <td>0</td>
      <td>13</td>
    </tr>
    <tr>
      <th>8</th>
      <td>420010301011008</td>
      <td>4</td>
      <td>13</td>
    </tr>
    <tr>
      <th>9</th>
      <td>420010301011009</td>
      <td>62</td>
      <td>13</td>
    </tr>
  </tbody>
</table>
</div>

To calculate these metrics for county splitting, we need a column for the county. Conveniently, the first two digits of the census BLOCKID correspond to the state FIPS code, and the next three digits correspond to the county FIPS code. 

```python
df_pop['county'] = df_pop['BLOCKID'].str[2:5]
df_pop.head(10)
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>BLOCKID</th>
      <th>pop</th>
      <th>cd_2018</th>
      <th>county</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>420010301011000</td>
      <td>6</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>1</th>
      <td>420010301011001</td>
      <td>30</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>2</th>
      <td>420010301011002</td>
      <td>15</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>3</th>
      <td>420010301011003</td>
      <td>77</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>4</th>
      <td>420010301011004</td>
      <td>27</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>5</th>
      <td>420010301011005</td>
      <td>25</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>6</th>
      <td>420010301011006</td>
      <td>12</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>7</th>
      <td>420010301011007</td>
      <td>0</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>8</th>
      <td>420010301011008</td>
      <td>4</td>
      <td>13</td>
      <td>001</td>
    </tr>
    <tr>
      <th>9</th>
      <td>420010301011009</td>
      <td>62</td>
      <td>13</td>
      <td>001</td>
    </tr>
  </tbody>
</table>
</div>

Then if you write the following python code:

```python 
from locality_splitting import metrics

metrics.calculate_all_metrics(df_pop, 'cd_2018', lclty_col='county')
```
you will get an output like this:
```python
{'plan': 'cd_2018',
 'splits_all': 14,
 'splits_pop': 13,
 'intersections_all': 85,
 'intersections_pop': 84,
 'effective_splits': 10.160339912460943,
 'conditional_entropy': 0.47256386411416673,
 'sqrt_entropy': 1.22572584704072,
 'split_pairs': 0.9590673198811142,
 'effective_splits_sym': 6.340218676778926,
 'conditional_entropy_sym': 0.9622343161303942,
 'sqrt_entropy_sym': 1.5503698835379718,
 'split_pairs_sym': 0.9784915514182326}
```
<div>
and can choose which metric(s) to use. The suffix "_all" means that zero-population regions are included, whereas "_pop" means they are ignored. (This distinction is only relevant for the geography-based metrics.) The suffix "_sym" indicates a symmetric splitting score.<sup>4</sup> 


## References
1. Samuel Wang, Sandra J. Chen, Richard Ober, Bernard Grofman, Kyle Barnes, and Jonathan Cervas. (2021). [Turning Communities Of Interest Into A Rigorous Standard For Fair Districting.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3828800) _Stanford Journal of Civil Rights and Civil Liberties, Forthcoming_.
2. Larry Guth, Ari Nieh, and Thomas Weighill. (2020). [Three Applications of Entropy to Gerrymandering.](https://arxiv.org/pdf/2010.14972.pdf) _arXiv_.
3. Moon Duchin. (2018). [Outlier analysis for Pennsylvania congressional redistricting.](https://www.governor.pa.gov/wp-content/uploads/2018/02/md-report.pdf)
4. Jacob Wachspress, Will Adler. (2021). [Metrics of locality splitting in political districts.](https://github.com/jacobwachspress/locality-splitting/blob/master/metrics_description_working_paper.pdf) _Working paper_.
