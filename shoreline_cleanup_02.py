# -*- coding: utf-8 -*-
"""
Must use Python 2

"""
def main():

###############################################################################
##   USER INPUTS   ############################################################
###############################################################################
    #Define Longterm Lake Elevation (feet)
    Ontario = 245.5
    #Erie    = 571
    lake_elevation = Ontario

    #Define Buffer Distances
    topo_buffer_distance  =  "50 Feet"
    bathy_buffer_distance = "330 Feet"
    point_buffer_distance = "0.1 Feet"

    #Point to layers
    #Data masks
    masksdir   = "P:/02/NY/Great Lakes Coastal/Terrain_Development/Oswego/masks/"
    topo_mask  = masksdir+"Oswego_topo_mask.shp"
    bathy_mask = masksdir+"Oswego_bathy_mask.shp"

    #Source data
    geodatabase = "P:/02/NY/Oswego_Co_36075/STUDY__TO90/GIS/DATA/TOPO/Terrain/Oswego_Terrain_ft.gdb/"
    topo_data   = geodatabase+"Topo_2014_lidar_C"
    bathy_data  = geodatabase+"Bathy_Lidar_2011_C"
    shoreline   = geodatabase+"Oswego_delineated_Shoreline_3D"

    #Point to temporary working directory
    temp_directory = "C:/Users/jdorvinen/Documents/Great_Lakes/Oswego/"

###############################################################################
##   IMPORT MODULES   #########################################################
###############################################################################
    import os
    import shapefile
    import archook
    archook.get_arcpy()
    import arcpy
    from datetime import datetime
    from time import strftime

