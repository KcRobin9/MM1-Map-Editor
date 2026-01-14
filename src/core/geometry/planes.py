import numpy as np
from typing import List

from src.core.vector.vector_3 import Vector3
from src.constants.misc import Shape, Default


def ensure_ccw_order(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    vertex_1, vertex_2, vertex_3 = vertex_coordinates
    
    normal = compute_normal(vertex_1, vertex_2, vertex_3)
    reference_up = np.array([0, 1, 0])
    
    dot_product = np.dot(normal, reference_up)
    
    if dot_product < 0: # Clockwise --> swap the order of the vertices
        return [vertex_1, vertex_3, vertex_2]
    else:               # Counterclockwise --> no changes needed
        return [vertex_1, vertex_2, vertex_3]
    
    
def compute_normal(vertex_1: Vector3, vertex_2: Vector3, vertex_3: Vector3) -> np.ndarray:
    v1 = np.array(vertex_2) - np.array(vertex_1)
    v2 = np.array(vertex_3) - np.array(vertex_1)
    normal = np.cross(v1, v2)
    return normal / np.linalg.norm(normal)


def ensure_quad_ccw_order(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    normal = compute_normal(*vertex_coordinates[:3])
    
    # Use Gram-Schmidt process to get two orthogonal vectors on the plane
    basis_1 = np.array(vertex_coordinates[1]) - np.array(vertex_coordinates[0])
    basis_1 -= np.dot(basis_1, normal) * normal
    basis_1 /= np.linalg.norm(basis_1)
    basis_2 = np.cross(normal, basis_1)

    # Project vertices onto the plane defined by the normal
    projections = [
        (np.dot(vertex, basis_1), np.dot(vertex, basis_2))
        for vertex in vertex_coordinates
        ]

    # Compute the centroid of the projected points
    centroid = np.mean(projections, axis = 0)
    
    # Compute angles of vertices relative to centroid
    delta = np.array(projections) - centroid
    angles = np.arctan2(delta[:, 1], delta[:, 0])
    
    # Sort vertices based on these angles
    sorted_indices = np.argsort(angles)
    
    return [vertex_coordinates[i] for i in sorted_indices]


def compute_plane_edgenormals(vertex_1: Vector3, vertex_2: Vector3, vertex_3: Vector3):     
    plane_normal = compute_normal(vertex_1, vertex_2, vertex_3)
    
    plane_distance = -np.dot(plane_normal, vertex_1)

    plane_normal = np.round(plane_normal, 3)
    plane_distance = round(plane_distance, 3)

    return plane_normal, plane_distance


def compute_edges(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    vertices = [np.array([vertex[0], 0, vertex[2]]) for vertex in vertex_coordinates]
    plane_normal, _ = compute_plane_edgenormals(*vertices[:3]) 

    num_verts = len(vertices)  
        
    plane_edges = []

    abs_plane_x = abs(plane_normal[0])
    abs_plane_y = abs(plane_normal[1])
    abs_plane_z = abs(plane_normal[2])

    negate = 1.0

    # TODO: Refactor
    if abs_plane_x < abs_plane_y or abs_plane_x < abs_plane_z:
        if abs_plane_y < abs_plane_x or abs_plane_y < abs_plane_z:
            if plane_normal[2] < 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[1] * negate, D[0] * negate, -np.dot([-D[1], D[0]], [A[0], A[1]])]))
        else:
            if plane_normal[1] > 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[2] * negate, D[0] * negate, -np.dot([-D[2], D[0]], [A[0], A[2]])]))
    else:
        if plane_normal[0] < 0.0:
            negate = -1.0
        for i in range(num_verts):
            A = vertices[i]
            B = vertices[(i+1) % num_verts]
            D = B - A
            plane_edges.append(np.array([-D[2] * negate, D[1] * negate, -np.dot([-D[2], D[1]], [A[1], A[2]])]))

    # Normalize edges
    for i in range(len(plane_edges)):
        norm_val = np.linalg.norm(plane_edges[i][:2])  # Only first two components
        plane_edges[i][:2] /= norm_val
        plane_edges[i][2] /= norm_val
        
    edges = [Vector3(edge[0], edge[1], edge[2]) for edge in plane_edges]
    
    # All shapes must always have 4 vectors
    if len(vertices) == Shape.TRIANGLE:
        edges.append(Default.VECTOR_3)
    
    return edges