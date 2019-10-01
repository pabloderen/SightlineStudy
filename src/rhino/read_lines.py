import Rhino
import scriptcontext
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import csv

with open('negative.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    next(readCSV)
    for row in readCSV:
        a = rg.Point3d(float(row[1]),float(row[2]),float(row[3]))
        b = rg.Point3d(float(row[4]),float(row[5]),float(row[6]))
        
        rs.AddLine(a,b)