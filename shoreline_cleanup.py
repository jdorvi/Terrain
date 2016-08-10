# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#Import Modules
#import os
#import shapefile
#import archook
#archook.getarcpy
#import arcpy

#Run this script on singlepart layers
import os
os.chdir("C:/Users/jdorvinen/Documents/Great_Lakes/Wayne/")

import shapefile
sf = shapefile.Reader("Bathy_Lidar_2001_100m_clip_singlepart")
shapes = sf.shapes()
zloc = []

for i in range(len(shapes)):
    if shapes[i].z[0] > 245.5:
        zloc.append(i)

w = shapefile.Writer(shapeType=11)
w.autoBalance = 1
w.field('OID','C','40')

for i in zloc:
    x = shapes[i].points[0][0]
    y = shapes[i].points[0][1]
    z = shapes[i].z[0]
    w.point(x,y,z)
    w.record(OID = str(i))

w.save("bathy__2001_remove")