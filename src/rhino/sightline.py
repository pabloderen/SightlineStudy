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

# @numba.jit(forceobj=True, parallel=True)
def FilterByBBX(Faces, line):
	maxX = line[0]
	maxY = line[1]
	maxZ = line[2]
	minX = line[3]
	minY = line[4]
	minZ = line[5]
	midX = (Faces[:,0] + Faces[:,3])/2
	mixY = (Faces[:,1] + Faces[:,4])/2
	mixZ = (Faces[:,2] + Faces[:,5])/2
	aa = np.where((midX >= minX) & ( mixY >= minY) & (mixZ >= minZ) & (midX <= maxX) & (mixY <= maxY) & (mixZ <= maxZ)   )
	return Faces[aa]


class BoundingBoxCreate(): 
	def __init__(self, line):

		XMax = max(line[3],line[0]) 
		YMax = max(line[4],line[1]) 
		ZMax = max(line[5],line[2]) 
		XMin = min(line[3],line[0])
		YMin = min(line[4],line[1])
		ZMin = min(line[5],line[2])
		self.vecMin = (XMin,YMin,ZMin)
		self.vecMax = (XMax,YMax,ZMax)


def split(aabb):
	minX = aabb.vecMin[0]
	maxX = aabb.vecMax[0]
	minY = aabb.vecMin[1]
	maxY = aabb.vecMax[1]
	minZ = aabb.vecMin[2]
	maxZ = aabb.vecMax[2]
	centerX = np.average([minX, maxX])
	centerY = np.average([minY, maxY])
	#centerZ = (minZ + maxZ)/2

	bbox0 = (maxX, maxY, maxZ, centerX, centerY, minZ)
	bbox1 = (centerX, maxY,maxZ,  minX, centerY, minZ)
	bbox2 = (maxX, centerY, maxZ, centerX, minY, minZ)
	bbox3 = (centerX, centerY, maxZ, minX, minY, minZ)
	return bbox0, bbox1 , bbox2, bbox3

# @numba.jit(forceobj=True, parallel=True)
def XClipLine(d,vecMax, vecMin,  v0,  v1, f_low, f_high):

	# // Find the point of intersection in this dimension only as a fraction of the total vector http://youtu.be/USjbg5QXk3g?t=3m12s
	#

	
	f_dim_low = (vecMin[d] - v0[d])/(v1[d] - v0[d] + 0.0000001)
	f_dim_high = (vecMax[d] - v0[d])/(v1[d] - v0[d]+ 0.0000001)

	# // Make sure low is less than high
	if (f_dim_high < f_dim_low):
		f_dim_high, f_dim_low = f_dim_low, f_dim_high

	# // If this dimension's high is less than the low we got then we definitely missed. http://youtu.be/USjbg5QXk3g?t=7m16s
	if (f_dim_high < f_low):
		return False

	# // Likewise if the low is less than the high.
	if (f_dim_low > f_high):
		return False

	# // Add the clip from this dimension to the previous results http://youtu.be/USjbg5QXk3g?t=5m32s
	f_low = max(f_dim_low, f_low)
	f_high = min(f_dim_high, f_high)

	if (f_low > f_high):
		return False

	return f_low , f_high





# // Find the intersection of a line from v0 to v1 and an axis-aligned bounding box http://www.youtube.com/watch?v=USjbg5QXk3g
#@numba.jit(forceobj=True, parallel=True)
def LineAABBIntersection(aabbBox,line):

	f_low = 0
	f_high = 1
	v0, v1 = (line[0], line[1], line[2]), (line[3], line[4], line[5])
	vecMax, vecMin  =  np.array(aabbBox.vecMax) , np.array(aabbBox.vecMin)
	x = XClipLine(0, vecMax, vecMin , v0, v1, f_low, f_high)
	if not x:
		return False
	

	x = XClipLine(1, vecMax, vecMin , v0, v1, x[0], x[1])
	if not x :
		return False
	x = XClipLine(2, vecMax, vecMin , v0, v1, x[0], x[1])
	if not x:
		return False

	return True

def checkFaces(Faces, line):

	for f in Faces:
		if LineAABBIntersection(BoundingBoxCreate(f),line):
			return True
	return False


# @numba.jit(forceobj=True, parallel=True)
def checklines(meshes, faces, line):
	
	for b in meshes:
		#check if line line intersect with mesh
		bbx = BoundingBoxCreate(b)
		if LineAABBIntersection(bbx, line):
		
			#if true split bbx in 4
			splitted  = split(bbx)
			for s in splitted:
				
				if LineAABBIntersection( BoundingBoxCreate(s) , line):
					
					ff = faces[faces[:,6] == b[6]]
					filteredFaces = FilterByBBX(ff, s)
					drop = np.delete(filteredFaces, np.s_[6:], axis=1)
					check = checkFaces(drop,line)
					if check:
						return True

	return False




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

	# ## Finding mesh intersection

	pool = Pool(processes=12)
	funB = partial(checklines,meshes_.values, mesh_faces.values)
	
	# funB = partial(checkFaces,mesh_faces_filter.drop('id', axis=1).values)
	#resultsB = [checklines(meshes_.values, mesh_faces.values, l) for l in lines.values]
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
