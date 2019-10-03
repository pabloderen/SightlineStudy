#!/usr/bin/env python
# coding: utf-8

# # Collision analysis
import pandas as pd
import numpy as np
import itertools
import numba
import os
import time
import multiprocessing as mp
from multiprocessing import Pool
from functools import partial
from numpy.lib import recfunctions as rfn

import os
os.environ["OMP_NUM_THREADS"] = "10"
os.environ["OPENBLAS_MAIN_FREE"] = "10"


# Loger for python console 

def log(message):
    print('{} , {}'.format(time.time(), message))


# ## Reading points of view

class BoundingBox():
    #Bounding box defined by tuple of max & min points
    def __init__(self, point):
        self.XMax = point[0]
        self.YMax = point[1]
        self.ZMax = point[2]
        self.XMin = point[3]
        self.YMin = point[4]
        self.ZMin = point[5]


def checkmesh(lines, meshes):
    #iterate over points
    aa = BoundingBox(meshes)
    for b in lines:
        bb = BoundingBox(b)
        if  bb_intersection_over_union(aa,bb):
            return True
    return False 

def bb_intersection_over_union(boxA, boxB):
    interArea =  ((boxA.XMax > boxB.XMin) 
                  and (boxB.XMax > boxA.XMin) 
                  and (boxA.YMax > boxB.YMin) 
                  and (boxA.YMin < boxB.YMax) 
                  and (boxA.ZMax > boxB.ZMin) 
                  and (boxA.ZMin < boxB.ZMax) )
    
    return interArea

@numba.jit(forceobj=True, parallel=True)
def FilterByBBX(Faces, line):
    maxX = max(line[3],line[0])
    maxY = max(line[4],line[1])
    maxZ = max(line[5],line[2])
    minX = min(line[3],line[0])
    minY = min(line[4],line[1])
    minZ = min(line[5],line[2])
    aa = np.where((Faces[:,0] > minX) & ( Faces[:,1] > minY) & (Faces[:,2] > minZ) & (Faces[:,3] < maxX) & (Faces[:,4] < maxY) & (Faces[:,5] < maxZ)   )
    return Faces[aa]

def checkFaces(Faces, line):
    #filter by boinding box intersection
    Faces = FilterByBBX(Faces, line)
    # sort by proximity to point to test occulsion
    f =np.delete(Faces, np.s_[3:6], axis=1) 
    idx = np.argsort(e_dist(f, np.array([line[0],line[1],line[2]])))
    for f in Faces[idx]:
        a = np.array(f,  dtype=np.float32)
        b = np.array(line,  dtype=np.float32)
        if intersection(a,b):
            return True
    return False

@numba.jit(['float32(float32,float32,float32)'], forceobj=True, parallel=True)
def tt(a,b,c):
    return (a - b) / c

@numba.jit(['float32(float32,float32,float32)'], forceobj=True, parallel=True)
def length(a,b,c):
    return (a**2 + b**2 + c**2)

@numba.jit(forceobj=True, parallel=True)
def normalC(ray):
    return [ray[3]-ray[0], ray[4]-ray[1],ray[5]-ray[2]]


@numba.jit(forceobj=True, parallel=True)
def intersection(aabb, ray):
    
    #Bounding box v line intersection detector
    normal = normalC(ray)
    #TODO : check divided by zero!
    t1 = tt(aabb[3],ray[0], normal[0])
    t2 = tt(aabb[0] , ray[0], normal[0])
    t3 = tt(aabb[4] , ray[1], normal[1])
    t4 = tt(aabb[1], ray[1], normal[1])
    t5 = tt(aabb[5],ray[2], normal[2])
    t6 = tt(aabb[2],ray[2], normal[2])
    
    tmax = min(max(t1, t2), max(t3, t4), max(t5, t6))

        # if tmax < 0, ray (line) is intersecting AABB, but whole AABB is behing us
    if (tmax < 0):
        return 0

        # if tmin > tmax, ray doesn't intersect AABB
    tmin = max(min(t1, t2), min(t3, t4), min(t5, t6))
    if (tmin > tmax):
        return 0
    t= None
    if (tmin < float(0)):
        t = tmax
    else:
        t = tmin
    if (t * t) > length(normal[0],normal[1],normal[2]):
        return 0
    return 1