###############################################################################
##   BEGIN SCRIPT   ###########################################################
###############################################################################
    begin = datetime.now()
    #Enter temporary working directory
    os.chdir(temp_directory)

    ###########################################################################
    #Buffer Shoreline
    ###########################################################################
    print("Buffering shoreline "+strftime("%Y-%m-%d %H:%M:%S"))
    topo_buffer  = temp_directory+"shoreline_topo_buffer.shp"
    bathy_buffer = temp_directory+"shoreline_bathy_buffer.shp"
    arcpy.Buffer_analysis(shoreline,
                          topo_buffer,
                          topo_buffer_distance,
                          "FULL","ROUND","NONE","#")
    arcpy.Buffer_analysis(shoreline,
                          bathy_buffer,
                          bathy_buffer_distance,
                          "FULL","ROUND","NONE","#")
    print("done")

    ###########################################################################
    #Clip data sources to shoreline buffer
    ###########################################################################
    topo_clip  = temp_directory+"topo_clip.shp"
    bathy_clip = temp_directory+"bathy_clip.shp"
    print("Clipping topo data to shoreline buffer "+strftime("%Y-%m-%d %H:%M:%S"))
    arcpy.Clip_analysis(topo_data,
                        topo_buffer,
                        topo_clip,"#")
    print("done")

    print("Clipping bathy data to shoreline buffer "+strftime("%Y-%m-%d %H:%M:%S"))
    arcpy.Clip_analysis(bathy_data,
                        bathy_buffer,
                        bathy_clip,"#")
    print("done")

    ###########################################################################
    #Explode clipped multipoint data to singlepoints
    ###########################################################################
    topo_explode  = temp_directory+"topo_explode.shp"
    bathy_explode = temp_directory+"bathy_explode.shp"
    print("Exploding clipped multipoint data "+strftime("%Y-%m-%d %H:%M:%S"))
    arcpy.MultipartToSinglepart_management(topo_clip,topo_explode)
    arcpy.MultipartToSinglepart_management(bathy_clip,bathy_explode)
    print("done")

    ###########################################################################
    #Select erroneous points from singlepoint topo and bathy layers
    ###########################################################################
    neg_onshore_remove  = temp_directory+"neg_onshore_remove.shp"
    pos_offshore_remove = temp_directory+"pos_offshore_remove.shp"

    print("Selecting out erroneous data points "+strftime("%Y-%m-%d %H:%M:%S"))
    def find_bad_points(points_layer,cutoff_elevation,savefile,topo_bathy):
        sf = shapefile.Reader(points_layer)
        shapes = sf.shapes()
        zloc = []

        if topo_bathy == "topo":
            for i in range(len(shapes)):
                if shapes[i].z[0] < cutoff_elevation:
                    zloc.append(i)
        elif topo_bathy == "bathy":
            for i in range(len(shapes)):
                if shapes[i].z[0] > cutoff_elevation:
                    zloc.append(i)
        else:
            print("ERROR: must define local variable 'topo_bathy' as 'topo' or 'bathy'")

        w = shapefile.Writer(shapeType=11)
        w.autoBalance = 1
        w.field('OID','C','40')

        for i in zloc:
            x = shapes[i].points[0][0]
            y = shapes[i].points[0][1]
            z = shapes[i].z[0]
            w.point(x,y,z)
            w.record(OID = str(i))

        w.save(savefile)

    find_bad_points(topo_explode,
                    lake_elevation,
                    neg_onshore_remove,
                    topo_bathy="topo")
    find_bad_points(bathy_explode,
                    lake_elevation,
                    pos_offshore_remove,
                    topo_bathy="bathy")
    print("done")

    ###########################################################################
    #Buffer selected erroneous points from topo and bathy layers
    ###########################################################################
    neg_onshore_buffer  = temp_directory+"neg_onshore_buffer.shp"
    pos_offshore_buffer = temp_directory+"pos_offshore_buffer.shp"

    print("Buffering selected points "+strftime("%Y-%m-%d %H:%M:%S"))
    arcpy.Buffer_analysis(neg_onshore_remove,
                          neg_onshore_buffer,
                          point_buffer_distance,
                          "FULL","ROUND","NONE","#")
    arcpy.Buffer_analysis(pos_offshore_remove,
                          pos_offshore_buffer,
                          point_buffer_distance,
                          "FULL","ROUND","NONE","#")
    print("done")

    ###########################################################################
    #Erase buffers from topo and bathy masks
    ###########################################################################
    topo_mask_v2  = temp_directory+"topo_mask_v2.shp"
    bathy_mask_v2 = temp_directory+"bathy_mask_v2.shp"

    print("Erasing buffered points from masks "+strftime("%Y-%m-%d %H:%M:%S"))
    arcpy.Erase_analysis(topo_mask,
                         neg_onshore_buffer,
                         topo_mask_v2,
                         "#")
    arcpy.Erase_analysis(bathy_mask,
                         pos_offshore_buffer,
                         bathy_mask_v2,
                         "#")
    print("done")
    #In a test run of Oswego County, NY (~33 miles of coastline) it took a
    #Total elapsed time of: 14:26:52.794000 to reach this point. Clipping is by
    #far the most time intensive of the operations performed. Initial clip of
    #source point data took ~14hrs. Expected total time to complete a county
    #of similar size to Oswego ~29hrs.

    ###########################################################################
    #Reclip source data to updated masks
    ###########################################################################
    """
    topo_data_v2  = temp_directory+"topo_data_v2.shp"
    bathy_data_v2 = temp_directory+"bathy_data_v2.shp"

    print("Clipping data to updated masks "+strftime("%Y-%m-%d %H:%M:%S"))
    arcpy.Clip_analysis(topo_data,
                        topo_mask_v2,
                        topo_data_v2,"#")
    arcpy.Clip_analysis(bathy_data,
                        bathy_mask_v2,
                        bathy_data_v2,"#")
    print("done")
    """
    ###########################################################################
    #Calculate total elapsed time
    ###########################################################################
    elapsed_time = datetime.now()-begin
    print("Script complete "+strftime("%Y-%m-%d %H:%M:%S"))
    print("Total elapsed time: "+str(elapsed_time))

if __name__ == "__main__":
    main()