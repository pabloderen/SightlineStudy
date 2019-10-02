import Rhino
import scriptcontext
import ghpythonlib.parallel
import ghpythonlib.components as gc
import rhinoscriptsyntax as rs
import csv
import Rhino.Geometry as rg
import os


def GetObjectsFromLayer(layername):

    rhobjs = scriptcontext.doc.Objects.FindByLayer(layername)
    output = []
    for obj in rhobjs:
        output.append(obj)
    return output

def roundPoint(pt):
    tol = 5
    p3D = Rhino.Geometry.Point3d(round(pt.X,tol),round(pt.Y,tol), round(pt.Z,tol))
    return p3D

def faceBoundingBox(object):
    output = []
    faces = object.Geometry.Faces
    count = len(faces)
    tol = 4
    for i in range(count):
        
        bbx = faces.GetFaceBoundingBox(i)
        outCSV = "{},{},{},{},{},{}".format( round(bbx.Max.X,tol), round(bbx.Max.Y,tol), round(bbx.Max.Z,tol),round(bbx.Min.X,tol), round(bbx.Min.Y,tol), round(bbx.Min.Z,tol))
        output.append(outCSV)
    return output


def getObjectOnLayer(layername):

    rhobjs = scriptcontext.doc.Objects.FindByLayer(layername)
    return rhobjs



def BBXtoCSV(obj, objIndex):
    '''Create a point representing a vertex'''
    tol = 4
    if isinstance(obj, rg.Line):
        point = obj.BoundingBox
    else:
        point = obj.Geometry.GetBoundingBox(True)
    return "{},{},{},{},{},{},{},{}\n".format(objIndex, round(point.Max.X,tol), round(point.Max.Y,tol), round(point.Max.Z,tol), round(point.Min.X,tol), round(point.Min.Y,tol), round(point.Min.Z,tol), obj.Id)

def pointToCSV(point):
    '''Create a point representing a vertex'''
    tol = 4
    return "{},{},{}\n".format(point.X, point.Y, point.Z)



def createGCLines(pointsOfView, vertex):
    
    lines = [gc.Line(a,b) for a in pointsOfView for b in vertex]
    return lines

def createRhinoLines(pointsOfView, a):
    
    lines = [Rhino.Geometry.Line(a,b) for a in pointsOfView for b in vertex]
    return lines


    
sample = []


    
def simplifyPoints(p):
   tol = str(scriptcontext.doc.ModelAbsoluteTolerance).count('0')
   point =rg.Point3d(round(p.X, tol),round(p.Y, tol), round(p.Z, tol))
   return point

def writePoints(vertex, name):
    
    f= open("{}.csv".format(name),"a")
    for l in vertex:
        f.write(l )

    f.close() 



if __name__=="__main__":
    files = ["mesh_faces.csv","pov_.csv","targets_.csv","context_.csv"]
    for f in files:
        if os.path.exists(f):
            os.remove(f)


    #Get elements to detect, TODO replace with other method for points
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    detection = GetObjectsFromLayer('Detection')
    context = GetObjectsFromLayer('Context')
#    context.extend(detection)
    vertex = []
    #Extract all vertex from meshes
    

    def getTargetPoints(o):
        global vertex
        vertex.extend([v for v in o.Geometry.Vertices])
    
    ghpythonlib.parallel.run(getTargetPoints,detection, True)
    POV = GetObjectsFromLayer('POV')
    pointsOfView = []
    #Extract all vertex from meshes
    for o in POV:
        pointsOfView.append(o.Geometry.Location)

#    sample = createRhinoLines(pointsOfView, vertex)
#    result = []
#    lines = [BBXtoCSV(s, idx) for idx, s in enumerate(sample)]

    povs = [pointToCSV(p) for p in pointsOfView]
    targets_ = [pointToCSV(p) for p in vertex]

    meshes = [BBXtoCSV(s, idx) for idx, s in enumerate(context)]
    
    writePoints(povs, "pov_")
    writePoints(targets_, "targets_")
    writePoints(meshes, "context_")
    

    points = [faceBoundingBox(o) for o in context]
    
    with open('mesh_faces.csv', 'w') as f:
        count = len(context)
        for i in range(count):
            for bb in points[i]:
                f.write("{},{}\n".format( bb, context[i].Id ))
    