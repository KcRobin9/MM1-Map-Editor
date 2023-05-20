def moronville(x):
    """
    =====================================================================
    ==================== Midtown Madness 1 Moronville ===================
    
    This is the script input data for the city Moronville in Midtown 
    Madness 1 that was made by Dading. 
    
    Hopefully this gives some insight of how to make your own City.
    
    Feel free to extend or modify the map, or use parts of it in your 
    own city.
    =====================================================================
    """
           
# Polygon 1 | BND floor
create_and_append_polygon(
    bound_number = 1,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),
        (-10, 15.0, -80),	
        (-80, 15.0, -80),
        (-80, 15.0, -10)])

# Polygon 1 | Texture
generate_and_save_bms_file(
    string_names = ["T_WALL"])

        # Polygon 2 | BND WALL1 1
create_and_append_polygon(
    bound_number = 2,
    material_index = 0,
    vertex_coordinates=[
        (-80, 35.0, -79.9),	
        (-80, 15.0, -80),
        (-10, 15.0, -80),
        (-10, 35.0, -79.9)], wall_side="outside")      

    # Generate BMS for Polygon 2 WALL1 1
generate_and_save_bms_file(
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0]) 
 
        # Polygon 3 | BND WALL1 2
create_and_append_polygon(
    bound_number = 3,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),		
        (-10.1, 35.0, -10),
        (-10.1, 35.0, -80),
        (-10, 15.0, -80)], wall_side="inside")

generate_and_save_bms_file( 
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0])     
    
  
        # Polygon 4 | BND WALL1 3
create_and_append_polygon(
    bound_number = 4,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, -10),		
        (-80, 35.0, -10.1),
        (-10, 35.0, -10.1),
        (-10, 15.0, -10)],wall_side="inside")
    
    # Generate BMS for Polygon 4 WALL1 3
generate_and_save_bms_file(
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0])         
    
        # Polygon 5 | BND WALL1 4
create_and_append_polygon(
    bound_number = 5,
    material_index = 0,
    vertex_coordinates=[
        (-79.9, 35.0, -80),		
        (-80, 15.0, -80),
        (-80, 15.0, -10),
        (-79.9, 35.0, -10)],wall_side="outside")
    
    # Generate BMS for Polygon 5 WALL1 4
generate_and_save_bms_file( 
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0])     
    
        # Polygon 12 | BND road floor
create_and_append_polygon(
    bound_number = 12,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -10),
        (40, 15.0, -80),	
        (80, 15.0, -80),
        (80, 15.0, -10)])
    
    # Generate BMS for Polygon 12
generate_and_save_bms_file(
    string_names = ["T_WALL"])   

        # Polygon 13 | BND WALL2 1
create_and_append_polygon(
    bound_number = 13,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -80),
        (40, 25.0, -79.9),
        (80, 25.0, -79.9),
        (80, 15.0, -80)], wall_side="outside")
    
    # Generate BMS for Polygon 13 WALL2 1
generate_and_save_bms_file(
    string_names=["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=5,repeat_y=5))

        # Polygon 14 | BND WALL2 2
create_and_append_polygon(
    bound_number = 14,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),
        (79.9, 25.0, -80),
        (79.9, 25.0, -10),
        (80, 15.0, -10)], wall_side="inside")
    
    # Generate BMS for Polygon 14 WALL2 2
generate_and_save_bms_file(
    string_names = ["IND_WALL"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 15 | BND WALL2 3
create_and_append_polygon(
    bound_number = 15,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -10),
        (40, 25.0, -10.1),
        (80, 25.0, -10.1),
        (80, 15.0, -10)],wall_side="inside")
    
    # Generate BMS for Polygon 15 WALL2 3
generate_and_save_bms_file(
    string_names=["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=5,repeat_y=5))

        # Polygon 16 | BND WALL2 4
create_and_append_polygon(
    bound_number = 16,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -10),
        (40.1, 25.0, -10),
        (40.1, 25.0, -80),
        (40, 15.0, -80)], wall_side="outside")
    
    # Generate BMS for Polygon 16 WALL2 4
generate_and_save_bms_file(
    string_names=["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal",repeat_x=5,repeat_y=5))

    # Polygon 21 | BND floor
create_and_append_polygon(
    bound_number = 21,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),		
        (10, 15.0, 40),
        (80, 15.0, 40),
        (80, 15.0, 10)])
    
    # Generate BMS for Polygon 21 floor
