from src.Vector.vector_3 import Vector3
from src.Constants.misc import Default, Color
from src.FileFormats.DLP.dlp import DLP, DLPVertex, DLPPatch, DLPGroup


s_res = 4
t_res = 1
r_opts = 636
dlp_flags = 1289  # 1513
material_index = 0
texture_index = 0
physics_index = 0

dlp_patch_name = ""
dlp_group_name = "BOUND\x00" 

dlp_normals = [
    DLPVertex(0, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE),
    DLPVertex(1, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE),
    DLPVertex(2, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE),
    DLPVertex(3, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE)
    ]

dlp_vertices = [ 
      Vector3(-50.0, 0.0, 80.0),
      Vector3(-140.0, 0.0, 50.0),
      Vector3(-100.0, 0.0, 10.0),
      Vector3(-50.0, 0.0, 30.0)
      ]

dlp_groups = [DLPGroup(dlp_group_name, 0, 2, [], [0, 1])]
               
dlp_patches = [
    DLPPatch(s_res, t_res, dlp_flags, r_opts, material_index, texture_index, physics_index, 
             [dlp_normals[0], dlp_normals[1], dlp_normals[2], dlp_normals[3]], dlp_patch_name),
    DLPPatch(s_res, t_res, dlp_flags, r_opts, material_index, texture_index, physics_index, 
             [dlp_normals[3], dlp_normals[2], dlp_normals[1], dlp_normals[0]], dlp_patch_name)
    ] 