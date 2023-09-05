

from typing import Union
import numpy as np

from utils.vectors import normalize 

def remapPt( pt: Union[np.array, list], toHorizontal, plane3d ):

    normal3D = np.array( normalize(plane3d["normal"]) )
    #origin3D = np.array(plane3d["origin"])

    if toHorizontal is True: # already 3d 
        n1 = list(normal3D)
        n2 = [0,0,1]
    else: 
        n1 = [0,0,1]
        n2 = list(normal3D)

    mat = rotation_matrix_from_vectors(n1, n2)
    vec1_rot = mat.dot(pt)

    if np.isnan(vec1_rot[0]):
        return pt

    result = vec1_rot
    return result


def rotation_matrix_from_vectors(vec1, vec2):
    # https://stackoverflow.com/questions/45142959/calculate-rotation-matrix-to-align-two-vectors-in-3d-space
    """ Find the rotation matrix that aligns vec1 to vec2
    :param vec1: A 3d "source" vector
    :param vec2: A 3d "destination" vector
    :return mat: A transform matrix (3x3) which when applied to vec1, aligns it with vec2.
    """
    a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
    v = np.cross(a, b)
    c = np.dot(a, b)
    s = np.linalg.norm(v)
    kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    rotation_matrix = np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))

    return rotation_matrix
