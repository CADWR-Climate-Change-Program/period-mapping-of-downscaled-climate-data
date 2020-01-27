# -*- coding: utf-8 -*-
"""
@author1: Wyatt Arnold (wyatt.arnold@water.ca.gov)
@author2: ajperez
"""

import os, sys
import numpy as np
import pandas as pd
import pmap

# Run Config
#---Future and historical period for analysis---
periods = [[1971,2000],[2058,2087]]
#---Months to compute statistic over---
ei_months = None # if isolating metric to month(s): e.g. [12,1]
#---Quandrants [T,P] or 'CT'---
quadrants_for_model_percentiles = ['CT', [0,0], [10,10], [10,90], [90,10], [90,90], [100,100]]
quadrants_for_scenario_output = ['CT', [0,0], [100,100]] # (can be a subset of quadrants_for_model_percentiles)
# #---Basin--
basin = 'CA-All-GCMs' # 'CA-All-GCMs' or basin-specfic 'DPR_I'
#---Path to GCM Files---
loca = r'../LOCA_GCM'
#---Path to Livneh Gridded Text Files---
livneh = r'../VIC/VIC_Forcing/Forcing_noclimatechange'
#---Path to Workbook Directory---
workbooks = r'./processed/workbooks'
#---Path to perturbed daily gridded output---
scenario_output = r'../VIC/VIC_Forcing'
#---Shapefiles of basins (points)---
geom_cabinet = r'./data/geom_cabinet'
#---Lat Long index range to proces---
ll_start_idx = 0
ll_end_idx = 2000

#---Save Directory---
datadir = os.path.join(loca,basin)
#--Models---
models = [model for model in os.listdir(datadir) if os.path.isdir(os.path.join(datadir,model))]
print(models)

#---Workbook Naming---
if basin != 'CA-All-GCMs':
    wrkbk_name_models = basin+'-TXPX-Models'
    wrkbk_name_percentiles = basin+'-TXPX-Monthly-Percentiles'
else:
    wrkbk_name_models = basin+'-TXPX-Models-{}-to-{}'.format(ll_start_idx,ll_end_idx)
    wrkbk_name_percentiles = basin+'-TXPX-Monthly-Percentiles-{}-to-{}'.format(ll_start_idx,ll_end_idx)


#--Lat Long list--
if basin != 'CA-All-GCMs':
    #---Basin latitude-longitude locations---
    liv_ll_list = pmap.utils.get_latlon(os.path.join(geom_cabinet,basin+'-latlon.csv'))
    print('processing latlongs: ',basin,liv_ll_list[0:1],' to ',liv_ll_list[-2:-1])
    ncFile_year_character_idx = -7
else:
    #--Livneh Grid List
    liv = sorted(os.listdir(livneh))
    liv_ll = []
    for name in liv:
        if name.startswith("data"):
            liv_ll.append(name)
    liv_ll = pd.DataFrame(liv_ll)[0].str.split('_',expand=True)
    liv_ll.drop([0],axis=1,inplace=True)
    liv_ll.columns = ['lat','long']
    liv_ll_list = list(liv_ll.lat + '_' +liv_ll.long)[ll_start_idx:ll_end_idx]
    print('processing latlongs: ',basin,liv_ll_list[0:1],' to ',liv_ll_list[-2:-1])
    ncFile_year_character_idx = -34


# Step 1 - Period Quadrants
#------------------------------#
# Load Data -> Summarize to Annual and Period Averages
[pr_mon,tas_mon,prhist,prfut,prdiff,tashist,tasfut,tasdiff] = pmap.run.period_tandp(
    datadir,
    liv_ll_list,
    periods,
    ncFile_year_character_idx,
    ei_months
)

# Calculate Quadrant Nearest Neighbors and Central Tendency
TXPX = pmap.ensemble.txpx_neighbors(
    prdiff,
    tasdiff,
    quadrants_for_model_percentiles
)

# Save out to workbook
pmap.utils.save_df_dict_to_excel(
    TXPX,
    wrkbk_name_models,
    workbooks
)


#  Step 2 - Adjustment Factors
#------------------------------#
# Calculate Percentiles and Adjustment Factors for Monthly Precip and Temp
TXPX_Percentiles = pmap.txpx_qmon(
    TXPX,
    quadrants_for_model_percentiles,
    pr_mon,tas_mon,periods
)

# Save out to workbook
pmap.utils.save_df_dict_to_excel(
    TXPX_Percentiles,
    wrkbk_name_percentiles,
    workbooks
)


# Step 3 - Perturb Historical
#------------------------------#
months = {'jan':1,'feb':2,'mar':3,
         'apr':4,'may':5,'jun':6,
          'jul':7,'aug':8,'sep':9,
         'oct':10,'nov':11,'dec':12}

dates = pmap.utils.period_index([1915,2011],freq="D")

for q in quadrants_for_scenario_output:

    txpx_name = 'T{}P{}_NN'.format(q[0],q[1]) if not q=='CT' else 'CT'

    for ll in liv_ll_list:

        #---Load livneh data for grid point---
        l = pd.read_table(
            os.path.join(livneh,'data_{}'.format(ll)),
            header=None,sep='\s+',names=['pr','tmax','tmin','wind'])
        l.set_index(dates,inplace=True)

        #---Calc livneh daily Tavg---
        l['tas'] = (l.tmax+l.tmin)/2
        l['y'] = l.index.year

        #---Upsample livneh to monthly---
        lmtas = l.loc[:,'tas'].resample('M').mean()
        lmpr = l.loc[:,'pr'].resample('M').sum()
        lp = l.copy()

        for v in ['pr','tas']:

            for m in months:

                qmv = txpx_name+'_'+m+'_'+v
                perturbtype = '_factor' if v=='pr' else '_delta'

                hist_p = TXPX_Percentiles[qmv+'_hist_p'].loc[:,ll]
                change_p = TXPX_Percentiles[qmv+perturbtype].loc[:,ll]

                obs = lmpr.loc[lmpr.index.month==months[m]] if v=='pr' else lmtas.loc[lmtas.index.month==months[m]]

                p_idx = np.searchsorted(hist_p,obs,'right')
                p_idx = np.where(p_idx==0,p_idx+1,p_idx)

                obs_perturb = change_p.loc[p_idx]
                obs_perturb.index = np.arange(1915,2012)
                obs_perturb = obs_perturb.to_dict()

                if v=='pr':
                    lp.loc[lp.index.month==months[m],'pr'] *= lp.y.map(obs_perturb)

                elif v=='tas':
                    lp.loc[lp.index.month==months[m],'tmax'] += lp.y.map(obs_perturb)
                    lp.loc[lp.index.month==months[m],'tmin'] += lp.y.map(obs_perturb)

        lp.drop(['tas','y'],inplace=True,axis=1)
        lp = lp.round(4)

        pathout = os.path.join(scenario_output,txpx_name)
        if not os.path.exists(pathout): os.makedirs(pathout)

        np.savetxt(os.path.join(pathout,'data_'+ll),lp.to_numpy(), fmt='%22.5f')
