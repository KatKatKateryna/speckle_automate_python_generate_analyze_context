
from specklepy.api.operations import receive, send
from specklepy.api.client import SpeckleClient
from specklepy.objects import Base
from specklepy.objects.other import Collection
from specklepy.api.models import Branch 

#from utils.utils_network import calculateAccessibility
from utils.utils_osm import getBuildings, getRoads
from utils.utils_other import RESULT_BRANCH

def run(client, server_transport, base, radius_in_meters): 
    try:

        import numpy as np 
        project_id = server_transport.stream_id
        projInfo = base["info"] #[o for o in objects if o.speckle_type.endswith("Revit.ProjectInfo")][0] 
        
        lon = np.rad2deg(projInfo["longitude"])
        lat = np.rad2deg(projInfo["latitude"])
        angle_deg = 0
        try: 
            angle_rad = projInfo["locations"][0]["trueNorth"]
            angle_deg = np.rad2deg(angle_rad)
        except: pass 

        crsObj = None
        commitObj = Collection(elements = [], units = "m", name = "Context", collectionType = "BuildingsLayer")

        blds = getBuildings(lat, lon, radius_in_meters)
        bases = [Base(units = "m", displayValue = [b]) for b in blds]
        bldObj = Collection(elements = bases, units = "m", name = "Context", collectionType = "BuildingsLayer")
            
        roads, meshes, analysisMeshes = getRoads(lat, lon, radius_in_meters)
        roadObj = Collection(elements = roads, units = "m", name = "Context", collectionType = "RoadsLayer")
        roadMeshObj = Collection(elements = meshes, units = "m", name = "Context", collectionType = "RoadMeshesLayer")
        analysisObj = Collection(elements = analysisMeshes, units = "m", name = "Context", collectionType = "RoadAnalysisLayer")
        
        # create branch if needed 
        existing_branch = client.branch.get(project_id, RESULT_BRANCH, 1)  
        if existing_branch is None: 
            br_id = client.branch.create(stream_id = project_id, name = RESULT_BRANCH, description = "") 

        commitObj.elements.append(base)
        commitObj.elements.append(bldObj)
        commitObj.elements.append(roadObj)
        commitObj.elements.append(roadMeshObj)

        objId = send(commitObj, transports=[server_transport]) 
        commit_id = client.commit.create(
                    stream_id=project_id,
                    object_id=objId,
                    branch_name=RESULT_BRANCH,
                    message="Context from Automate",
                    source_application="Python",
                )
        r'''
        commitObj.elements = []
        commitObj.elements.append(bldObj)
        commitObj.elements.append(analysisObj)

        objId = send(commitObj, transports=[server_transport]) 
        commit_id = client.commit.create(
                    stream_id=project_id,
                    object_id=objId,
                    branch_name=RESULT_BRANCH,
                    message="Space Syntax from Automate",
                    source_application="Python",
                )
        '''
                
    except Exception as e: 
        raise e 


r'''
# TO DEBUG LOCALLY run this file 
from specklepy.transports.server import ServerTransport
from specklepy.api.credentials import get_local_accounts

server_url = "https://latest.speckle.dev/" #"https://speckle.xyz/" # project_data.speckle_server_url
project_id = "4ea6a03993" #project_data.project_id
model_id = "revit models"
radius_in_meters = 300 #float(project_data.radius) 

account = get_local_accounts()[0]
client = SpeckleClient(server_url)
client.authenticate_with_token(account.token)
branch: Branch = client.branch.get(project_id, model_id, 1)

commit = branch.commits.items[0] 
server_transport = ServerTransport(project_id, client)
base = receive(branch.commits.items[0].referencedObject, server_transport)

run(client, server_transport, base, radius_in_meters)
'''