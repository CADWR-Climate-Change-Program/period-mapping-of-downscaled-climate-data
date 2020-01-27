#!/usr/bin/env python
# coding: utf-8

import os as os
from ftplib import FTP
import numpy as np
import pandas as pd
import netCDF4 as nc4
import itertools

# save data to:
pathout = r'./loca'

# get a list of models from ftp site
ftp = FTP('gdo-dcp.ucllnl.org')
ftp.login(user='', passwd = '')
wd_General = '/pub/dcp/archive/cmip5/loca/LOCA_2016-04-02/'
ftp.cwd(wd_General)
models = ftp.nlst()
print (models)

# param sets
# opendap url for future and historical LOCA
opendap = ['https://cida.usgs.gov/thredds/dodsC/loca_future',
           'https://cida.usgs.gov/thredds/dodsC/loca_historical']
# total time steps per future or historical
time_horizon = [34698,20454]
# three scenarios
scenarios = ['rcp45', 'rcp85','historical']
# only one realization is available by LOCA
realization = 'r1i1p1'
# precip, Tmax, and Tmin
variables = ['pr', 'tasmax', 'tasmin']
# basin to look up lat longs
basin = 'dpr'
ll = [[37.59375,-120.53125],[37.59375,-120.53125]]

# indexing for the loca opendap server
latRange = np.arange(23.40625,53.96875,0.0625)
lonRange = np.arange(-125.96875,-66.03125,0.0625)

for s in itertools.islice(scenarios,0,1):
    t = opendap_time_horizon[0] if s!='historical' else opendap_time_horizon[1]
    loca = nc4.Dataset(opendap[0],'r') if s!='historical' else nc4.Dataset(opendap[1],'r')
    for m in itertools.islice(models,0,32):
        modeloutpath = os.path.join(pathout,basin,s,m)
        if not os.path.exists(modeloutpath): os.makedirs(modeloutpath)
        for i in itertools.islice(ll,0,1):
            lat_idx = np.where(latRange==i[0])[0][0]
            lon_idx = np.where(lonRange==i[1])[0][0]
            e = []
            for v in itertools.islice(variables,0,3):
                print(basin,s,m,v,i)
                modelstring = v+'_'+m+'_'+realization+'_'+s
                data = loca.variables[modelstring][0:t,lat_idx:lat_idx+1,lon_idx:lon_idx+1]
                data = data.data.flatten()
                e.append(data)
            df = pd.DataFrame(e).T
            df.to_csv(os.path.join(modeloutpath,'data_'+str(i[0])+'_'+str(i[1])), sep='\t')

