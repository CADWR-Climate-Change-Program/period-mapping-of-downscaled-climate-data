# -*- coding: utf-8 -*-
"""
@author1: Wyatt Arnold (wyatt.arnold@water.ca.gov)
@author2: ajperez
"""

import os
import numpy as np
import pandas as pd
import xarray as xr

def extract_daily_nc(file,var,lat_longs,endidx):

    #---Read Data from nc file---
    ds = xr.open_dataset(file)
    # print(file)

    #---Create time index---
    time_index = pd.date_range(start='1/1/'+file[endidx-4:endidx], end='12/31/'+file[endidx-4:endidx],freq='D')
    # df = pd.DataFrame(index=time_index)

    #---Data to dataframe---
    ds = ds.to_dataframe().reset_index()
    if 'WGS84_EPSG_4326' in ds.columns:
        ds = ds.drop(['WGS84_EPSG_4326','lat_bnds','lon_bnds','time_bnds','bnds'], 1)
    ds = ds.set_index('time',drop=True)
    ds['latlon'] = ds['lat'].astype(str) + '_' + (ds['lon']-360).astype(str)
    ds_ll = ds.loc[ds.latlon.isin(lat_longs)]
    ds_ll = ds_ll.pivot(columns='latlon', values=var)
    ds_ll.set_index(time_index,drop=True)

    # #---Latlon loop---
    # for ll in lat_longs:
    #     # print(ll)
    #     #---Raise error if lat lon is not in netcdf file
    #     if ds.loc[((ds['lat'] == ll[0]) & (ds['lon'] == ll[1])),var].empty:
    #         raise Exception(str(ll) + ' is not contained netcdf file')
    #     #---Set grid column to values from netcdf
    #     df[str(ll[0])+'_'+str(ll[1]-360)] = ds.loc[((ds['lat'] == ll[0]) &
    #                                                 (ds['lon'] == ll[1])),var].values[:len(time_index)]

    #---Convert units---
    if var == 'pr':
        #---From (kg m^-2 s^-1) to (mm/day)---
        #---(kg m-2 s-1) * (1 m^3 / 1000 kg) * (1000 mm/m) * (3600 s/hr) * (24hr/day) ---
        ds_ll = ds_ll.iloc[:] * (3600 * 24)

    elif var == 'tasmax' or var == 'tasmin':
        #---From Kelvin to celcius---
        ds_ll = ds_ll.iloc[:] - 273.15

    return ds_ll

def extract_model_data(models,scenarios,variables,data_dir,lat_longs,period_idxs,endidx,ei_months):

    #---Initiate output dictionaries---
    pr_sum_m,pr_sum_a,tas_avg_m,tas_avg_a = {},{},{},{}
    pr_hist,pr_fut,tas_hist,tas_fut = {},{},{},{}

    for m in models: # model loop
        # print(m, end=" ")
        for s in scenarios: # scenario loop
            #---model.scenario key---
            m_name = m + '_' + s
            # print(m_name, end=" ")
            #---period idx marker---
            period = 'hist' if s=='historical' else 'fut'
            #---empty dataframes for collecting variables---
            df_pr,df_tmin,df_tmax = pd.DataFrame(),pd.DataFrame(),pd.DataFrame()
            for v in variables: # variable loop
                print(m_name + '_' + v, end=" ")
                vpath = os.path.join(data_dir,m,s,v)
                # print(vpath, end=" ")
                #---year start and end to filter nc files---
                y_start = period_idxs[0][0] if period == 'hist' else period_idxs[1][0]
                y_end = period_idxs[0][1] if period == 'hist' else period_idxs[1][1]

                #---filter nc files---
                ncfiles = sorted([x for x in os.listdir(vpath) if x.endswith('nc')])
                ncfiles = sorted([x for x in ncfiles if ((int(x[endidx-4:endidx]) >= y_start) &
                                                         (int(x[endidx-4:endidx]) <= y_end))])
                #---loop through nc files and load daily downscaled data---
                for f in ncfiles:
                    df = extract_daily_nc(os.path.join(vpath,f),v,lat_longs,endidx)
                    if v == 'pr':
                        df_pr = pd.concat([df_pr,df])
                    elif v == 'tasmin':
                        df_tmin = pd.concat([df_tmin,df])
                    elif v == 'tasmax':
                        df_tmax = pd.concat([df_tmax,df])

            #---Average daily temp---
            df_tas = df_tmin.add(df_tmax).divide(2)

            #---T & P metric monthly---
            pr_sum_m[m_name] = df_pr.resample('M').sum()
            tas_avg_m[m_name] = df_tas.resample('M').mean()

            #---if period metric is computed on specific subset of months:---
            if not ei_months==None:
                df_pr = df_pr.loc[df_pr.index.month.isin(ei_months)].copy()
                df_tas = df_tas.loc[df_tas.index.month.isin(ei_months)].copy()

            #---T & P metric annual---
            pr_sum_a[m_name] = df_pr.resample('A').sum()
            tas_avg_a[m_name] = df_tas.resample('A').mean()

            #---Period averages---
            if s=='historical':
                pr_hist[m_name] = pr_sum_a[m_name].mean()
                tas_hist[m_name] = tas_avg_a[m_name].mean()
            else:
                pr_fut[m_name] = pr_sum_a[m_name].mean()
                tas_fut[m_name] = tas_avg_a[m_name].mean()

    return pr_sum_m,tas_avg_m,pr_hist,tas_hist,pr_fut,tas_fut

def save_df_dict_to_excel(df_dict, name, path):

    if not os.path.exists(path):
        os.makedirs(path)
    writer = pd.ExcelWriter(os.path.join(path,name+'.xlsx'), engine='xlsxwriter')
    for i in df_dict:
        # Write each dataframe to a different worksheet
        df_dict[i].to_excel(writer, sheet_name=i)
    writer.save()

def get_latlon(csv):

    ll = pd.read_csv(csv)
    # ll['Long'] = 360 + ll['Long'] # convert lon west to east
    ll = list(ll.Lat + '_' +ll.long)
    # ll = np.array(ll).tolist()

    return ll

def period_index(period,freq):

    start = '12/31/' if freq =='A' else '1/1/'

    time_index = pd.date_range(start=start + str(period[0]),
                               end='12/31/'+str(period[1]), freq=freq)

    return time_index