generate_and_save_bms_file(
    string_names = ["T_WALL"])        

        # Polygon 22 | BND WALL3 1
create_and_append_polygon(
    bound_number = 22,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),
        (10, 25.0, 10.1),
        (80, 25.0, 10.1),
        (80, 15.0, 10)], wall_side="outside")
    
    # Generate BMS for Polygon 22 WALL3 1
generate_and_save_bms_file(
    string_names=["OT_BAR_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 23 | BND WALL3 2
create_and_append_polygon(
    bound_number = 23,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 40),
        (79.9, 25.0, 40),
        (79.9, 25.0, 10),
        (80, 15.0, 10)], wall_side="inside")
    
    # Generate BMS for Polygon 23 WALL3 2
generate_and_save_bms_file(
    string_names = ["OT_BAR_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 24 | BND WALL3 3
create_and_append_polygon(
    bound_number = 24,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 40),
        (10, 25.0, 39.9),
        (80, 25.0, 39.9),
        (80, 15.0, 40)], wall_side="inside")
    
    # Generate BMS for Polygon 24 WALL3 3
generate_and_save_bms_file(
    string_names=["OT_BAR_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 25 | BND WALL3 4
create_and_append_polygon(
    bound_number = 25,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),
        (10.1, 25.0, 10),
        (10.1, 25.0, 40),
        (10, 15.0, 40)], wall_side="outside")
    
    # Generate BMS for Polygon 25 WALL3 4
generate_and_save_bms_file(
    string_names = ["OT_BAR_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 26 | BND
create_and_append_polygon(
    bound_number = 26,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 40),		
        (10, 15.0, 50),
        (80, 15.0, 50),
        (80, 15.0, 40)])
    
    # Generate BMS for Polygon 26
generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="horizontal"))

    # Polygon 27 | BND floor
create_and_append_polygon(
    bound_number = 27,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 50),		
        (10, 15.0, 80),
        (80, 15.0, 80),
        (80, 15.0, 50)])
    
    # Generate BMS for Polygon 27 floor
generate_and_save_bms_file(
    string_names = ["T_WALL"])  

        # Polygon 28 | BND WALL4 1
create_and_append_polygon(
    bound_number = 28,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 50),
        (10, 25.0, 50.1),
        (80, 25.0, 50.1),
        (80, 15.0, 50)], wall_side="outside")
    
    # Generate BMS for Polygon 28 WALL4 1
generate_and_save_bms_file(
    string_names=["CT_SHOP_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 29| BND WALL4 2
create_and_append_polygon(
    bound_number = 29,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 50),
        (79.9, 25.0, 50),
        (79.9, 25.0, 80),
        (80, 15.0, 80)], wall_side="inside")
    
    # Generate BMS for Polygon 29 WALL4 2
generate_and_save_bms_file(
    string_names = ["CT_SHOP_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 30| BND WALL4 3
create_and_append_polygon(
    bound_number = 30,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 80),
        (80, 25.0, 79.9),
        (10, 25.0, 79.9),
        (10, 15.0, 80)], wall_side="inside")
    
    # Generate BMS for Polygon 30 WALL4 3
generate_and_save_bms_file(
    string_names=["CT_SHOP_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 31| BND WALL4 4
create_and_append_polygon(
    bound_number = 31,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 80),
        (10.1, 25.0, 80),
        (10.1, 25.0, 50),
        (10, 15.0, 50)], wall_side="outside")
    
    # Generate BMS for Polygon 31 WALL4 4
generate_and_save_bms_file(
    string_names = ["CT_SHOP_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 50 | BND
create_and_append_polygon(
    bound_number = 50,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),		
        (-10, 15.0, 80),
        (-80, 15.0, 80),
        (-80, 15.0, 10)])
    
    # Generate BMS for Polygon 50
generate_and_save_bms_file(
    string_names = ["T_WALL"])      

        # Polygon 6 | BND spawn
create_and_append_polygon(
    bound_number = 6,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),
        (-10, 15.0, 10),	
        (10, 15.0, 10),
        (10, 15.0, -10)])
    
    # Generate BMS for Polygon 6 spawn
generate_and_save_bms_file(
    string_names=["Rinter"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="horizontal"))
     
    # Polygon 7 | BND
create_and_append_polygon(
    bound_number = 7,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),
        (-10, 15.0, -80),	
        (10, 15.0, -80),
        (10, 15.0, -10)])
    
    # Generate BMS for Polygon 7
generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="horizontal"))

        # Polygon 8 | BND
create_and_append_polygon(
    bound_number = 8,
    material_index = 87,
    vertex_coordinates=[
        (10, 15.0, -10),
        (10, 15.0, -80),	
        (40, 15.0, -80),
        (40, 15.0, -10)])
    
    # Generate BMS for Polygon 8
generate_and_save_bms_file(
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])       

# Polygon 9 | BND
create_and_append_polygon(
    bound_number = 9,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),              
        (-80, 15.0, -80),		
        (-80, 15.0, -90),
        (80, 15.0, -90)])
    
    # Generate BMS for Polygon 9
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal_flipped",repeat_x=7,repeat_y=1))


    # Polygon 10 | BND
create_and_append_polygon(
    bound_number = 10,
    material_index = 87,
    vertex_coordinates=[
        (90, 15.0, -90),              
        (90, 4.0, -115),		
        (-90, 4.0, -115),
        (-90, 15.0, -90)], corners=[0.0, 1.0, -0.44, -54.6])
    
    # Generate BMS for Polygon 10
generate_and_save_bms_file(
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])
    
    # Polygon 11 | BND 
create_and_append_polygon(
    bound_number = 11,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, -115),		
        (-115, 4.0, -115),
        (-115, 4.0, -500),
        (115, 4.0, -500)])
    
    # Generate BMS for Polygon 11
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])     
    
# Polygon 17 | BND
create_and_append_polygon(
    bound_number = 17,
    material_index = 0,
    base_vertex_index=len(vertices),
    vertex_coordinates=[
        (10, 15.0, -10),
        (80, 15.0, -10),
        (80, 15.0, 10),
        (10, 15.0, 10)])

    # Generate BMS for Polygon 17
generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="vertical"))

    # Polygon 18 | BND
create_and_append_polygon(
    bound_number = 18,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),		
        (80, 15.0, 80),
        (90, 15.0, 80),
        (90, 15.0, -80)])
    
    # Generate BMS for Polygon 18
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=1,repeat_y=7))

    # Polygon 19 | BND
create_and_append_polygon(
    bound_number = 19,
    material_index = 87,
    vertex_coordinates=[
        (90, 15.0, 90),		
        (115, 4.0, 90),
        (115, 4.0, -90),
        (90, 15.0, -90)],corners=[0.44, 1, 0.0, -54.6])
    
    # Generate BMS for Polygon 19
generate_and_save_bms_file(
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])     

    # Polygon 20 | BND 
create_and_append_polygon(
    bound_number = 20,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, 115),		
        (115, 4.0, -115),
        (500, 4.0, -115),
        (500, 4.0, 115)])
    
    # Generate BMS for Polygon 20
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])     

    # Polygon 32 | BND
create_and_append_polygon(
    bound_number = 32,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),		
        (-10, 15.0, 10),
        (-10, 15.0, 80),
        (10, 15.0, 80)])
    
    # Generate BMS for Polygon 32
generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="horizontal"))        
    
     # Polygon 47 | BND
create_and_append_polygon(
    bound_number = 47,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 80),		
        (80, 15.0, 90),
        (-80, 15.0, 90),
        (-80, 15.0, 80),])
    
    # Generate BMS for Polygon 47
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal",repeat_x=7,repeat_y=1))

     # Polygon 48 | BND
create_and_append_polygon(
    bound_number = 48,
    material_index = 0,
    vertex_coordinates=[
        (-90, 15.0, 90),
        (-90, 4.0, 115),
        (90, 4.0, 115),
        (90, 15.0, 90)], corners=[0.0, 1.0, 0.44, -54.6])
    
    # Generate BMS for Polygon 48
generate_and_save_bms_file( 
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])   

    # Polygon 49 | BND
create_and_append_polygon(
    bound_number = 49,
    material_index = 91,
    vertex_coordinates=[
        (-115, 4.0, 115),		
        (-115, 4.0, 500),
        (115, 4.0, 500),
        (115, 4.0, 115)])
    
    # Generate BMS for Polygon 49
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

# Polygon 33 | BND
create_and_append_polygon(
    bound_number = 33,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),		
        (-10, 15.0, -10),
        (-80, 15.0, -10),
        (-80, 15.0, 10),])

    # Generate BMS for Polygon 33
generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="horizontal"))

        # Polygon 35| BND WALL5 1
create_and_append_polygon(
    bound_number = 35,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),
        (-10, 40.0, 10.1),
        (-40, 40.0, 10.1),
        (-40, 15.0, 10)], wall_side="outside")
    
    # Generate BMS for Polygon 35 WALL5 1
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 36| BND WALL5 2
create_and_append_polygon(
    bound_number = 36,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),
        (-10.1, 40.0, 10),
        (-10.1, 40.0, 40),
        (-10, 15.0, 40)],wall_side="inside")
    
    # Generate BMS for Polygon 36 WALL5 2
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 37| BND WALL5 3
create_and_append_polygon(
    bound_number = 37,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 40),
        (-10, 40.0, 39.9),
        (-40, 40.0, 39.9),
        (-40, 15.0, 40)],wall_side="inside")
    
    # Generate BMS for Polygon 37 WALL5 3
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 38| BND WALL5 4
create_and_append_polygon(
    bound_number = 38,
    material_index = 0,
    vertex_coordinates=[
        (-40, 15.0, 10),
        (-39.9, 40.0, 10),
        (-39.9, 40.0, 40),
        (-40, 15.0, 40)],wall_side="outside")
    
    # Generate BMS for Polygon 38 WALL5 4
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 43| BND WALL7 1
create_and_append_polygon(
    bound_number = 43,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 50),
        (-10, 40.0, 50.1),
        (-50, 40.0, 50.1),
        (-50, 15.0, 50)],wall_side="outside")
    
    # Generate BMS for Polygon 43 WALL7 1
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 44| BND WALL7 2
create_and_append_polygon(
    bound_number = 44,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 80),
        (-10.1, 40.0, 80),
        (-10.1, 40.0, 50),
        (-10, 15.0, 50)],wall_side="inside")
    
    # Generate BMS for Polygon 44 WALL7 2
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 45| BND WALL7 3
create_and_append_polygon(
    bound_number = 45,
    material_index = 0,
    vertex_coordinates=[
        (-50, 15.0, 80),
        (-50, 40.0, 79.9),
        (-10, 40.0, 79.9),
        (-10, 15.0, 80)],wall_side="inside")
    
    # Generate BMS for Polygon 45 WALL7 3
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 51 | BND WALL6 1
create_and_append_polygon(
    bound_number = 51,
    material_index = 0,
    vertex_coordinates=[
        (-50, 15.0, 10),		
        (-50, 35.0, 10.1),
        (-80, 35.0, 10.1),
        (-80, 15.0, 10)],wall_side="outside")
    
    # Generate BMS for Polygon 51 WALL6 1
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])     

        # Polygon 52 | BND WALL6 2
create_and_append_polygon(
    bound_number = 52,
    material_index = 0,
    vertex_coordinates=[
        (-50, 15.0, 80),		
        (-50.1, 35.0, 80),
        (-50.1, 35.0, 10.),
        (-50, 15.0, 10)],wall_side="inside")
    
    # Generate BMS for Polygon 52 WALL6 2
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

        # Polygon 53 | BND WALL6 3
create_and_append_polygon(
    bound_number = 53,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, 80),		
        (-80, 35.0, 79.9),
        (-50, 35.0, 79.9),
        (-50, 15.0, 80)],wall_side="inside")
    
    # Generate BMS for Polygon 53 WALL6 3
generate_and_save_bms_file( 
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

        # Polygon 54 | BND WALL6 4
create_and_append_polygon(
    bound_number = 54,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, 10),		
        (-79.9, 35.0, 10),
        (-79.9, 35.0, 80),
        (-80, 15.0, 80)],wall_side="outside")
    
    # Generate BMS for Polygon 54 WALL6 4
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 55 | BND
create_and_append_polygon(
    bound_number = 55,
    material_index = 0,
    vertex_coordinates=[
        (-90, 15.0, 80),		
        (-80, 15.0, -80),
        (-80, 15.0, 80),
        (-90, 15.0, -80)])
    
    # Generate BMS for Polygon 55
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical_flipped",repeat_x=1,repeat_y=7))

        # Polygon 56 | BND
create_and_append_polygon(
    bound_number = 56,
    material_index = 87,
    vertex_coordinates=[
        (-90, 15.0, 90),	
        (-115, 4.0, 90),
        (-115, 4.0, -90),
        (-90, 15.0, -90)],corners=[-0.44, 1, 0.0, -54.6])
    
    # Generate BMS for Polygon 56
