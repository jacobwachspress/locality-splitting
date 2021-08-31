


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
The required input is a pandas DataFrame with a row for each unit (usually census block or precinct) used to build the districts. The DataFrame must have a column denoting each unit's **population, district, and locality.** For U.S. Census provides a table with census blocks and their corresponding districts, called "block equivalency files." As a sample data set, we have downloaded this file for the Congressional districts used in 2018 and merged in the populations.

```python 
from locality_splitting import cd_2018
df = cd_2018.get_block_equivalency_file()

df.head(10)
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>GEOID</th>
      <th>pop</th>
      <th>cd_2018</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>010010201001000</td>
      <td>61</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001001</td>
      <td>0</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001002</td>
      <td>0</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001003</td>
      <td>75</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001004</td>
      <td>0</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001005</td>
      <td>1</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001006</td>
      <td>0</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001007</td>
      <td>23</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001008</td>
      <td>0</td>
      <td>2</td>
    </tr>
    <tr>
      <td>010010201001009</td>
      <td>1</td>
      <td>2</td>
    </tr>
  </tbody>
</table>
</div>

To calculate these metrics for county splitting, we need a column for the state and the county. Conveniently, the first two digits of the census block GEOID corresponds to the state FIPS code, and the next three digits correspond to the county FIPS code. State FIPS codes can be looked up [here](https://www.nrcs.usda.gov/wps/portal/nrcs/detail/?cid=nrcs143_013696).

```python 
df['state'] = df['GEOID'].str[:2]
df['county'] = df['GEOID'].str[2:5]
PA_df = df[df['state'] == '42']

PA_df.head(10)
```
<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>GEOID</th>
      <th>pop</th>
      <th>cd_2018</th>
      <th>state</th>
      <th>county</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>420010301011000</td>
      <td>6</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011001</td>
      <td>30</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011002</td>
      <td>15</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011003</td>
      <td>77</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011004</td>
      <td>27</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011005</td>
      <td>25</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011006</td>
      <td>12</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011007</td>
      <td>0</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011008</td>
      <td>4</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
    <tr>
      <td>420010301011009</td>
      <td>62</td>
      <td>13</td>
      <td>42</td>
      <td>001</td>
    </tr>
  </tbody>
</table>
</div>
Then if you write the following python code:

```python 
from locality_splitting import metrics

metrics.calculate_all_metrics(PA_df, 'cd_2018', lclty_col='county')
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
