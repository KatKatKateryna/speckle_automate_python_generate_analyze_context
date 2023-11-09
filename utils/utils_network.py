import math
from typing import List
from pandana.loaders import osm
import pandas as pd 

from specklepy.objects import Base
from specklepy.objects.geometry import Polyline, Point, Line
from utils.utils_geometry import rotate_pt 

from utils.utils_pyproj import create_crs, getBbox, reproject_to_crs

def calculateAccessibility(lat, lon, r):
    y0,x0,y1,x1 = getBbox(lat, lon, r)
    network = osm.pdna_network_from_bbox(y0,x0,y1,x1) 
    #print(network.nodes_df.head()) 
    #print(network.edges_df.head()) 

    #nodes = network.get_node_ids(network.nodes_df["x"][0:3], network.nodes_df["y"][:3]).values
    #print(network.nodes_df.columns)
    #nodes = network.nodes_df.iloc[:,0][0:3].to_list()
    nodes = network.node_ids.to_list()
    origs = [o for o in nodes for d in nodes]
    dests = [d for o in nodes for d in nodes]
    #distances = network.shortest_path_lengths(origs, dests)
    paths = network.shortest_paths(origs, dests)

    id_counts = {}
    for p in paths:
        for p_id in p:
            try: val = id_counts[p_id] + 1
            except: val = 1
            id_counts.update({ p_id: val })
    #print(id_counts)
    return network, id_counts
    
def colorSegments(lat:float, lon:float, r:float, angle_rad:float):
    lines = []
    maxCount = 0

    projectedCrs = create_crs(lat, lon)

    network, id_counts = calculateAccessibility(lat, lon, r)
    nodesX = network.nodes_df.iloc[:,0].to_list()
    nodesY = network.nodes_df.iloc[:,1].to_list()
    nodesIds = network.node_ids.to_list()

    for i in network.edges_df.index:
        fromNode = i[0] # id 
        toNode = i[1] # id 
        
        try:
            fromNodeCount = id_counts[fromNode]
            toNodeCount = id_counts[toNode]
            count = None
            if fromNodeCount is not None and toNodeCount is not None:
                count = min(fromNodeCount, toNodeCount)
                if count> maxCount: maxCount = count
        
            # get coordinates 
            ind1 = nodesIds.index(fromNode)
            lon1, lat1 = reproject_to_crs(nodesY[ind1], nodesX[ind1], "EPSG:4326", projectedCrs)
            #pt1 = Point.from_list([lon1, lat1, 0])

            ind2 = nodesIds.index(toNode)
            lon2, lat2 = reproject_to_crs(nodesY[ind2], nodesX[ind2], "EPSG:4326", projectedCrs)
            #pt2 = Point.from_list([lon2, lat2, 0])

            length = math.sqrt( math.pow( (lon2-lon1),2) + math.pow( (lat2-lat1),2) )

            if length<1: continue
            
            if angle_rad == 0:
                pt1 = Point.from_list([lon1, lat1, 0])
                pt2 = Point.from_list([lon2, lat2, 0])
            else:
                coords1 = rotate_pt({"x": lon1, "y": lat1}, angle_rad)
                coords2 = rotate_pt({"x": lon2, "y": lat2}, angle_rad)
                pt1 = Point.from_list([coords1["x"], coords1["y"], 0])
                pt2 = Point.from_list([coords2["x"], coords2["y"], 0])

            line = Line(start =pt1, end=pt2, units = "m" )
            line.length = length
            line.count = count 
            lines.append(line)
        except: continue
    
    return lines, maxCount 
        