generate_and_save_bms_file(
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])

        # Polygon 57 | BND
create_and_append_polygon(
    bound_number = 57,
    material_index = 91,
    vertex_coordinates=[
        (-115, 4.0, -115),	
        (-115, 4.0, 115),
        (-500, 4.0, 115),
        (-500, 4.0, -115)])
    
    # Generate BMS for Polygon 57
generate_and_save_bms_file( 
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])

    # Polygon 58 | BND
create_and_append_polygon(
    bound_number = 58,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),		
        (90, 15.0, -80),
        (90, 15.0, -90),
        (80, 15.0, -90)])
    
    # Generate BMS for Polygon 58
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(0,-45)))
         
    # Polygon 59 | BND
create_and_append_polygon(
    bound_number = 59,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 80),		
        (80, 15.0, 90),
        (90, 15.0, 90),
        (90, 15.0, 80)])
    
    # Generate BMS for Polygon 59
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(0,90)))      

        # Polygon 60 | BND
create_and_append_polygon(
    bound_number = 60,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, 80),		
        (-90, 15.0, 80),
        (-90, 15.0, 90),
        (-80, 15.0, 90)])
    
    # Generate BMS for Polygon 60
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(-90,-45)))    

        # Polygon 61 | BND
create_and_append_polygon(
    bound_number = 61,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, -80),	
        (-90, 15.0, -80),
        (-90, 15.0, -90),
        (-80, 15.0, -90)])
    
    # Generate BMS for Polygon 61
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(0,135)))      
         
        # Polygon 39 | BND
create_and_append_polygon(
    bound_number = 39,
    material_index = 0,
    vertex_coordinates=[
        (-40, 15.0, 10),		
        (-50, 15.0, 10),
        (-50, 25.0, 40),
        (-40, 25.0, 40)],corners=[0.0, 1.0, -0.33, -11.8])
      
    # Generate BMS for Polygon 39
generate_and_save_bms_file( 
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,10,0,0,10,10,10,0]) 
    
        # Polygon 40 | BND
create_and_append_polygon(
    bound_number = 40,
    material_index = 0,
    vertex_coordinates=[
        (-50, 25.0, 40),		
        (-25, 25.0, 40),
        (-50, 25.0, 50),
        (-25, 25.0, 50)])
    
    # Generate BMS for Polygon 40
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,10,0,0,10,10,10,0])    
    
# Polygon 41 | BND
create_and_append_polygon(
    bound_number = 41,
    material_index = 0,
    vertex_coordinates=[
        (-25, 25.0, 40),		
        (-25, 25.0, 50),
        (-10, 30.0, 50),
        (-10, 30.0, 40)],corners=[-0.33, 1.0, 0.0, -33.2])
    
    # Generate BMS for Polygon 41
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,10,0,0,10,10,10,0])   

        # Polygon 34 | BND
create_and_append_polygon(
    bound_number = 34,
    material_index = 0,
    vertex_coordinates=[
        (-10.01, 30.0, 40),		
        (-10.0, 15.0, 40),
        (-10.0, 15.0, 50),
        (-10.01, 30.0, 50)],wall_side="inside")
    
    # Generate BMS for Polygon 34
generate_and_save_bms_file(
    string_names=["R_BLDG1_DOOR_01"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="vertical")) 

    # Polygon 99 | BND | N ew Rooftop
create_and_append_polygon(
    bound_number = 99,
    material_index = 0,
    vertex_coordinates=[
        (10, 25.0, 40),		
        (10, 25.0, 50),
        (80, 25.0, 50),
        (80, 25.0, 40)])
    
    # Generate BMS for Polygon 99
generate_and_save_bms_file( 
    string_names = ["EXPLOSION"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,10,0,0,10,10,10,0])

    # Polygon 90 | BND | Water Missing Part 1
