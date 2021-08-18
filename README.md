

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
The required input is a pandas DataFrame with a row for each unit (usually census block or precinct) used to build the districts. The DataFrame must have a column denoting each unit's **population, district, and locality.** Here is an example of the input format, using ten random census blocks from Pennsylvania. The U.S. Census 

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>GEOID10</th>
      <th>pop</th>
      <th>cd_2018</th>
      <th>county_fips</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>420659503002020</td>
      <td>39</td>
      <td>15</td>
      <td>065</td>
    </tr>
    <tr>
      <td>420430241021027</td>
      <td>24</td>
      <td>10</td>
      <td>043</td>
    </tr>
    <tr>
      <td>421010280001004</td>
      <td>216</td>
      <td>3</td>
      <td>101</td>
    </tr>
    <tr>
      <td>420710120013011</td>
      <td>58</td>
      <td>11</td>
      <td>071</td>
    </tr>
    <tr>
      <td>420034572004011</td>
      <td>20</td>
      <td>18</td>
      <td>003</td>
    </tr>
    <tr>
      <td>420171047021022</td>
      <td>56</td>
      <td>1</td>
      <td>017</td>
    </tr>
    <tr>
      <td>420130109002021</td>
      <td>25</td>
      <td>13</td>
      <td>013</td>
    </tr>
    <tr>
      <td>420430248005010</td>
      <td>42</td>
      <td>10</td>
      <td>043</td>
    </tr>
    <tr>
      <td>420210122003037</td>
      <td>51</td>
      <td>15</td>
      <td>021</td>
    </tr>
    <tr>
      <td>420792122003018</td>
      <td>15</td>
      <td>8</td>
      <td>079</td>
    </tr>
  </tbody>
</table>

If you read in this DataFrame as ``df`` and write the following python code:

```python 
from locality_splits import metrics

metrics.calculate_all_metrics(df, 'cd_2018', lclty_col='county_fips')
```

you will get an output like this:
```python
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
```
<div>
and can choose which metric(s) to use. The suffix "_all" means that zero-population regions are included, whereas "_pop" means they are ignored. (This distinction is only relevant for the geography-based metrics.) The suffix "_sym" indicates a symmetric splitting score.<sup>4</sup> 


## References
1. Samuel Wang, Sandra J. Chen, Richard Ober, Bernard Grofman, Kyle Barnes, and Jonathan Cervas. (2021). [Turning Communities Of Interest Into A Rigorous Standard For Fair Districting.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3828800) _Stanford Journal of Civil Rights and Civil Liberties, Forthcoming_.
2. Larry Guth, Ari Nieh, and Thomas Weighill. (2020). [Three Applications of Entropy to Gerrymandering.](https://arxiv.org/pdf/2010.14972.pdf) _arXiv_.
3. Moon Duchin. (2018). [Outlier analysis for Pennsylvania congressional redistricting.](https://www.governor.pa.gov/wp-content/uploads/2018/02/md-report.pdf)
4. Jacob Wachspress, Will Adler. (2021). [Metrics of locality splitting in political districts.](https://github.com/jacobwachspress/locality-splitting/blob/master/metrics_description_working_paper.pdf) _Working paper_.
