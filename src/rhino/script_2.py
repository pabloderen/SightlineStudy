import Rhino
import ghpythonlib.parallel
import scriptcontext
import rhinoscriptsyntax as rs
import csv
import time
import os

rg = Rhino.Geometry

now = int(time.time())
logName = 'log_{}'.format(now)

def saveLog(start, message):
	end = time.time()
	delta = end-start
	f = open(os.path.expanduser('~/Documents/{}.txt'.format(logName)), 'a')
	f.write('{}, {}, {}\n'.format(time.time(), delta, message))
	f.close()

# three levels of detection
# mesh bounding box
# face bounding box
# face intersection
def GetObjectsFromLayer(layername):

    rhobjs = scriptcontext.doc.Objects.FindByLayer(layername)
    output = []
    for obj in rhobjs:
        output.append(obj)
    return output

def PointToCSV(point, objIndex):
    '''Create a obj line representing a vertex'''
    return "{},{},{},{},{},{},{}\n".format(objIndex, point.Min.X, point.Min.Y, point.Min.Z, point.Min.X, point.Min.Y, point.Min.Z)

def writePoints(vertex, name, objIndex):
    
    f= open("{}.csv".format(name),"a")
    for l in vertex:
        f.write(PointToCSV(l,objIndex ))

    f.close() 



def ProcessMesh(d):
    ix, o = d
    objBBX = o.Geometry.GetBoundingBox(True)
    writePoints([objBBX], 'MeshBBX_{}'.format(now), ix)
    faces = o.Geometry.Faces
    facesBoundingBox = []
    for i, f in enumerate(faces):

        bbx = faces.GetFaceBoundingBox(i)
        facesBoundingBox.append(bbx)

    writePoints(facesBoundingBox, 'FaceBBX_{}'.format(now), ix)
    saveLog(now, "end mesh")

if __name__=="__main__":

    detection = GetObjectsFromLayer('Detection')
    vertex = []
    #Extract all vertex from meshes
    
    saveLog(now, "starting script")
    d = [(ix, o) for ix,o in  enumerate(detection) ]
    ghpythonlib.parallel.run(ProcessMesh,d, True)
    saveLog(now, "end script")

    

    
