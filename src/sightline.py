#get sphere
import bpy
import os
import time
from mathutils import Vector


print("Starting!")
log = []
coords = []
hits = []

name = str(round(time.time()))
f = open(os.path.expanduser('~/Documents/sightline/log.txt'), 'w')
f.write('')
f.close()
    
def saveLog(delta, message):
    f = open(os.path.expanduser('~/Documents/sightline/log.txt'), 'a')
    f.write('{}, {}\n'.format( delta ,message))
    f.close()

def deltas(message):
    log.append((time.time() , message))


#raytrace from center to target vertex

def drawLine(name, p1, p2):
    # create the Curve Datablock
    curveData = bpy.data.curves.new(name, type='CURVE')
    curveData.dimensions = '3D'
    curveData.resolution_u = 2
    polyline = curveData.splines.new('POLY')
    polyline.points.add(1)
    x,y,z = p1
    polyline.points[0].co = (x, y, z, 1)
    x,y,z = p2
    polyline.points[1].co = (x, y, z, 1)
    # create Object
    curveOB = bpy.data.objects.new('raytrace', curveData)
    curveData.bevel_depth = 0.01


    bpy.data.collections["Points"].objects.link(curveOB)
    #scn.collection.objects.active = curveOB


def clean():
    bpy.ops.object.select_all(action='DESELECT')
    objs = bpy.data.objects
    for o in objs:
        if 'raytrace' in o.name or 'point' in  o.name:
            deltas('clean')
            
            o.select_set(True)
    bpy.ops.object.delete()
    
cube = bpy.context.scene.objects.get('Cube')
if not cube:
    bpy.ops.mesh.primitive_cube_add(size=0.1,location=(0,0,0))
    cube = bpy.context.scene.objects['Cube']

def CubeFromPoint(location):
    coll = bpy.data.collections.get('Points')

    if not coll:
        coll = bpy.data.collections.new('Points')
        bpy.context.scene.collection.children.link(coll)

    dupliCube = cube.copy()
    dupliCube.location = location
    dupliCube.name = "point"
    
    coll.objects.link( dupliCube )
  
    deltas('cube placed')
    

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

def GetPOV():
    bpy.ops.object.select_pattern(pattern="Sphere*")
    [sphere.hide_set(False) for sphere in bpy.context.selected_objects]
    print(bpy.context.selected_objects)
    centers = [POVCenter(sphere) for sphere in bpy.context.selected_objects]

    [sphere.hide_set(True) for sphere in bpy.context.selected_objects]
    bpy.ops.object.select_all(action='DESELECT')

    return centers

def POVCenter(sphere):
    print(sphere.matrix_world.to_translation())
    return sphere.matrix_world.to_translation()

#cleanLog()

start = time.time()
deltas('starting script')

# Clean
# Select objects
# Place points
# Select POV
# For each point

clean()

# Create points per vertex
bpy.ops.object.select_pattern(pattern="Obj*")
vertex = []
for o in bpy.context.selected_objects:
    deltas('process points')
    vertex.extend([(o.matrix_world @ v.co) for v in o.data.vertices])
[CubeFromPoint(c) for c in vertex]
bpy.ops.object.select_all(action='DESELECT')
# Get POV centers

centers = GetPOV()

for center in centers:
    [rayFromScene(o, center)  for o in vertex]
deltas('finish script')

[saveLog(l[0], l[1]) for l in log]
print("Done!")

f = open(os.path.expanduser('~/Documents/sightline/points.txt'), 'a')
for h in hits:
    p = h[0]
    f.write('{},{},{},{}\n'.format(p[0],p[1],p[2], h[1]))
f.close()