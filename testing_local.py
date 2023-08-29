

r'''
- to install poetry, in cmd: 
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry 
- to add modules, in vs code:
poetry shell
poetry add numpy

# Reprojecting:
https://pyproj4.github.io/pyproj/stable/examples.html

# Network analysis:
https://networkx.org/documentation/stable/auto_examples/index.html#examples-gallery
https://github.com/networkx/networkx

# Satellite imagery
https://github.com/yannforget/landsatxplore

# Styling: 
https://github.com/pysal/mapclassify 

# Download elevation
https://github.com/bopen/elevation 

# Work with shapes
https://pypi.org/project/shapely/ 

# Geospatial data abstraction
https://pypi.org/project/GDAL/ 
first, download whl file here https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal , then pip install "....whl"

# Geospatial analysis 
https://github.com/geopandas/geopandas 

'''
from typing import List
from specklepy.transports.server import ServerTransport
from specklepy.api.credentials import get_local_accounts
from specklepy.api.operations import receive, send
from specklepy.api.client import SpeckleClient
from specklepy.objects import Base
from specklepy.objects.other import Collection
from flatten import flatten_base

server_url = "https://speckle.xyz/" # project_data.speckle_server_url
project_id = "17b0b76d13" #project_data.project_id
version_id = "5d720c0998" #project_data.version_id

#inputs.model_id = #project_data.model_id
RADIUS = 500 #float(inputs.radius) 
RESULT_BRANCH = "automate"

account = get_local_accounts()[2]
client = SpeckleClient(server_url)
client.authenticate_with_token(account.token)
commit = client.commit.get(project_id, version_id)
server_transport = ServerTransport(project_id, client)
base = receive(commit.referencedObject, server_transport)

objects = [b for b in flatten_base(base)]
print(objects)

def downloadElev():
    import elevation
    # clip the SRTM1 30m DEM of Rome and save it to Rome-DEM.tif
    elevation.clip(bounds=(12.35, 41.8, 12.65, 42), output='Rome-DEM.tif')
    # clean up stale temporary files and fix the cache in the event of a server error
    elevation.clean()

def createCRS(lat: float, lon: float):
    from pyproj import CRS
    from pyproj import Transformer

    newCrsString = "+proj=tmerc +ellps=WGS84 +datum=WGS84 +units=m +no_defs +lon_0=" + str(lon) + " lat_0=" + str(lat) + " +x_0=0 +y_0=0 +k_0=1"
    crs2 = CRS.from_string(newCrsString)
    return crs2


def reprojectToCrs(lat: float, lon: float, crs_from, crs_to, direction = "FORWARD"):
    from pyproj import CRS
    from pyproj import Transformer

    transformer = Transformer.from_crs(crs_from, crs_to, always_xy=True)
    pt = transformer.transform(lon, lat, direction=direction)

    return pt[0], pt[1] 

def cleanString(text: str) -> str:
    symbols = r"/[^\d.-]/g, ''"
    new_text = text
    for s in symbols:
        new_text = new_text.split(s)[0]#.replace(s, "")
    return new_text

def fix_orientation(polyBorder, reversed_vert_indices, positive = True, coef = 1): 
    
    sum_orientation = 0 
    for k, ptt in enumerate(polyBorder): #pointList:
        index = k+1
        if k == len(polyBorder)-1: index = 0
        pt = polyBorder[k*coef]
        pt2 = polyBorder[index*coef]

        sum_orientation += (pt2[0] - pt[0]) * (pt2[1] + pt[1]) 
    
    inverse = False
    if positive is True: 
        if sum_orientation < 0:
            reversed_vert_indices.reverse()
            inverse = True
    else: 
        if sum_orientation > 0:
            reversed_vert_indices.reverse()
            inverse = True
    return reversed_vert_indices, inverse

