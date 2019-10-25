# Sightline studies 
The project tries to find different approaches to the problem of finding invisible points within a street art installation.

Content
1. **[Sightline using Blender 2.8](https://github.com/pabloderen/SightlineStudy#sightline-using-blender-28)**
2. **[Collision Detection using Pandas and Numpy](https://github.com/pabloderen/SightlineStudy#collision-detection-using-pandas-and-numpy)**

## Sightline using Blender 2.8

![blender sample](https://github.com/pabloderen/Blender_SighlineStudy/raw/master/img/01_Blender_Script.png)

For this [approach](https://github.com/pabloderen/SightlineStudy/blob/master/src/blender/sightline.py), we use the scene method ray_cast to check if a point is visible from a specific point in space.
Access objects vertex

```python
bpy.ops.object.select_pattern(pattern="Obj*")
vertex = []
for o in bpy.context.selected_objects:
    deltas('process points')
    vertex.extend([(o.matrix_world @ v.co) for v in o.data.vertices])
```
Get point of view (POV)  - "Spheres":

```python
def GetPOV():
    bpy.ops.object.select_pattern(pattern="Sphere*")
    [sphere.hide_set(False) for sphere in bpy.context.selected_objects]
    print(bpy.context.selected_objects)
    centers = [POVCenter(sphere) for sphere in bpy.context.selected_objects]

    [sphere.hide_set(True) for sphere in bpy.context.selected_objects]
    bpy.ops.object.select_all(action='DESELECT')

    return centers
```

And lastly, detect if vertex is visible from POV using scene.ray_cast()

```python
def rayFromScene( origin, dst):

    layer = bpy.context.view_layer
    scn = bpy.context.scene
    direction =  origin - dst
    hit, loc, normal, index, obj, matrix = scn.ray_cast(layer, dst, direction)

    if hit and 'point' in obj.name:
        drawLine("o", dst, loc)
        deltas('hit on point')
        
        
        distance = (origin - dst).length
        hits.append((loc, distance))
    else:
        deltas('no hit on point')
        
```   
**TODO**: Use multiprocessor to improve execution time.
      Investigate the use of a render engine to use the ligth ray trace instead.


# Collision Detection using Pandas and Numpy

The next step was to investigate the use of python libraries Pandas and Numpy to perform the calculation thru an agnostic [approach](https://github.com/pabloderen/SightlineStudy/blob/master/src/rhino/sightline.py) not depending on 3D software.
For this we imported information from the 3D model formated in 4 different datasets:

* Points of Views (x,y,z)
* Targets - points over the object to be tested for occlusion (x,y,z)
* Meshes - bounding boxes of possible occlutors (X,Y,Z,x,y,z,Id)
* Faces - boungin boxes of faces of the previous meshes (X,Y,Z,x,y,z,Mesh_Id)

## Create sightlines
The first step is to construct the cross product of all POV vs Targers

```python

lines = pov_ #POV dataset readed from a csv
lines = lines.assign(foo=1).merge(target_.assign(foo=1)).drop('foo', 1) # merging POV with Targets in all possible ways
lines = lines.drop_duplicates()
lines = lines.reset_index() # Droping the first index
lines = lines.drop(['index'], axis=1) # droping the second index

```
## Line vs Mesh bounding box

With the lines reconstructed we test each line against the list of meshes

```python
# Method for AABB vs line took from https://github.com/BSVino/MathForGameDevelopers/tree/line-box-intersection
#We check each bbx plane against one plane of the line and return a low high value to be used again to compare
def XClipLine(d,vecMax, vecMin,  v0,  v1, f_low, f_high):

	f_dim_low = (vecMin[d] - v0[d])/(v1[d] - v0[d] + 0.0000001)
	f_dim_high = (vecMax[d] - v0[d])/(v1[d] - v0[d]+ 0.0000001)

	# Make sure low is less than high
	if (f_dim_high < f_dim_low):
		f_dim_high, f_dim_low = f_dim_low, f_dim_high

	# // If this dimension's high is less than the low we got then we definitely missed. 
	if (f_dim_high < f_low):
		return False

	# // Likewise if the low is less than the high.
	if (f_dim_low > f_high):
		return False

	# // Add the clip from this dimension to the previous results 
	f_low = max(f_dim_low, f_low)
	f_high = min(f_dim_high, f_high)

	if (f_low > f_high):
		return False

	return f_low , f_high

# Method for AABB vs line took from https://github.com/BSVino/MathForGameDevelopers/tree/line-box-intersection
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


for b in meshes:
    #check if line line intersect with mesh
    bbx = BoundingBoxCreate(b)
    if LineAABBIntersection(bbx, line):
        return True

```

## Line vs Mesh voxel

If the mesh is collisioning with the line, we split the mesh bbx in 4 and try each section for colissions.

```python
def split(aabb):
	minX = aabb.vecMin[0]
	maxX = aabb.vecMax[0]
	minY = aabb.vecMin[1]
	maxY = aabb.vecMax[1]
	minZ = aabb.vecMin[2]
	maxZ = aabb.vecMax[2]
	centerX = np.average([minX, maxX])
	centerY = np.average([minY, maxY])
	#centerZ = (minZ + maxZ)/2 #for future implementation

	bbox0 = (maxX, maxY, maxZ, centerX, centerY, minZ)
	bbox1 = (centerX, maxY,maxZ,  minX, centerY, minZ)
	bbox2 = (maxX, centerY, maxZ, centerX, minY, minZ)
	bbox3 = (centerX, centerY, maxZ, minX, minY, minZ)
	return bbox0, bbox1 , bbox2, bbox3

#same function as before but more complete
def checklines(meshes, faces, line):
	
	for b in meshes:
		#check if line line intersect with mesh
		bbx = BoundingBoxCreate(b)
		if LineAABBIntersection(bbx, line):
		
			#if true split bbx in 4
			splitted  = split(bbx)
			for s in splitted:
				if LineAABBIntersection( BoundingBoxCreate(s) , line):


```

## Line vs Faces

Finally, when the result it's true we test the faces which their center point it's located inside the mesh

```python

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

```

## Export result
By now we can be sure that lines resulting in a False intersection have a clean 'view' of the object. The rest of the lines now filtered can be tested inside the 3D software for more accurate intersection.

## PRO Tip
The performance can be improved by using pool and numba 

```python

pool = Pool(processes=12)
funB = partial(checklines,meshes_.values, mesh_faces.values)
resultsB = pool.map(funB,lines.values)


lines['hits']= resultsB
positive = len(lines[lines['hits'] == False])
print('{} lines with clean sight from POV to targets'.format(positive))
negative = len(lines[lines['hits'] == True])
print('{} lines with possible context intersection'.format(negative))

```

## TODO
* Test using CUDA script to compute
* Improve numba scripts
