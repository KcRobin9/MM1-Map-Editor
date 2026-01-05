from src.constants.file_formats import Anim


animations_data = {
    Anim.PLANE: [               # You can not have multiple Planes or Eltrains
        (450, 30.0, -450),      # You can set any number of coordinates for your path(s)
        (450, 30.0, 450),       
        (-450, 30.0, -450),     
        (-450, 30.0, 450)
        ], 
    Anim.ELTRAIN: [
        (180, 25.0, -180),
        (180, 25.0, 180), 
        (-180, 25.0, -180),
        (-180, 25.0, 180)
        ]
}