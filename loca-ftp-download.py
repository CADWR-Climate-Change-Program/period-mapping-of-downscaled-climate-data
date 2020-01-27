# -*- coding: utf-8 -*-
"""
@author1: Wyatt Arnold (wyatt.arnold@water.ca.gov)
@author2: ajperez
"""

import os
from ftplib import FTP
import numpy as np
import pandas as pd
import itertools
import ocgis
from ocgis import crs
import shapefile as shp

# save data to:
pathout = r'./data/loca'
pathshape = r'./data/geom_cabinet'

#Shapefile Directory, where to find shapefile=
ocgis.env.DIR_GEOMCABINET = pathshape
ocgis.env.DIR_DATA = './'
ocgis.env.OVERWRITE = True

def grab_file(filename):
    localfile = open(filename, 'wb')
    ftp.retrbinary('RETR ' + filename, localfile.write, 262144)
    localfile.close()

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
time_horizon = [34697,20453]
# three scenarios
scenarios = ['rcp45', 'rcp85','historical']
# precip, Tmax, and Tmin
variables = ['pr', 'tasmax', 'tasmin']
# basin to look up lat longs
basin = 'dpr'

# get a list of models from ftp site
ftp = FTP('gdo-dcp.ucllnl.org')
ftp.login(user='', passwd = '')
wd_General = '/pub/dcp/archive/cmip5/loca/LOCA_2016-04-02/'
ftp.cwd(wd_General)
for s in itertools.islice(scenarios,1,2):
    for m in itertools.islice(models,0,32):
        ftp.cwd(wd_General+m+'/16th/'+s)
        realization = ftp.nlst()[0]
        for v in itertools.islice(variables,0,3):
            print(basin,s,m,v)
            modeloutpath = os.path.join(pathout,basin,m,s,v)
            if not os.path.exists(modeloutpath): os.makedirs(modeloutpath)
            ocgis.env.DIR_OUTPUT = modeloutpath
            modelstring = v+'_'+m+'_'+realization+'_'+s
            ftp.cwd(wd_General+m+'/16th/'+s+'/'+realization+'/'+v+'/')
            ncfiles = ftp.nlst()
            ncfiles = [x for x in ncfiles if not x.endswith('ncP')]
            ncfiles_idx_end = len(ncfiles)-1 if s!='historical' else len(ncfiles)
            for f in itertools.islice(ncfiles,0,ncfiles_idx_end):
                grab_file(f)
                rd = ocgis.RequestDataset(f, variable=v, crs=crs.WGS84())
                basinbbox = list(shp.Reader(os.path(pathshape,"thuc12")).bbox)
                ops = ocgis.OcgOperations(dataset=rd,
                          geom =list(basinbbox),
                          add_auxiliary_files = False,
                          spatial_operation = 'intersects',
                          output_format='nc', prefix=basin+'_'+f[:-24])
                ret = ops.execute()
                os.remove(f)