def extrudeBuildings(coords: List[dict], height: float):
    from specklepy.objects.geometry import Mesh 
    vertices = []
    faces = []
    colors = []
    
    # bottom
    reversed_vert_indices = list(range(int(len(vertices)/3), int(len(vertices)/3) + len(coords)))
    for c in coords: vertices.extend([c['x'], c['y'], 0])

    polyBorder = [ (vertices[ind*3], vertices[ind*3+1], vertices[ind*3+2] ) for ind in reversed_vert_indices]
    reversed_vert_indices, inverse = fix_orientation(polyBorder, reversed_vert_indices)
    faces.extend( [len(coords)] + reversed_vert_indices)

    # top
    reversed_vert_indices = list(range(int(len(vertices)/3), int(len(vertices)/3) + len(coords)))
    for c in coords: vertices.extend([c['x'], c['y'], height])

    polyBorder = [ (vertices[ind*3], vertices[ind*3+1], vertices[ind*3+2] ) for ind in reversed_vert_indices]
    reversed_vert_indices, inverse = fix_orientation(polyBorder, reversed_vert_indices)
    reversed_vert_indices.reverse()
    faces.extend( [len(coords)] + reversed_vert_indices)

    # sides
    for i,c in enumerate(coords):
        if i != len(coords)-1: nextC = coords[i+1] #i+1
        else: nextC = coords[0] #0
        #faces.extend( [4, i, nextC, nextC + len(coords), i+len(coords) ] )
        reversed_vert_indices = list(range(int(len(vertices)/3), int(len(vertices)/3) + 4))
        faces.extend([4] + reversed_vert_indices)
        if inverse is False:
            vertices.extend([c['x'],c['y'],0,c['x'],c['y'],height, nextC['x'],nextC['y'],height, nextC['x'],nextC['y'],0])
        else:
            vertices.extend([c['x'],c['y'],0, nextC['x'],nextC['y'],0, nextC['x'],nextC['y'],height,c['x'],c['y'],height])

    obj = Mesh.create(faces = faces, vertices = vertices)
    obj.units = "m"
    return obj 