@numba.jit(forceobj=True, parallel=True)
def e_dist(a, b):

    """Distance calculation for 1D, 2D and 3D points using einsum
    : a, b   - list, tuple, array in 1,2 or 3D form
    : metric - euclidean ('e','eu'...), sqeuclidean ('s','sq'...),
    :-----------------------------------------------------------------------
    """
    a = np.asarray(a)
    b = np.atleast_2d(b)
    a_dim = a.ndim
    b_dim = b.ndim
    if a_dim == 1:
        a = a.reshape(1, 1, a.shape[0])
    if a_dim >= 2:
        a = a.reshape(np.prod(a.shape[:-1]), 1, a.shape[-1])
    if b_dim > 2:
        b = b.reshape(np.prod(b.shape[:-1]), b.shape[-1])
    diff = a - b
    dist_arr = np.einsum('ijk,ijk->ij', diff, diff)
    
    dist_arr = np.sqrt(dist_arr)
    dist_arr = np.squeeze(dist_arr)
    return dist_arr



# Filter lines with positive intersections


if __name__ is  '__main__':
    start= time.time()
    pov_ = pd.read_csv(r".\pov_.csv",header=None )
    pov_.columns = ["x","y","z" ]
    print('{} Points of View'.format(len(pov_)))
    pov_.head(10)

    # ## Reading targets (points over meshes)

    target_ = pd.read_csv(r".\targets_.csv",header=None )
    target_.columns = ["x1","y1","z1" ]
    print('{} targets or points of interest'.format(len(target_)))
    target_.head()


    # ## Reading meshes bounding box
    meshes_ = pd.read_csv(r".\context_.csv",header=None, index_col=0  )
    meshes_.columns = ["xMax","yMax","zMax","xMin","yMin","zMin","id" ]
    print('{} meshes in context set'.format(len(meshes_)))
    meshes_.head()


    # ## Reading meshes faces
    mesh_faces = pd.read_csv(r".\mesh_faces.csv",header=None  )
    mesh_faces.columns = ["xMax","yMax","zMax","xMin","yMin","zMin", "id" ]
    print('{} meshes faces in set'.format(len(mesh_faces)))
    mesh_faces.head()

    # ## Creating all cross product of points vs targets to represent the lines of view
    lines = pov_
    lines = lines.assign(foo=1).merge(target_.assign(foo=1)).drop('foo', 1)
    lines = lines.drop_duplicates()
    lines = lines.reset_index()
    lines = lines.drop(['index'], axis=1)

    print('{} lines between POV and targets'.format(len(lines)))
    #lines.head()


    # ## Converting lines to bounding boxes
    bbx = pd.DataFrame(columns = ["xMax","yMax","zMax","xMin","yMin","zMin"])
    bbx['xMax'] = lines[['x', 'x1']].values.max(1)
    bbx['yMax'] = lines[['y', 'y1']].values.max(1)
    bbx['zMax'] = lines[['z', 'z1']].values.max(1)
    bbx['xMin'] = lines[['x', 'x1']].values.min(1)
    bbx['yMin'] = lines[['y', 'y1']].values.min(1)
    bbx['zMin'] = lines[['z', 'z1']].values.min(1)

    bbx.head()


    # ## Finding if lines bounding box versus meshes bounding box intersect
    # ### Estimation of total calculation in meshes versus lines bounding boxes (worst case scenario)

    print('{} possible calculations between meshes and lines'.format(len(bbx)* len(meshes_)))
    bbx2 = bbx 

    resultA = meshes_.apply(lambda x: checkmesh( bbx2.values, x), axis=1)
    meshes_['hits'] = resultA
    print('{} meshes with intersections'.format(len(meshes_[resultA])))


    # ## Finding mesh intersection

    # Filtering only the mesh faces that belong to a mesh from previews test
    filter = mesh_faces["id"].isin(meshes_[resultA]['id'])
    mesh_faces_filter = mesh_faces[filter]
    print('{} faces to test'.format(len(mesh_faces_filter)))
    print('{} possible intersections to test'.format(len(mesh_faces_filter) * len(lines)))

    pool = Pool(processes=10)

    
    funB = partial(checkFaces,mesh_faces_filter.drop('id', axis=1).values)
    #resultsB = [funB(l) for l in lines.values]
    resultsB = pool.map(funB,lines.values)


    lines['hits']= resultsB
    positive = len(lines[lines['hits'] == False])
    print('{} lines with clean sight from POV to targets'.format(positive))
    negative = len(lines[lines['hits'] == True])
    print('{} lines with possible context intersection'.format(negative))


    # ## Saving lines with no intersection
    lines[ lines['hits'] == False].to_csv('positive.csv')

    # ## Saving lines with possible intersection

    lines[ lines['hits'] == True].to_csv('negative.csv')
    end = time.time()
    print('total time {} seconds'.format(round(end-start, 3)))