create_and_append_polygon(
    bound_number = 90,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, 500),		
        (500, 4.0, 500),
        (500, 4.0, 115),
        (115, 4.0, 115)])
    
    # Generate BMS for Polygon 90
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 91 | BND | Water Missing Part 2
create_and_append_polygon(
    bound_number = 91,
    material_index = 91,
    vertex_coordinates=[
        (-115, 4.0, -500),		
        (-500, 4.0, -500),
        (-500, 4.0, -115),
        (-115, 4.0, -115)])
    
    # Generate BMS for Polygon 91
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 92 | BND | Water Missing Part 3
create_and_append_polygon(
    bound_number = 92,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, -115),		
        (115, 4.0, -500),
        (500, 4.0, -500),
        (500, 4.0, -115)])
    
    # Generate BMS for Polygon 92
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 93 | BND | Water Missing Part 4
create_and_append_polygon(
    bound_number = 93,
    material_index = 91,
    vertex_coordinates=[
         (-115, 4.0, 115),                 
         (-115, 4.0, 500),                 
         (-500, 4.0, 500),                 
         (-500, 4.0, 115)]), 

    # Generate BMS for Polygon 93
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

# Polygon 991 | BND floor roof
create_and_append_polygon(
    bound_number = 991,
    material_index = 0,
    vertex_coordinates=[
        (-10, 35.0, -10),
        (-10, 35.0, -80),	
        (-80, 35.0, -80),
        (-80, 35.0, -10)])

# Polygon 991 | Texture roof
generate_and_save_bms_file(
    string_names = ["T_WOOD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=7,repeat_y=7)) 

        # Polygon 992 | BND road floor roof
create_and_append_polygon(
    bound_number = 992,
    material_index = 0,
    vertex_coordinates=[
        (40, 25.0, -10),
        (40, 25.0, -80),	
        (80, 25.0, -80),
        (80, 25.0, -10)])
    
    # Generate BMS for Polygon 992 roof
generate_and_save_bms_file(
    string_names = ["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=4,repeat_y=7))   

    # Polygon 993 | BND floor roof
create_and_append_polygon(
    bound_number = 993,
    material_index = 0,
    vertex_coordinates=[
        (10, 25.0, 10),		
        (10, 25.0, 40),
        (80, 25.0, 40),
        (80, 25.0, 10)])
    
    # Generate BMS for Polygon 993 floor roof
generate_and_save_bms_file(
    string_names = ["OT_BAR_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=7,repeat_y=3))  

    # Polygon 994 | BND floor roof
create_and_append_polygon(
    bound_number = 994,
    material_index = 0,
    vertex_coordinates=[
        (10, 25.0, 50),		
        (10, 25.0, 80),
        (80, 25.0, 80),
        (80, 25.0, 50)])
    
    # Generate BMS for Polygon 994 floor roof
generate_and_save_bms_file(
    string_names = ["CT_SHOP_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=7,repeat_y=3))  

    # Polygon 995 | BND floor roof
create_and_append_polygon(
    bound_number = 995,
    material_index = 0,
    vertex_coordinates=[
        (-10, 40.0, 10),		
        (-40, 40.0, 10),
        (-40, 40.0, 40),
        (-10, 40.0, 40)])
    
    # Generate BMS for Polygon 995 floor roof
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=3,repeat_y=3))   

    # Polygon 996 | BND floor roof
create_and_append_polygon(
    bound_number = 996,
    material_index = 0,
    vertex_coordinates=[
        (-10, 40.0, 50),		
        (-50, 40.0, 50),
        (-50, 40.0, 80),
        (-10, 40.0, 80)])
    
    # Generate BMS for Polygon 996 floor roof
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=4,repeat_y=3))   

    # Polygon 997 | BND floor roof
create_and_append_polygon(
    bound_number = 997,
    material_index = 0,
    vertex_coordinates=[
        (-50, 35.0, 80),		
        (-80, 35.0, 80),
        (-80, 35.0, 10),
        (-50, 35.0, 10)])
    
    # Generate BMS for Polygon 997 floor roof
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=3,repeat_y=7))   

# Polygon 999 BND Garage
create_and_append_polygon(
    bound_number=999,
    material_index=0,
    vertex_coordinates=[
        (90,0,-90),
        (90,0,90),
        (-90,0,90),
        (-90,0,-90)]),

generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1], TexCoords=generate_tex_coords(mode="horizontal"))  

# Polygon 998 BND Garage HILL
create_and_append_polygon(
    bound_number=998,
    material_index=0,
    vertex_coordinates=[
        (-10,-0.5,-10),
        (-10,15,-60),
        (10,15,-60),
        (10,-0.5,-10)],corners=[0.0, 1, 0.297, 3])

generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1], TexCoords=generate_tex_coords(mode="horizontal"))  
 
 
################################################################################################################               
################################################################################################################