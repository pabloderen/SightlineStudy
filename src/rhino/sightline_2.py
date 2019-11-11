import Rhino
import scriptcontext
import rhinoscriptsyntax as rs


#Get all objects from layer and create a box onvertex Debug Done
#save list of all boxes #Done
#go to each POV and select visible
#save visible to list
#clean list just with elements in list of boxes


def GetObjectsFromLayer(layername):

    rhobjs = scriptcontext.doc.Objects.FindByLayer(layername)

    return rhobjs

def SetCamera(pov, direction):

    location = pov.Geometry.Location
    view = Rhino.RhinoDoc.ActiveDoc.Views.ActiveView
    name = view.ActiveViewport.Name
    vp = view.ActiveViewport
    # save the current viewport projection
    vp.PushViewProjection()
    vp.CameraUp = Rhino.Geometry.Vector3d.ZAxis
    
    vp.SetCameraLocation(location, False)
    if direction:
        
        lookat = Rhino.Geometry.Point3d( location.X + 100000, location.Y, location.Z)
        vp.SetCameraDirection(lookat - location, True)
    else:
       
        lookat = Rhino.Geometry.Point3d( location.X - 100000, location.Y, location.Z)
        vp.SetCameraDirection(lookat - location, True)
    vp.Name = name
    vp.Camera35mmLensLength = 0.1
    
    return vp.Name

def SelectByPOV(POV, points):
    SetCamera(POV,0)
    
    rs.Command("_SelVisible _Enter")
    selection = rs.SelectedObjects()
    visible = set(points) & set(selection)
    selection = rs.UnselectAllObjects()
    
    
    output = [points.index(i) for i in visible]
    
    SetCamera(POV,1)
    rs.Command("_SelVisible _Enter")
    selection = rs.SelectedObjects()
    visible = set(points) & set(selection)
    selection = rs.UnselectAllObjects()
    
    output.extend( [points.index(i) for i in visible])
    p = POV.Geometry.Location
    object = {}
    object['Location'] = (p.X,p.Y,p.Z)
    object['VisiblePoints'] = output
    return object
    
def CreatePoints():
    detection = GetObjectsFromLayer('Detection')
    vertex = []
    #Extract all vertex from meshes
    def getTargetPoints(o):
        global vertex
        return [v for v in o.Geometry.Vertices]
    
    [vertex.extend(getTargetPoints(o)) for o in detection]
    for v in vertex:
        rs.AddSphere(v, 0.1)
    
    

rs.EnableRedraw(False)

#CreatePoints()

def VisibleObjects(view=None, select=False, include_lights=False, include_grips=False):
    """Return identifiers of all objects that are visible in a specified view
    Parameters:
      view [opt] = the view to use. If omitted, the current active view is used
      select [opt] = Select the objects
      include_lights [opt] = include light objects
      include_grips [opt] = include grip objects
    Returns:
      list of Guids identifying the objects
    """
    it = Rhino.DocObjects.ObjectEnumeratorSettings()
    it.DeletedObjects = False
    it.ActiveObjects = True
    it.ReferenceObjects = True
    it.IncludeLights = include_lights
    it.IncludeGrips = include_grips
    it.IncludePhantoms = False
    it.VisibleFilter = True
    viewport = Rhino.RhinoDoc.ActiveDoc.Views.ActiveView.ActiveViewport
    it.ViewportFilter = viewport

    object_ids = []
    e = scriptcontext.doc.Objects.GetObjectList(it)
    for object in e:
        bbox = object.Geometry.GetBoundingBox(True)
        if viewport.IsVisible(bbox):
            if select: object.Select(True)
            object_ids.append(object.Id)

    if object_ids and select: scriptcontext.doc.Views.Redraw()
    return object_ids

r = VisibleObjects(select = True)

print(dir(Rhino.DocObjects.ObjectEnumeratorSettings()))
#
#points =[x.Id for x in GetObjectsFromLayer('Points')]
#POV = GetObjectsFromLayer('POV')
#results = []
#for p in POV:
#    results.append(SelectByPOV(p, points))
#
##with open('points.csv', 'w') as f:
##    for i,p in enumerate(points):
##        try:
##            point = rs.SurfaceVolumeCentroid(p)[0]
##            
##            f.write("{},{},{},{}\n".format(i, point.X,point.Y, point.Z ))
##        except:
##            pass
#
#with open('results.csv', 'w') as f:
#    for r in results:
#
#            
#       f.write(str(r) + '\n')
#
#
#rs.EnableRedraw(True)