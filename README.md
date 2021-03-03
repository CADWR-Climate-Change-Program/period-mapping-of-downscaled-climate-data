# Enesemble-Informed Quantile Mapping of Monthly Temperature and Precipitation

The **pmap** package is for preparation of daily perturbed time-series of temperature and precipitation based on ensmebles of downscaled climate change projections. Quadrants of average annual temperature and precipitation change are computed over 30-year periods for each grid point. Quantile mapping is performed at the monthly scale to develop temperature (delta) and precipitation (factor) change factors. The monthly T-delta and P-factor are applied to a daily time series of historical gridded meteorology (Livneh).

# Contact
[Wyatt Arnold](mailto:wyatt.arnold@water.ca.gov)<br>
Engineer, Water Resources<br>
Climate Change Program<br>
California Department of Water Resources

# Scripts
## "loca-ei-qmap-T-P"
The script 'loca-ei-qmap-T-P.py' is configured to run **e**nsemble-**i**nformed **q**uantile **map**ing of **t**emperature and **p**recipitation for 64 members of the LOCA archive (32 GCM model realizations x2 RCPs 4.5 and 8.5 = 64 members).

### "loca-ei-qmap-T-P" Run Config
- `periods`
 	the guture and historical period for analysis 
    e.g. `[[1971,2000],[2058,2087]]`
- `ei_months`
    months to compute the average period change statistic over. Can be left as `None` or a list of months e.g. `[12,1]`
- `quadrants_for_model_percentiles`
    list of percentile combinations for model grouping, e.g. `['CT', [10,10], [10,90]]` to process the central tendency (CT), the 10th percentile  precip and temperature, and the 10th percentile temperature and 90th percentile precip combination.
- `quadrants_for_scenario_output`
    same as `quadrants_for_model_percentiles`, but can be a limited subset for final daily weather outputs
- `basin`
    this will either be `'CA-All-GCMs'` or a basin specific identifier in the `geom_cabinet` e.g. `'DPR_I'`
- `loca`
    this will either be `'CA-All-GCMs'` or a basin specific identifier in the `geom_cabinet` e.g. `'DPR_I'`
- `loca`
    Path to GCM Files
- `livneh`
    Path to Livneh Gridded Text File
- `workbooks`
    Path to processed workbooks directory
- `scenario_output`
    Path to perturbed daily gridded output
- `geom_cabinet`
    Path to shapefiles of basins (points)
- `ll_start_idx` and `ll_end_idx`
    A start and end index, e.g. `[0,2000]`, to run multiple scripts in parallel over certain subsets of the livneh grids.

---
**Package Requirements**
- xarray
- scipy
- netcdf4
- xlsxwriter

# Disclaimer
> All information provided by the Department of Water Resources is made available to provide immediate access for the convenience of interested persons. While the Department believes the information to be reliable, human or mechanical error remains a possibility. Therefore, the Department does not guarantee the accuracy, completeness, timeliness, or correct sequencing of the information. Neither the Department of Water Resources nor any of the sources of the information shall be responsible for any errors or omissions, or for the use or results obtained from the use of this information.
