
import math
import random
from typing import List
import numpy as np
from numpy import cross, eye, dot
from numpy.linalg import norm
from operator import add, sub
from specklepy.objects.geometry import Mesh, Point
from utils.vectors import createPlane, normalize 
from utils.convex_shape import remapPt
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from utils.scipy_replacement import expm

def getAllPlanes(mesh: Mesh) -> List[list]:
    meshList = []
    if isinstance(mesh, Mesh):
        i = 0
        fs = mesh.faces
        for count, f in enumerate(fs):
            if i >= len(fs)-1: break
            current_face_index = fs[i]
            pt_list = []
            for x in range(i+1, i+fs[i]+1):
                ind = int(fs[x])
                pt_list.append( [mesh.vertices[3*ind], mesh.vertices[3*ind+1], mesh.vertices[3*ind+2]] )
            meshList.append(pt_list)
            i += fs[i] + 1 
    elif isinstance(mesh, List):
        for m in mesh:
            meshList.extend(getAllPlanes(m))
    return meshList
    
def LinePlaneCollision(planeNormal, planePoint, rayDirection, rayPoint, epsilon=1e-6):
    # https://gist.github.com/TimSC/8c25ca941d614bf48ebba6b473747d72
    ndotu = planeNormal.dot(rayDirection)
    if abs(ndotu) < epsilon:
        #raise RuntimeError("no intersection or line is within plane")
        return None 

    w = rayPoint - planePoint
    si = -planeNormal.dot(w) / ndotu
    Psi = w + si * rayDirection + planePoint
    return Psi

def containsPoint(pt: np.array, mesh: List):
    
    plane3d = createPlane(*mesh[:3])
    vert2d = remapPt(pt, True, plane3d)
    mesh2d = [ remapPt(m, True, plane3d) for m in mesh ]

    point = Point(vert2d[0], vert2d[1])
    polygon = Polygon([ (m[0], m[1]) for m in mesh2d ])
    result = polygon.contains(point)
    return result


def M(axis, theta):
    # https://stackoverflow.com/questions/6802577/rotation-of-3d-vector
    
    return expm(cross(eye(3), axis/norm(axis)*theta))

def rotate_vector(pt_origin, vector, half_angle_degrees=70, step = 10):

    half_angle = np.deg2rad(half_angle_degrees)

    vectors = []
    axis = vector # direction
    #vectors.append( np.array( list( map(add, pt_origin, vector) )) )

    count = int(half_angle_degrees/step) # horizontal expansion 
    for c in range(0, count+1):
        # xy plane
        x = vector[0] * math.cos(half_angle*c/count) - vector[1] * math.sin(half_angle*c/count)
        y = vector[0] * math.sin(half_angle*c/count) + vector[1] * math.cos(half_angle*c/count)
        
        v = [x,y,vector[2]]
        if c==0:
            vectors.append( np.array( list( map(add, pt_origin, v) )) ) 
            continue 
        
        coeff = 1- math.pow( (count+1 - c) / (count+1), 100)
        step2 = int( coeff * (count+1 - c) * step ) 
        if step2 == 0: step2 = 1

        for a in range(0,360,step2): 
            theta = a*math.pi / 180 
            M0 = M(vector, theta)
            newDir = dot(M0,v)
            vectors.append( np.array( list( map(add, pt_origin, newDir) )) ) 

    return vectors

def projectToPolygon(point: List[float], vectors: List[List[float]], usedVectors: dict, m, index):
    
    allIntersections = []

    #meshes = getAllPlanes(mesh)
    #for x, m in enumerate(meshes): 

    pt1, pt2, pt3 = m[:3]
    plane = createPlane(pt1, pt2, pt3)

    #Define plane
    planeNormal = np.array(plane["normal"])
    planePoint = np.array(plane["origin"]) #Any point on the plane

    #Define ray
    for i, direct in enumerate(vectors):
        rayPoint = np.array(point) #Any point along the ray
        dir = np.array(direct) - rayPoint

        # check collision and its direction 
        normalOriginal = normalize( dir )
        collision = LinePlaneCollision(planeNormal, planePoint, dir, rayPoint)
        if collision is None: continue 
        normC = normalize( collision-rayPoint )
        #if int(normalCollision[0]*1000) != int(normalOriginal[0]*1000): 
        compare1 = normalOriginal[0]*normC[0]
        compare2 = normalOriginal[1]*normC[1]
        compare3 = normalOriginal[2]*normC[2]
        if (compare1>=0 and compare2>=0 and compare3>=0): # or (compare1<0 and compare2<0 and compare3<0) : 
            pass 
        else:
            continue # if different direction 

        result = containsPoint(collision, m)

        if result is True:

            pt_intersect = Point.from_list([collision[0], collision[1], collision[2]])
            pt_intersect.vectorId = i
            pt_intersect.meshId = index 
            pt_intersect.distance = np.sqrt(np.sum(( np.array(point) -collision)**2, axis=0))

            allIntersections.append(pt_intersect)

            try: val = usedVectors[i] + 1
            except: val = 1
            usedVectors.update({i:val})

    return allIntersections, usedVectors


def expandPtsList(pt_origin, all_pts, usedVectors, step_original, all_geom, mesh_nearby):

    new_pts = []
    #
    half_angle_degrees = step_original/2
    if half_angle_degrees ==0: half_angle_degrees = 1
    if half_angle_degrees == step_original:
        return
    half_angle = np.deg2rad(half_angle_degrees)

    for i, ptSpeckle in enumerate(all_pts):
        vectors = []
        pt = [ptSpeckle.x, ptSpeckle.y, ptSpeckle.z]
        vector =  np.array( list(map(sub, pt, pt_origin)) ) # direction
        # xy plane
        x = vector[0] * math.cos(half_angle) - vector[1] * math.sin(half_angle)
        y = vector[0] * math.sin(half_angle) + vector[1] * math.cos(half_angle)
        
        v = [x,y,vector[2]]
        axis = vector
        
        ran = random.randint(0,10)
        for a in range(ran,360+ran,60): 
            theta = a*math.pi / 180 
            M0 = M(axis, theta)
            newDir = dot(M0,v)
            vectors.append( np.array( list( map(add, pt_origin, newDir) )) ) 
    
        # project rays 
        count = 0
        for mesh in all_geom:
            if count in ([ptSpeckle.meshId] + mesh_nearby[i]):  
                pts, usedVectors = projectToPolygon(pt_origin, vectors, {}, mesh, count) #Mesh.create(vertices = [0,0,0,5,0,0,5,19,0,0,14,0], faces=[4,0,1,2,3]))
                new_pts.extend( pts )
            count +=1
        #break
    return new_pts, usedVectors


