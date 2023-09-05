import numpy as np

def expm(A):
    # https://stackoverflow.com/questions/60797516/difference-between-scipy-linalg-expm-versus-hand-coded-one
    
    eigvalue, eigvectors = np.linalg.eig(A)
    e_Lambda = np.eye(np.size(A, 0))*(np.exp(eigvalue))
    e_A = eigvectors*e_Lambda*eigvectors.I

    return (e_A)
