# -*- coding: utf-8 -*-
"""
@author1: Wyatt Arnold (wyatt.arnold@water.ca.gov)
@author2: ajperez
"""

import os
import numpy as np
import pandas as pd

def nearest_neighbors(df_pr_diff,df_tas_diff,TX,PX,neighbor_count):

    #---Initialize Nearest Neighbor Models Dataframe (per grid)---
    TXPX_NN_Models = pd.DataFrame(columns=df_pr_diff.columns)
    TXPX_Distances = df_pr_diff.copy()

    #---Percentile Index location for sorted values---
    x = np.arange(1,len(df_pr_diff.index)+1,1)
    pr_prcnt_loc = int(np.round(np.percentile(x, PX)))
    tas_prcnt_loc = int(np.round(np.percentile(x, TX)))

    #---Cycle through all grids---
    for i,grid in enumerate(df_pr_diff.columns):

        #---Extract Unique Grid Data for calculations---
        pr = df_pr_diff.iloc[:,i].values.astype(float)
        tas = df_tas_diff.iloc[:,i].values.astype(float)

        #---Sort array into ascending order---
        pr_sorted = np.sort(pr)
        tas_sorted = np.sort(tas)

        #---Identify Percentile value from sorted array and location---
        PX_val = pr_sorted[pr_prcnt_loc-1]
        TX_val = tas_sorted[tas_prcnt_loc-1]

        #---Take Normalized Differences---
        pr_PX_norm_diff = (pr - PX_val)/(np.sum(np.abs(pr - PX_val)))
        tas_TX_norm_diff = (tas - TX_val)/(np.sum(np.abs(tas - TX_val)))

        #---Compute Distance---
        distance = np.sqrt(np.square(pr_PX_norm_diff) + np.square(tas_TX_norm_diff))
        distances = distance.round(3)
        TXPX_Distances.iloc[:,i] = distances

        #---Ranking---
        distance_sort = distance.argsort()
        rank = np.empty_like(distance_sort)
        rank[distance_sort] = np.arange(len(distance))+1

        #---Extract Nearest Neighbor Models---
        ind = (rank <= neighbor_count)
        TXPX_NN_Models.iloc[:,i] = df_pr_diff.index.values[ind]

    return TXPX_NN_Models, TXPX_Distances

def central_tendency(df_pr_diff,df_tas_diff):

    df_pr = df_pr_diff.copy()
    df_tas = df_tas_diff.copy()

    #---Percentile Index location for sorted values---
    x = np.arange(1,len(df_pr.index.values)+1,1)
    Prcnt25_loc = int(np.round(np.percentile(x, 25)))
    Prcnt75_loc = int(np.round(np.percentile(x, 75)))

    #---Initialize DF collectors---
    ct = pd.DataFrame(columns=df_pr.columns)

    #---Cycle through all grids---
    for idx,grid in enumerate(df_pr_diff.columns):

        #---Extract Unique Grid Data for calculations---
        pr = df_pr.iloc[:,idx].values
        tas = df_tas.iloc[:,idx].values

        Model_Out_Array = np.empty(len(pr))
        Model_Out_Array[:] = np.nan

        #---Sort Temp array into ascending order---
        pr_Sorted = np.sort(pr)
        tas_Sorted = np.sort(tas)

        #---Identify Percentile value from sorted array and location---
        P25_Value = pr_Sorted[Prcnt25_loc-1]
        P75_Value = pr_Sorted[Prcnt75_loc-1]
        T25_Value = tas_Sorted[Prcnt25_loc-1]
        T75_Value = tas_Sorted[Prcnt75_loc-1]

        ind_1 = [pr>=P25_Value,pr<=P75_Value]
        ind_2 = [tas>=T25_Value, tas<=T75_Value]

        ind_Pr = np.empty(0)
        ind_Tas = np.empty(0)
        ind_Central = np.empty(0)

        for j in range(len(ind_1[1])):
            if ind_1[0][j] == 1 and ind_1[1][j] == 1:
                ind_Pr = np.append(ind_Pr, True)
            else:
                ind_Pr = np.append(ind_Pr, False)

            if ind_2[0][j] == 1 and ind_2[1][j] == 1:
                ind_Tas = np.append(ind_Tas, True)
            else:
                ind_Tas = np.append(ind_Tas, False)

            if ind_Pr[j] == 1 and ind_Tas[j] == 1:
                ind_Central = np.append(ind_Central, True)
            else:
                ind_Central = np.append(ind_Central, False)

        #---Extract Nearest Neighbors---
        ct[grid] = pd.Series(df_pr.index.values[ind_Central==True])

    return ct

def txpx_neighbors(pr_diff,tas_diff,quadrants):

    TXPX = {}

    #---Copy in differences---
    TXPX['pr_diff'] = pr_diff.copy()
    TXPX['tas_diff'] = tas_diff.copy()

    #---Compute quadrant models (per grid)---
    for q in quadrants:
        if 'CT' not in q:
            [TXPX['T{}P{}_NN'.format(q[0],q[1])],
             TXPX['T{}P{}_Distances'.format(q[0],q[1])]]  = nearest_neighbors(
                pr_diff,tas_diff, q[0],q[1],10)
        else:
            TXPX['CT'] = central_tendency(pr_diff, tas_diff)

    return TXPX

def percentile_change(df_hist,df_fut,p_range,var,min_threshold):

    p_hist = np.percentile(df_hist,p_range)
    p_fut = np.percentile(df_fut,p_range)

    if var=='pr':
        min_mask = np.logical_and(p_hist>min_threshold,p_fut>min_threshold)
        p_change = np.divide(p_fut,p_hist,where=min_mask)
        p_change = np.where(min_mask,p_change,1)
    elif var=='tas':
        p_change = p_fut-p_hist

    return p_hist,p_fut,p_change

