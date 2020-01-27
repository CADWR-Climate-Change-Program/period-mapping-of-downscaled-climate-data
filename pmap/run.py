# -*- coding: utf-8 -*-
"""
@author1: Wyatt Arnold (wyatt.arnold@water.ca.gov)
@author2: ajperez
"""

import os
import numpy as np
import pandas as pd
from pmap import utils, ensemble

def period_tandp(data_dir,lat_longs,periods,endidx,ei_months=None):
    """
    Compute monthly and annual precipitation and temperature.
    Compute period averages of annual total precipitation and mean temperature.

    :param data_dir: (path) directory containing GCM data downloaded from gdo-dcp.ucllnl.org
        and extracted and must be organized by [model name]/[scenario]/[variable]
    :param basin_ll: (list) list of [latitude, longitude] pairs
        must be in N,W format (no negatives)
    :param periods: (list) list with the historical and future period
        i.e. [[1971,2000],[2070,2099]]

    :returns: (dictionaries) pr_mon
    """
    #--Scenarios--
    scenarios = ['historical','rcp45', 'rcp85']
    #--Variables--
    variables = ['pr', 'tasmax', 'tasmin']
    #--Models---
    models = sorted(os.listdir(data_dir))

    #---Period time index
    idxs = {'hist_a':utils.period_index(periods[0],'A'),
                 'fut_a':utils.period_index(periods[1],'A'),
                  'hist_m':utils.period_index(periods[0],'M'),
                  'fut_m':utils.period_index(periods[1],'M')}

    #---Extract daily t&p from annual netcdf files into model.scenario dfs---
    [pr_mon,tas_mon,pr_havg,tas_havg,pr_favg,tas_favg] = utils.extract_model_data(
        models,scenarios,variables,data_dir,lat_longs,periods,endidx,ei_months)

    #---Prepare dataframes for period differences---
    pr_havg = pd.DataFrame(pr_havg).T
    pr_favg = pd.DataFrame(pr_favg).T
    pr_favg_diff = pr_favg.copy()
    tas_havg = pd.DataFrame(tas_havg).T
    tas_favg = pd.DataFrame(tas_favg).T
    tas_favg_diff = tas_favg.copy()

    #--Take period differences---
    for i in range(0,len(pr_havg.index)):

        #--precip (percent difference)--
        pr_diff = pr_favg.iloc[i*2:i*2+2].sub(
            pr_havg.iloc[i]).divide(
            pr_havg.iloc[i]).multiply(100)
        pr_favg_diff.iloc[i*2:i*2+2] = pr_diff

        #--tas (absolute difference)--
        tas_diff = tas_favg.iloc[i*2:i*2+2].sub(tas_havg.iloc[i])
        tas_favg_diff.iloc[i*2:i*2+2] = tas_diff

    return pr_mon,tas_mon,pr_havg,pr_favg,pr_favg_diff,tas_havg,tas_favg,tas_favg_diff

def txpx_qmon(txpx_nn,quadrants,pr_mon,tas_mon,periods):

    #---Master dict of quantile-maps by quadrant---
    txpx_qmonth = {}

    #---Dictionary of months for qmapping
    months = {'jan':1,'feb':2,'mar':3,'apr':4,
              'may':5,'jun':6,'jul':7,'aug':8,
             'sep':9,'oct':10,'nov':11,'dec':12}

    #---Percentiles---
    prange = np.arange(1,100)

    #---Loop over quadrants and develop quantiles---
    for q in quadrants:
        #---Quadrant name (for workbook output)---
        txpx_name = 'T{}P{}_NN'.format(q[0],q[1]) if not q=='CT' else 'CT'

        #---Load quadrant sheet---
        txpx = txpx_nn[txpx_name]

        #---Get list of latlongs to process per quadrant---
        latlon = txpx.columns.values.tolist()

        #---Get model-scenario names in quadrant---
        m_s = list(np.char.array(txpx.iloc[:,0].dropna().values, unicode=True))

        #---Generate model-historical names in quadrant---
        m_h = [x.split('_')[0]+'_historical' for x in m_s]

        #---Percentile calculation per grid cell for models in qudrant---
        for mon in months:
            #---Monthly period index (for subsetting months)
            hist_idx_mon = pd.date_range(start='{}/1/{}'.format(months[mon],periods[0][0]),
                                         periods=30,freq=pd.offsets.MonthEnd(12))
            fut_idx_mon = pd.date_range(start='{}/1/{}'.format(months[mon],periods[1][0]),
                                         periods=30,freq=pd.offsets.MonthEnd(12))

            #---Dataframes to hold grid-based percentiles
            txpx_pr_factor = pd.DataFrame(index=prange,columns=latlon)
            txpx_tas_delta = pd.DataFrame(index=prange,columns=latlon)
            txpx_pr_hist_p = pd.DataFrame(index=prange,columns=latlon)
            txpx_pr_fut_p = pd.DataFrame(index=prange,columns=latlon)
            txpx_tas_hist_p = pd.DataFrame(index=prange,columns=latlon)
            txpx_tas_fut_p = pd.DataFrame(index=prange,columns=latlon)

            for ll in latlon:
                #---Dataframe per grid: columns = model-scenario, rows = months---
                pr_fut,tas_fut = pd.DataFrame(),pd.DataFrame()
                pr_hist,tas_hist = pd.DataFrame(),pd.DataFrame()

                for m in m_s:
                    pr_fut[m] = pr_mon[m].loc[fut_idx_mon,ll]
                    tas_fut[m] = tas_mon[m].loc[fut_idx_mon,ll]

                for m in m_h:
                    pr_hist[m] = pr_mon[m].loc[hist_idx_mon,ll]
                    tas_hist[m] = tas_mon[m].loc[hist_idx_mon,ll]

                #---Calculate percentiles---
                #---Precip---
                pr_hist_p,pr_fut_p,pr_factor = ensemble.percentile_change(
                    pr_hist,pr_fut,prange,'pr',0.1)
                txpx_pr_factor.loc[:,ll] = pr_factor
                txpx_pr_hist_p.loc[:,ll] = pr_hist_p
                txpx_pr_fut_p.loc[:,ll] = pr_fut_p

                #---Temp----
                tas_hist_p,tas_fut_p,tas_delta = ensemble.percentile_change(
                    tas_hist,tas_fut,prange,'tas',None)
                txpx_tas_delta.loc[:,ll] = tas_delta
                txpx_tas_hist_p.loc[:,ll] = tas_hist_p
                txpx_tas_fut_p.loc[:,ll] = tas_fut_p

            #---Populate TXPX dictionary---
            txpx_qmonth[txpx_name+'_'+mon+'_pr_factor'] = txpx_pr_factor
            txpx_qmonth[txpx_name+'_'+mon+'_pr_hist_p'] = txpx_pr_hist_p
            txpx_qmonth[txpx_name+'_'+mon+'_pr_fut_p'] = txpx_pr_fut_p
            txpx_qmonth[txpx_name+'_'+mon+'_tas_delta'] = txpx_tas_delta
            txpx_qmonth[txpx_name+'_'+mon+'_tas_hist_p'] = txpx_tas_hist_p
            txpx_qmonth[txpx_name+'_'+mon+'_tas_fut_p'] = txpx_tas_fut_p

    return txpx_qmonth
