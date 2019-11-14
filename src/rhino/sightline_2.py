import rhinoscriptsyntax as rs
import Rhino
import ghpythonlib.components as ghcomp
import ghpythonlib.parallel
import math
from functools import partial
import scriptcontext
import os
import time
import json

now = 0
def saveLog( message):
    global now
    if not now:
        now = time.time()
    f = open(os.path.expanduser('~/Documents/log.txt'), 'a')
    f.write('{},  {}\n'.format(time.time() - now,  message)) 
    f.close()
    now =  time.time()



def createPoints():
    now =time.time()
    saveLog("start creating points")
    matrix = None
    if not matrix:
        matrix = 1000
    #set point tolerance
    tol=scriptcontext.doc.ModelAbsoluteTolerance
    #size of point matrix

    vertices = []
    #All objects in layer detection
    objects = scriptcontext.doc.Objects.FindByLayer("Detection")


    def placePoints(obj):
        vertices = []
        sel_vol= obj.Geometry
        bbx = sel_vol.GetBoundingBox(True)
        _min = bbx.Min
        _max = bbx.Max
        curvesContours =[]
        curves = []
        zContour = Rhino.Geometry.Point3d(_min.X,_min.Y,_max.Z)
        yContour = Rhino.Geometry.Point3d(_max.X,_min.Y,_max.Z)
        xContour = Rhino.Geometry.Point3d(_max.X,_min.Y,_min.Z)
        curvesContours.extend( Rhino.Geometry.Mesh.CreateContourCurves(sel_vol, _min, zContour, matrix))
        curvesContours.extend(Rhino.Geometry.Mesh.CreateContourCurves(sel_vol, _max, yContour, matrix))
        curvesContours.extend(Rhino.Geometry.Mesh.CreateContourCurves(sel_vol, _min, xContour, matrix))
        
        #Create temporary curves
        for curve in curvesContours:
            curve_object_id = scriptcontext.doc.Objects.AddCurve(curve)
            curves.append(curve_object_id)
            scriptcontext.doc.Objects.Select(curve_object_id)
        #Find all curves intersections
        for c in curves:
            c1 = rs.coercecurve(c)
            for cc in curves:
                c2 = rs.coercecurve(cc)
                _points = Rhino.Geometry.Intersect.Intersection.CurveCurve(c1, c2, 0.01 , tol)
                for p in _points:
                    vertices.append(p.PointA)
        #Remove curves from model
        for c in curves:
            scriptcontext.doc.Objects.Delete(c, True)
            
        return vertices

    rs.EnableRedraw(False)
    #ghpythonlib.parallel.run(placePoints, objects, True)
    batch = [ placePoints(o) for o in objects]
    
    [vertices.extend(o) for o in batch]
    
    #clean points
    unique = set(vertices)
    
    points = [rs.AddSphere(p, 50 ) for p in unique]
    
    layername = "Target"
    if not rs.IsLayer(layername): rs.AddLayer(layername)
    rs.ObjectLayer(points, layername)
    rs.EnableRedraw(True)
    saveLog("done creating points")
    
    with open('points.csv', 'w') as f:
        for i,p in enumerate(points):
            try:
                point = rs.spj(p)
                
                f.write("{},{},{},{}\n".format(p, point.X,point.Y, point.Z ))
            except:
                pass
    
    

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
#    if direction:
#        
#        lookat = Rhino.Geometry.Vector3d( location.X + 10000, location.Y, location.Z)
#        #vp.SetCameraDirection(lookat, True)
#    else:
       
    lookat = Rhino.Geometry.Point3d( location.X + 10000, location.Y, location.Z)
    vp.SetCameraDirection(location - lookat  , True)
    vp.Name = name
    view.Redraw()
    vp.Camera35mmLensLength = 50
    
    return vp.Name

def SelectByPOV(POV, points):
    SetCamera(POV,1)
    
    rs.Command("_SelVisible _Enter")
    selection = rs.SelectedObjects()
    
    visible = [o for o in selection if rs.IsPoint(o)]
    rs.UnselectAllObjects()
    output = []
    
    output.extend(visible)
    
#    SetCamera(POV,1)
#    rs.Command("_SelVisible _Enter")
#    selection = rs.SelectedObjects()
#    visible = set(points) & set(selection) 
#    selection = rs.UnselectAllObjects()
#    output = list(set(output))

    p = POV.Geometry.Location
    object = {}
    object['Location'] = (p.X,p.Y,p.Z)
    object['VisiblePoints'] = map(str, output)
    saveLog("Done POV")
    return object
    
def SetCameraDefault():

    view = Rhino.RhinoDoc.ActiveDoc.Views.ActiveView
    name = view.ActiveViewport.Name
    vp = view.ActiveViewport
    vp.Camera35mmLensLength = 50
    
    return vp.Name
    
    
def clean():
    '''Remove old targets'''
    try:
        rs.PurgeLayer("Target")
        print("Removed layers")
    except:
        print("No Target layers")




def runSightline():
    now =time.time()
    saveLog("start process")
#    
    points =[x.Id for x in GetObjectsFromLayer('Target')]
    POV = GetObjectsFromLayer('POV')
    results = []
    
    for p in POV:
        results.append(SelectByPOV(p, points))
    

    
    with open('results.csv', 'w') as f:
        json.dump(results, f)
           
    
    SetCameraDefault()
    
    rs.EnableRedraw(True)
    saveLog("Done process")
    

def drawResults():
    p = rs.GetObject()
    point = rs.coerce3dpoint(p)
    coordinates = [point.X,point.Y, point.Z]
    data = None
    with open('results.csv') as json_file:
        data = json.load(json_file)
        
    #Awful I know but is the best way to filter this I could find
    filterPoints = [x for x in data if str(x['Location']) in str(coordinates)]
    selectedPoint = None
    if filterPoints:
        selectedPoint = filterPoints[0]
    points = {}
    with open('points.csv') as f:
        for p in f:
            line = p.split(",")
            points[line[0]] = (line[1],line[2], line[3])

    visiblePoints = [x for x in selectedPoint["VisiblePoints"]]
    results = []
    for v in visiblePoints:
        p = points[v]
        rs.AddLine(p,selectedPoint["Location"])
        results.append(p)
    
    


#GUI options

options = ('Create points', 'Run detection', 'Clean points', 'Test result')

if options:
    result = rs.ListBox(options,
        "LoremLimpsum.\n"
        "More loremplipsum.\n"
        "\n"
        )
    if result: 
        if result in 'Create points':
            createPoints()
        if result in 'Run detection':
            runSightline()
        if result in 'Clean points':
            clean()
        if result in  'Test result':
            drawResults()