def getBuildings(lat: float, lon: float):
    # https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0 
    import requests
    import json

    projectedCrs = createCRS(lat, lon)
    lonPlus1, latPlus1 = reprojectToCrs(1, 1, projectedCrs, "EPSG:4326")
    scaleX = lonPlus1 - lon
    scaleY = latPlus1 - lat
    r = RADIUS #meters

    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""[out:json];
    (node["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    way["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    relation["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    );out body;>;out skel qt;"""

    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()
    features = data['elements']

    ways = []
    tags = []

    rel_outer_ways = []
    rel_outer_ways_tags = []

    ways_part = []
    nodes = []

    for feature in features:
        # ways
        if feature['type'] == 'way':
            try:
                feature['id']
                feature['nodes']
                
                try: tags.append( { 'building': feature['tags']['building'], 'layer': feature['tags']['layer'] } )
                except: 
                    try: tags.append( { 'building': feature['tags']['building'], 'levels': feature['tags']['building:levels'] } )
                    except:
                        try:tags.append( { 'building': feature['tags']['building'], 'height': feature['tags']['height'] } )
                        except: tags.append( { 'building': feature['tags']['building']} )
                ways.append( { 'id': feature['id'], 'nodes': feature['nodes'] } )
            except:
                ways_part.append( { 'id': feature['id'], 'nodes': feature['nodes'] } )
        
        # relations 
        elif feature['type'] == 'relation':
            outer_ways = []
            try: outer_ways_tags = { 'building': feature['tags']['building'], 'layer': feature['tags']['layer'] }
            except: 
                try: outer_ways_tags = { 'building': feature['tags']['building'], 'levels': feature['tags']['building:levels']}
                except: 
                    try: outer_ways_tags = { 'building': feature['tags']['building'], 'height': feature['tags']['height'] }
                    except: outer_ways_tags = { 'building': feature['tags']['building'] }
            
            for n, x in enumerate(feature['members']):
                # if several Outer ways, combine them
                if feature['members'][n]['type'] == 'way' and feature['members'][n]['role'] == 'outer':
                    outer_ways.append( { 'ref': feature['members'][n]['ref'] } )
            rel_outer_ways.append( outer_ways )
            rel_outer_ways_tags.append( outer_ways_tags )
        
        # get nodes (that don't have tags)
        elif feature['type'] == 'node':
            try: feature['tags']
            except: nodes.append( { 'id': feature['id'], 'lat': feature['lat'], 'lon': feature['lon'] } )

    # turn relations_OUTER into ways
    for n, x in enumerate(rel_outer_ways):  
        # there will be a list of "ways" in each of rel_outer_ways
        full_node_list = []
        for m, y in enumerate(rel_outer_ways[n]): 
            #find ways_parts with corresponding ID
            for k, z in enumerate(ways_part): 
                if k == len(ways_part): break
                if rel_outer_ways[n][m]['ref'] == ways_part[k]['id']:
                    full_node_list += ways_part[k]['nodes'] 
                    ways_part.pop(k) # remove used ways_parts
                    k -= 1 # reset index
                    break
        ways.append( { 'nodes': full_node_list } ) 
        try: tags.append( { 'building': rel_outer_ways_tags[n]['building'], 'layer': rel_outer_ways_tags[n]['layer'] } )
        except:
            try:tags.append( { 'building': rel_outer_ways_tags[n]['building'], 'levels': rel_outer_ways_tags[n]['levels'] } )
            except:
                try:tags.append( { 'building': rel_outer_ways_tags[n]['building'], 'height': rel_outer_ways_tags[n]['height'] } )
                except: tags.append( { 'building': rel_outer_ways_tags[n]['building']} )
        
        buildingsCount = len(ways)
        #print(buildingsCount)

    # get coords of Ways
    objectGroup = []
    for i, x in enumerate(ways): # go through each Way: 2384
        ids = ways[i]['nodes']
        coords = [] # replace node IDs with actual coords for each Way
        height = 3
        tags[i]['building']: height = 9
        try: height = float( cleanString(tags[i]['levels'].split( ',' )[0].split( ';' )[0] )) * 3
        except:
            try: height = float( cleanString(tags[i]['height'].split( ',' )[0].split( ';' )[0]) )
            except: 
                try: 
                    if tags[i]['layer'] < 0: height = -1 * height
                except: pass
        if height > 150: 
            print(height)
            #height = 10 

        for k, y in enumerate(ids): # go through each node of the Way
            if k==len(ids)-1: continue # ignore last 
            for n, z in enumerate(nodes): # go though all nodes
                if ids[k] == nodes[n]['id']: 
                    x, y = reprojectToCrs(nodes[n]['lat'], nodes[n]['lon'], "EPSG:4326", projectedCrs)
                    coords.append( { 'x': x, 'y': y } )
                    break

        obj = extrudeBuildings( coords, height )
        objectGroup.append( obj )
        coords = None
        height = None   
    return objectGroup

def joinRoads(coords: List[dict], closed: bool,  height: float):
    from specklepy.objects.geometry import Polyline, Point 
    points = []
    
    for i,c in enumerate(coords): 
        points.append(Point.from_list([c['x'], c['y'], 0]))

    poly = Polyline.from_points(points)
    poly.closed = closed
    poly.units = "m"
    return poly


def getRoads(lat: float, lon: float):
    # https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0 
    import requests
    import json
    keyword = "highway"

    projectedCrs = createCRS(lat, lon)
    lonPlus1, latPlus1 = reprojectToCrs(1, 1, projectedCrs, "EPSG:4326")
    scaleX = lonPlus1 - lon
    scaleY = latPlus1 - lat
    r = RADIUS #meters

    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""[out:json];
    (node["{keyword}"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    way["{keyword}"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    relation["{keyword}"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    );out body;>;out skel qt;"""

    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()
    features = data['elements']

    ways = []
    tags = []

    rel_outer_ways = []
    rel_outer_ways_tags = []

    ways_part = []
    nodes = []

    for feature in features:
        # ways
        if feature['type'] == 'way':
            try:
                feature['id']
                feature['nodes']
                
                tags.append( { f'{keyword}': feature['tags'][keyword] } )
                ways.append( { 'id': feature['id'], 'nodes': feature['nodes'] } )
            except:
                ways_part.append( { 'id': feature['id'], 'nodes': feature['nodes'] } )
        
        # relations 
        elif feature['type'] == 'relation':
            outer_ways = []
            outer_ways_tags = { f'{keyword}': feature['tags'][keyword] }
            
            for n, x in enumerate(feature['members']):
                # if several Outer ways, combine them
                if feature['members'][n]['type'] == 'way': # and feature['members'][n]['role'] == 'inner':
                    outer_ways.append( { 'ref': feature['members'][n]['ref'] } )

            rel_outer_ways.append( outer_ways )
            rel_outer_ways_tags.append( outer_ways_tags )
        
        # get nodes (that don't have tags)
        elif feature['type'] == 'node':
            try: 
                feature['tags']
                feature['tags'][keyword]
            except: 
                #if feature['tags'][keyword] != 'traffic_signals':
                nodes.append( { 'id': feature['id'], 'lat': feature['lat'], 'lon': feature['lon'] } )

    # turn relations_OUTER into ways
    for n, x in enumerate(rel_outer_ways):  
        # there will be a list of "ways" in each of rel_outer_ways
        full_node_list = []
        for m, y in enumerate(rel_outer_ways[n]): 
            #find ways_parts with corresponding ID
            for k, z in enumerate(ways_part): 
                if k == len(ways_part): break
                if rel_outer_ways[n][m]['ref'] == ways_part[k]['id']:
                    full_node_list += ways_part[k]['nodes'] 
                    ways_part.pop(k) # remove used ways_parts
                    k -= 1 # reset index
                    break
        
            # move inside the loop to separate the sections
            ways.append( { 'nodes': full_node_list } ) 
            tags.append( { f'{keyword}': rel_outer_ways_tags[n][keyword] } )
            # empty the list after each loop to start new part 
            full_node_list = []
        
        roadsCount = len(ways)
        #print(roadsCount)

    # get coords of Ways
    objectGroup = []
    for i, x in enumerate(ways): # go through each Way: 2384
        ids = ways[i]['nodes']
        coords = [] # replace node IDs with actual coords for each Way
        r'''
        height = 3
        tags[i][keyword]: height = 9
        try: height = float( cleanString(tags[i]['levels'].split( ',' )[0].split( ';' )[0] )) * 3
        except:
            try: height = float( cleanString(tags[i]['height'].split( ',' )[0].split( ';' )[0]) )
            except: 
                try: 
                    if tags[i]['layer'] < 0: height = -1 * height
                except: pass
        if height > 150: 
            print(height)
            #height = 10 
        '''
        closed = False
        for k, y in enumerate(ids): # go through each node of the Way
            if k==len(ids)-1 and y == ids[0]: 
                closed = True
                continue
            for n, z in enumerate(nodes): # go though all nodes
                if ids[k] == nodes[n]['id']: 
                    x, y = reprojectToCrs(nodes[n]['lat'], nodes[n]['lon'], "EPSG:4326", projectedCrs)
                    coords.append( { 'x': x, 'y': y } )
                    break

        obj = joinRoads( coords, closed, 0 )
        objectGroup.append( obj )
        coords = None
        height = None   
    return objectGroup


try:
    import numpy as np 
    projInfo = base["info"] #[o for o in objects if o.speckle_type.endswith("Revit.ProjectInfo")][0] 
    angle_rad = projInfo["locations"][0]["trueNorth"]
    angle_deg = np.rad2deg(angle_rad)
    lon = np.rad2deg(projInfo["longitude"])
    lat = np.rad2deg(projInfo["latitude"])

    #lat = 42.33868845652055
    #lon = -71.08536785916132

    print(angle_rad)
    print(lon)
    print(lat)

    crsObj = None
    commitObj = Collection(elements = [], units = "m", name = "Context", collectionType = "BuildingsLayer")

    blds = getBuildings(lat, lon)
    bases = [Base(units = "m", displayValue = [b]) for b in blds]
    bldObj = Collection(elements = bases, units = "m", name = "Context", collectionType = "BuildingsLayer")
    commitObj.elements.append(bldObj)
    
    roads = getRoads(lat, lon)
    bases = roads
    roadObj = Collection(elements = bases, units = "m", name = "Context", collectionType = "RoadsLayer")
    commitObj.elements.append(roadObj)
    
    # create branch if needed 
    existing_branch = client.branch.get(project_id, RESULT_BRANCH, 1)  
    if existing_branch is None: 
        br_id = client.branch.create(stream_id = project_id, name = RESULT_BRANCH, description = "") 

    objId = send(commitObj, transports=[server_transport]) 

    commit_id = client.commit.create(
                stream_id=project_id,
                object_id=objId,
                branch_name=RESULT_BRANCH,
                message="Sent objects from Automate",
                source_application="Python",
            )
            
except Exception as e: 
    raise e 


