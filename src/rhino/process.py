import pandas as pd
import numpy as np
import numba as nb
import itertools
import os
import time
from multiprocessing import Pool
from functools import partial


count = 0 
def bb_intersection_over_union(boxA, boxB):

    interArea = not np.any([np.greater(boxA[0],boxB[3]),np.greater( boxA[3],boxB[0]) #testing X
    ,np.greater(boxA[1],boxB[4]), np.greater(boxA[4],boxB[1]) #testing Y
    ,np.greater(boxA[2],boxB[5]), np.greater(boxA[5], boxB[2])]) # testing Z

    return interArea

def checkmesh(meshes, points):
    global count
    n = len(meshes)
    for b in range(n):
        bb = meshes[b]
        if  bb_intersection_over_union(points,bb):
            count = count + 1
            if count % 1000 == 0:
                print(count)
            return True 
    return False 


def checkmeshPool(pp):
    points, meshes = pp
    n = len(meshes.values)
    for b in range(n):
        bb = meshes.values[b]
        if not bb_intersection_over_union(points,bb):
            return (points[6], True )
    return (points[6], False )


def log(message):
    print('{},{}'.format(time.time(), message))

if __name__ == '__main__':
    log('start')
    #Reading all data csv
    pov_ = pd.read_csv("pov_.csv",header=None )
    pov_.columns = ["x","y","z" ]
    target_ = pd.read_csv("targets_.csv",header=None )
    target_.columns = ["x1","y1","z1" ]
    meshes_ = pd.read_csv("meshes_.csv",header=None, index_col=0  )
    meshes_.columns = ["xMax","yMax","zMax","xMin","yMin","zMin" ]

    log('import finish {}'.format(len(meshes_)))

    pov_['_tmpkey'] = 1
    target_['_tmpkey'] = 1

    lines = pd.merge(pov_, target_, on='_tmpkey').drop('_tmpkey', axis=1)
    lines.index = pd.MultiIndex.from_product((pov_.index, target_.index))

    pov_.drop('_tmpkey', axis=1, inplace=True)
    target_.drop('_tmpkey', axis=1, inplace=True)

    # print(res)
    lines = pd.DataFrame(lines, columns =['x','y','z','x1','y1','z1'] )
    log('finish creating lines dt')
    bbx = pd.DataFrame(columns = ["xMax","yMax","zMax","xMin","yMin","zMin",'order' ])
    bbx['xMax'] = lines[['x', 'x1']].values.max(1)
    bbx['yMax'] = lines[['y', 'y1']].values.max(1)
    bbx['zMax'] = lines[['z', 'z1']].values.max(1)
    bbx['xMin'] = lines[['x', 'x1']].values.min(1)
    bbx['yMin'] = lines[['y', 'y1']].values.min(1)
    bbx['zMin'] = lines[['z', 'z1']].values.min(1)
    bbx['order'] = bbx.index

    log('finish creating bbx dt {}'.format(len(bbx)))
    log('possible calculations {}'.format(len(bbx)* len(meshes_)))
    fun = partial(checkmesh, meshes_.values)
    bbx2 = bbx.head(1000000)
    bbx2['hit'] = bbx2.apply(lambda x: fun(x), axis=1)
    # p = Pool(10)
    # results = p.map(fun ,bbx.values )

    log('finish intersections {}'.format(len(bbx[bbx['hit'] == True])))

    bbx.to_csv("hits_.csv")

    log('finish writing')
    
    #TODO add index to bbx df to use it on checkmesh and return a tuple (index, bool) to relate with table
    