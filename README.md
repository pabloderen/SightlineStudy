# Sightline studies 
The project tries to find different approaches to the problem of finding invisible points within a street art installation.

## Sightline using Blender 2.8

![blender sample](https://github.com/pabloderen/Blender_SighlineStudy/raw/master/img/01_Blender_Script.png)

For this approach, we use the scene method ray_cast to check if a point is visible from a specific point in space.
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
