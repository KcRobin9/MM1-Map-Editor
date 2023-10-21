############################
###### Made by Dading ######
############################

# Updated by me


# Polygon 1 | BND floor
create_polygon(
    bound_number = 1, 
    vertex_coordinates = [
        (-10, 15.0, -10), 
        (-10, 15.0, -80), 	
        (-80, 15.0, -80), 
        (-80, 15.0, -10)])

# Polygon 1 | Texture
save_bms(
    texture_name = ["T_WALL"])

# Polygon 2 | BND WALL1 1
create_polygon(
    bound_number = 2, 
    vertex_coordinates = [
        (-10, 35.0, -79.99), 	
        (-10, 15.0, -80), 
        (-80, 15.0, -80), 
        (-80, 35.0, -79.99)], wall_side = "outside")      

# Generate BMS for Polygon 2 WALL1 1
save_bms(
    texture_name = ["T_WOOD"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, 0, 5, 5, 5, 0]) 
 
# Polygon 3 | BND WALL1 2
create_polygon(
    bound_number = 3, 
    vertex_coordinates = [
        (-10, 15.0, -80), 		
        (-10.01, 35.0, -80), 
        (-10.01, 35.0, -10), 
        (-10, 15.0, -10)], wall_side = "inside")

save_bms( 
    texture_name = ["T_WOOD"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, 0, 5, 5, 5, 0])     
    
# Polygon 4 | BND WALL1 3
create_polygon(
    bound_number = 4, 
    vertex_coordinates = [
        (-10, 15.0, -10), 		
        (-10, 35.0, -10.01), 
        (-80, 35.0, -10.01), 
        (-80, 15.0, -10)], wall_side = "inside")
    
# Generate BMS for Polygon 4 WALL1 3
save_bms(
    texture_name = ["T_WOOD"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, 0, 5, 5, 5, 0])         
    
# Polygon 5 | BND WALL1 4
create_polygon(
    bound_number = 5, 
    vertex_coordinates = [
        (-79.99, 35.0, -80), 		
        (-80, 15.0, -80), 
        (-80, 15.0, -10), 
        (-79.99, 35.0, -10)], wall_side = "outside")
    
# Generate BMS for Polygon 5 WALL1 4
save_bms( 
    texture_name = ["T_WOOD"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, 0, 5, 5, 5, 0])     
    
# Polygon 12 | BND road floor
create_polygon(
    bound_number = 12, 
    vertex_coordinates = [
        (80, 15.0, -10), 
        (80, 15.0, -80), 	
        (40, 15.0, -80), 
        (40, 15.0, -10)])
    
# Generate BMS for Polygon 12
save_bms(
    texture_name = ["T_WALL"])   

# Polygon 13 | BND WALL2 1
create_polygon(
    bound_number = 13, 
    vertex_coordinates = [
        (40, 15.0, -80), 
        (40, 25.0, -79.99), 
        (80, 25.0, -79.99), 
        (80, 15.0, -80)], wall_side = "outside")
    
# Generate BMS for Polygon 13 WALL2 1
save_bms(
    texture_name = ["IND_WALL"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 13, mode = "repeating_vertical", tile_x = 5, tile_y = 5))

# Polygon 14 | BND WALL2 2
create_polygon(
    bound_number = 14, 
    vertex_coordinates = [
        (80, 15.0, -80), 
        (79.99, 25.0, -80), 
        (79.99, 25.0, -10), 
        (80, 15.0, -10)], wall_side = "inside")
    
# Generate BMS for Polygon 14 WALL2 2
save_bms(
    texture_name = ["IND_WALL"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 15 | BND WALL2 3
create_polygon(
    bound_number = 15, 
    vertex_coordinates = [
        (80, 15.0, -10), 
        (80, 25.0, -10.01), 
        (40, 25.0, -10.01), 
        (40, 15.0, -10)], wall_side = "inside")
    
# Generate BMS for Polygon 15 WALL2 3
save_bms(
    texture_name = ["IND_WALL"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 15, mode = "repeating_vertical", tile_x = 5, tile_y = 5))

# Polygon 16 | BND WALL2 4
create_polygon(
    bound_number = 16, 
    vertex_coordinates = [
        (40, 15.0, -10), 
        (40.01, 25.0, -10), 
        (40.01, 25.0, -80), 
        (40, 15.0, -80)], wall_side = "outside")
    
# Generate BMS for Polygon 16 WALL2 4
save_bms(
    texture_name = ["IND_WALL"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 16, mode = "repeating_horizontal", tile_x = 5, tile_y = 5))

# Polygon 21 | BND floor
create_polygon(
    bound_number = 21, 
    vertex_coordinates = [
        (10, 15.0, 10), 		
        (10, 15.0, 40), 
        (80, 15.0, 40), 
        (80, 15.0, 10)])
    
# Generate BMS for Polygon 21 floor
save_bms(
    texture_name = ["T_WALL"])        

# Polygon 22 | BND WALL3 1
create_polygon(
    bound_number = 22, 
    vertex_coordinates = [
        (10, 15.0, 10), 
        (10, 25.0, 10.01), 
        (80, 25.0, 10.01), 
        (80, 15.0, 10)], wall_side = "outside")
    
# Generate BMS for Polygon 22 WALL3 1
save_bms(
    texture_name = ["OT_BAR_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 22, mode = "repeating_vertical", tile_x = 12, tile_y = 5))

# Polygon 23 | BND WALL3 2
create_polygon(
    bound_number = 23, 
    vertex_coordinates = [
        (80, 15.0, 10), 
        (79.99, 25.0, 10), 
        (79.99, 25.0, 40), 
        (80, 15.0, 40)], wall_side = "inside")
    
# Generate BMS for Polygon 23 WALL3 2
save_bms(
    texture_name = ["OT_BAR_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 24 | BND WALL3 3
create_polygon(
    bound_number = 24, 
    vertex_coordinates = [
        (80, 15.0, 40), 
        (80, 25.0, 39.99), 
        (10, 25.0, 39.99), 
        (10, 15.0, 40)], wall_side = "inside")
    
# Generate BMS for Polygon 24 WALL3 3
save_bms(
    texture_name = ["OT_BAR_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 24, mode = "repeating_vertical", tile_x = 12, tile_y = 5))

# Polygon 25 | BND WALL3 4
create_polygon(
    bound_number = 25, 
    vertex_coordinates = [
        (10, 15.0, 40), 
        (10.01, 25.0, 40), 
        (10.01, 25.0, 10), 
        (10, 15.0, 10)], wall_side = "outside")
    
# Generate BMS for Polygon 25 WALL3 4
save_bms(
    texture_name = ["OT_BAR_BRICK"], 
    texture_darkness= [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 26 | BND
create_polygon(
    bound_number = 26, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (10, 15.0, 40), 		
        (10, 15.0, 50), 
        (80, 15.0, 50), 
        (80, 15.0, 40)])
    
# Generate BMS for Polygon 26
save_bms(
    texture_name = ["ROAD"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 26, mode = "horizontal"))

# Polygon 27 | BND floor
create_polygon(
    bound_number = 27, 
    vertex_coordinates = [
        (10, 15.0, 50), 		
        (10, 15.0, 80), 
        (80, 15.0, 80), 
        (80, 15.0, 50)])
    
# Generate BMS for Polygon 27 floor
save_bms(
    texture_name = ["T_WALL"])  

# Polygon 28 | BND WALL4 1
create_polygon(
    bound_number = 28, 
    vertex_coordinates = [
        (10, 15.0, 50), 
        (10, 25.0, 50.01), 
        (80, 25.0, 50.01), 
        (80, 15.0, 50)], wall_side = "outside")
    
# Generate BMS for Polygon 28 WALL4 1
save_bms(
    texture_name = ["CT_SHOP_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 28, mode = "repeating_vertical", tile_x = 12, tile_y = 5))

# Polygon 29| BND WALL4 2
create_polygon(
    bound_number = 29, 
    vertex_coordinates = [
        (80, 15.0, 50), 
        (79.99, 25.0, 50), 
        (79.99, 25.0, 80), 
        (80, 15.0, 80)], wall_side = "inside")
    
# Generate BMS for Polygon 29 WALL4 2
save_bms(
    texture_name = ["CT_SHOP_BRICK"], 
    texture_darkness= [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 30| BND WALL4 3
create_polygon(
    bound_number = 30, 
    vertex_coordinates = [
        (80, 15.0, 80), 
        (80, 25.0, 79.99), 
        (10, 25.0, 79.99), 
        (10, 15.0, 80)], wall_side = "inside")
    
# Generate BMS for Polygon 30 WALL4 3
save_bms(
    texture_name = ["CT_SHOP_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 30, mode = "repeating_vertical", tile_x = 12, tile_y = 5))

# Polygon 31| BND WALL4 4
create_polygon(
    bound_number = 31, 
    vertex_coordinates = [
        (10, 15.0, 80), 
        (10.01, 25.0, 80), 
        (10.01, 25.0, 50), 
        (10, 15.0, 50)], wall_side = "outside")
    
# Generate BMS for Polygon 31 WALL4 4
save_bms(
    texture_name = ["CT_SHOP_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 50 | BND
create_polygon(
    bound_number = 50, 
    vertex_coordinates = [
        (-80, 15.0, 10), 		
        (-80, 15.0, 80), 
        (-10, 15.0, 80), 
        (-10, 15.0, 10)])
    
# Generate BMS for Polygon 50
save_bms(
    texture_name = ["T_WALL"])      

# Polygon 6 | BND spawn
create_polygon(
    bound_number = 6, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (-10, 15.0, -10), 
        (-10, 15.0, 10), 	
        (10, 15.0, 10), 
        (10, 15.0, -10)])
    
# Generate BMS for Polygon 6 spawn
save_bms(
    texture_name = ["Rinter"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 6, mode = "horizontal"))
     
# Polygon 7 | BND
create_polygon(
    bound_number = 7, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (10, 15.0, -10), 
        (10, 15.0, -80), 	
        (-10, 15.0, -80), 
        (-10, 15.0, -10)])
    
# Generate BMS for Polygon 7
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 7, mode = "repeating_horizontal_flipped", tile_x = 10, tile_y = 2))

# Polygon 8 | BND
create_polygon(
    bound_number = 8, 
    material_index = NO_FRICTION_MTL, 
    cell_type = INDOORS, 
    hud_color = SNOW_HUD, 
    vertex_coordinates = [
        (40, 15.0, -10), 
        (40, 15.0, -80), 	
        (10, 15.0, -80), 
        (10, 15.0, -10)])
    
# Generate BMS for Polygon 8
save_bms(
    texture_name = ["L_RIVET"], 
    texture_darkness = [3, 3, 3, 3], 
    tex_coords = compute_uv(bound_number = 8, mode = "H", tile_x = 21, tile_y = 21))  

# Polygon 9 | BND
create_polygon(
    bound_number = 9, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (-80, 15.0, -80),              
        (80, 15.0, -80), 		
        (80, 15.0, -90), 
        (-80, 15.0, -90)])
    
# Generate BMS for Polygon 9
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 9, mode = "repeating_horizontal_flipped", tile_x = 7, tile_y = 1))

# Polygon 10 | BND
create_polygon(
     bound_number = 10, 
     material_index = GRASS_MTL, 
     hud_color = GRASS_HUD,       
     vertex_coordinates = [
         (-90.00, 4.00, -115.00), 
         (-90.00, 15.00, -90.00),  
         (90.00, 15.00, -90.00), 
         (90.00, 4.00, -115.00)])   
    
# Polygon 10 | Texture
save_bms(
     texture_name = ["T_GRASS"], texture_darkness = [2, 2, 2, 2], 
     tex_coords = compute_uv(bound_number = 10, mode = "repeating_vertical", tile_x = 20, tile_y = 20))

# Polygon 11 | BND 
create_polygon(
    bound_number = 11, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,    
    vertex_coordinates = [
        (-115, 4.0, -115), 		
        (115, 4.0, -115), 
        (115, 4.0, -500), 
        (-115, 4.0, -500)])
    
# Generate BMS for Polygon 11
save_bms(
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 11, mode = "r.H", tile_x = 25, tile_y = 25))
    
# Polygon 17 | BND
create_polygon(
    bound_number = 17, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (80, 15.0, -10), 
        (10, 15.0, -10), 
        (10, 15.0, 10), 
        (80, 15.0, 10)])

# Generate BMS for Polygon 17
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 17, mode = "repeating_horizontal_flipped", tile_x = 10, tile_y = 2))

# Polygon 18 | BND
create_polygon(
    bound_number = 18, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (80, 15.0, -80), 		
        (80, 15.0, 80), 
        (90, 15.0, 80), 
        (90, 15.0, -80)])
    
# Generate BMS for Polygon 18
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 18, mode = "repeating_horizontal", tile_x = 7, tile_y = 1))

# Polygon 19 | BND
create_polygon(
    bound_number = 19, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD,    
    vertex_coordinates = [
        (90, 15.0, 90), 		
        (115, 4.0, 90), 
        (115, 4.0, -90), 
        (90, 15.0, -90)])
    
# Generate BMS for Polygon 19
save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness= [2, 2, 2, 2], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5])     

# Polygon 20 | BND 
create_polygon(
    bound_number = 20, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,  
    vertex_coordinates = [
        (115, 4.0, -115), 		
        (115, 4.0, 115), 
        (500, 4.0, 115), 
        (500, 4.0, -115)])
    
# Generate BMS for Polygon 20
save_bms(
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 20, mode = "r.V", tile_x = 25, tile_y = 25))   

# Polygon 32 | BND
create_polygon(
    bound_number = 32, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (10, 15.0, 10), 		
        (-10, 15.0, 10), 
        (-10, 15.0, 80), 
        (10, 15.0, 80)])
    
# Generate BMS for Polygon 32
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 32, mode = "repeating_vertical_flipped", tile_x = 2, tile_y = 10))      
    
# Polygon 47 | BND
create_polygon(
    bound_number = 47, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (-80, 15.0, 80), 		
        (-80, 15.0, 90), 
        (80, 15.0, 90), 
        (80, 15.0, 80), ])
    
# Generate BMS for Polygon 47
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 47, mode = "repeating_vertical", tile_x = 1, tile_y = 7))

# Polygon 48 | BND
create_polygon(
    bound_number = 48, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD,    
    vertex_coordinates = [
        (-90, 15.0, 90), 
        (-90, 4.0, 115), 
        (90, 4.0, 115), 
        (90, 15.0, 90)])
    
# Generate BMS for Polygon 48
save_bms( 
    texture_name = ["T_GRASS"], 
    texture_darkness= [2, 2, 2, 2], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5])   

# Polygon 49 | BND
create_polygon(
    bound_number = 49, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,  
    vertex_coordinates = [
        (-115, 4.0, 115), 		
        (-115, 4.0, 500), 
        (115, 4.0, 500), 
        (115, 4.0, 115)])
    
# Generate BMS for Polygon 49
save_bms(
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 49, mode = "r.V", tile_x = 20, tile_y = 20))  

# Polygon 33 | BND
create_polygon(
    bound_number = 33, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (-10, 15.0, 10), 		
        (-10, 15.0, -10), 
        (-80, 15.0, -10), 
        (-80, 15.0, 10), ])

# Generate BMS for Polygon 33
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 33, mode = "repeating_vertical_flipped", tile_x = 2, tile_y = 10))

# Polygon 35| BND WALL5 1
create_polygon(
    bound_number = 35, 
    vertex_coordinates = [
        (-40, 15.0, 10), 
        (-40, 40.0, 10.01), 
        (-10, 40.0, 10.01), 
        (-10, 15.0, 10)], wall_side = "outside")
    
# Generate BMS for Polygon 35 WALL5 1
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 36| BND WALL5 2
create_polygon(
    bound_number = 36, 
    vertex_coordinates = [
        (-10, 15.0, 10), 
        (-10.01, 40.0, 10), 
        (-10.01, 40.0, 40), 
        (-10, 15.0, 40)], wall_side = "inside")
    
# Generate BMS for Polygon 36 WALL5 2
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 37| BND WALL5 3
create_polygon(
    bound_number = 37, 
    vertex_coordinates = [
        (-10, 15.0, 40), 
        (-10, 40.0, 39.99), 
        (-40, 40.0, 39.99), 
        (-40, 15.0, 40)], wall_side = "inside")
    
# Generate BMS for Polygon 37 WALL5 3
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 38| BND WALL5 4
create_polygon(
    bound_number = 38, 
    vertex_coordinates = [
        (-40, 15.0, 40), 
        (-39.99, 40.0, 40), 
        (-39.99, 40.0, 10), 
        (-40, 15.0, 10)], wall_side = "outside")
    
# Generate BMS for Polygon 38 WALL5 4
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 43| BND WALL7 1
create_polygon(
    bound_number = 43, 
    vertex_coordinates = [
        (-40, 15.0, 50), 
        (-40, 40.0, 50.01), 
        (-10, 40.0, 50.01), 
        (-10, 15.0, 50)], wall_side = "outside")
    
# Generate BMS for Polygon 43 WALL7 1
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 44| BND WALL7 2
create_polygon(
    bound_number = 44, 
    vertex_coordinates = [
        (-10, 15.0, 50), 
        (-10.01, 40.0, 50), 
        (-10.01, 40.0, 80), 
        (-10, 15.0, 80)], wall_side = "inside")
    
# Generate BMS for Polygon 44 WALL7 2
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 45| BND WALL7 3
create_polygon(
    bound_number = 45, 
    vertex_coordinates = [
        (-10, 15.0, 80), 
        (-10, 40.0, 79.99), 
        (-40, 40.0, 79.99), 
        (-40, 15.0, 80)], wall_side = "inside")
    
# Generate BMS for Polygon 45 WALL7 3
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 51 | BND WALL6 1
create_polygon(
    bound_number = 51, 
    vertex_coordinates = [
        (-80, 15.0, 10), 		
        (-80, 35.0, 10.01), 
        (-50, 35.0, 10.01), 
        (-50, 15.0, 10)], wall_side = "outside")
    
# Generate BMS for Polygon 51 WALL6 1
save_bms(
    texture_name = ["OT_MARKT_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5])     

# Polygon 52 | BND WALL6 2
create_polygon(
    bound_number = 52, 
    vertex_coordinates = [
        (-50, 15.0, 10), 		
        (-50.01, 35.0, 10), 
        (-50.01, 35.0, 80.), 
        (-50, 15.0, 80)], wall_side = "inside")
    
# Generate BMS for Polygon 52 WALL6 2
save_bms(
    texture_name = ["OT_MARKT_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5])    

# Polygon 53 | BND WALL6 3
create_polygon(
    bound_number = 53, 
    vertex_coordinates = [
        (-50, 15.0, 80), 		
        (-50, 35.0, 79.99), 
        (-80, 35.0, 79.99), 
        (-80, 15.0, 80)], wall_side = "inside")
    
# Generate BMS for Polygon 53 WALL6 3
save_bms( 
    texture_name = ["OT_MARKT_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5])    

# Polygon 54 | BND WALL6 4
create_polygon(
    bound_number = 54, 
    vertex_coordinates = [
        (-80, 15.0, 80), 		
        (-79.99, 35.0, 80), 
        (-79.99, 35.0, 10), 
        (-80, 15.0, 10)], wall_side = "outside")
    
# Generate BMS for Polygon 54 WALL6 4
save_bms(
    texture_name = ["OT_MARKT_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5])    

# Polygon 55 | BND
create_polygon(
    bound_number = 55, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (-90, 15.0, 80), 		
        (-80, 15.0, 80), 
        (-80, 15.0, -80), 
        (-90, 15.0, -80)])
    
# Generate BMS for Polygon 55
save_bms(
    texture_name = ["R4"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 55, mode = "repeating_vertical_flipped", tile_x = 1, tile_y = 7))

# Polygon 56 | BND
create_polygon(
    bound_number = 56, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD,    
    vertex_coordinates = [
        (-90, 15.0, -90), 	
        (-115, 4.0, -90), 
        (-115, 4.0, 90), 
        (-90, 15.0, 90)])
    
# Generate BMS for Polygon 56
save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5])

# Polygon 57 | BND
create_polygon(
    bound_number = 57, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,  
    vertex_coordinates = [
        (-500, 4.0, -115), 	
        (-500, 4.0, 115), 
        (-115, 4.0, 115), 
        (-115, 4.0, -115)])
    
# Generate BMS for Polygon 57
save_bms( 
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 57, mode = "r.V", tile_x = 25, tile_y = 25))

# Polygon 58 | BND
create_polygon(
    bound_number = 58, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (80, 15.0, -80), 		
        (90, 15.0, -80), 
        (90, 15.0, -90), 
        (80, 15.0, -90)])
    
# Generate BMS for Polygon 58
save_bms(
    texture_name = ["R2"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 58, mode = "rotating_repeating", tile_x = 1, tile_y = 1, angle_degrees = (0, -45)))
         
# Polygon 59 | BND
create_polygon(
    bound_number = 59, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (80, 15.0, 80), 		
        (80, 15.0, 90), 
        (90, 15.0, 90), 
        (90, 15.0, 80)])
    
# Generate BMS for Polygon 59
save_bms(
    texture_name = ["R2"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 59, mode = "rotating_repeating", tile_x = 1, tile_y = 1, angle_degrees = (0, 90)))      

# Polygon 60 | BND
create_polygon(
    bound_number = 60, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (-80, 15.0, 80), 		
        (-90, 15.0, 80), 
        (-90, 15.0, 90), 
        (-80, 15.0, 90)])
    
# Generate BMS for Polygon 60
save_bms(
    texture_name = ["R2"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 60, mode = "rotating_repeating", tile_x = 1, tile_y = 1, angle_degrees = (-90, -45)))    

# Polygon 61 | BND
create_polygon(
    bound_number = 61, 
    hud_color = ROAD_HUD, 
    vertex_coordinates = [
        (-90, 15.0, -80), 	
        (-80, 15.0, -80), 
        (-80, 15.0, -90), 
        (-90, 15.0, -90)])
    
# Generate BMS for Polygon 61
save_bms(
    texture_name = ["R2"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 61, mode = "rotating_repeating", tile_x = 1, tile_y = 1, angle_degrees = (0, 135)))      
         
# Polygon 39 | BND
create_polygon(
    bound_number = 39, 
    hud_color = '#F2B935', 
    vertex_coordinates = [
        (-40, 15.0, 10), 		
        (-50, 15.0, 10), 
        (-50, 25.0, 40), 
        (-40, 25.0, 40)])
      
# Generate BMS for Polygon 39
save_bms( 
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness= [0, 1, 2, 3], tex_coords = [0, 10, 0, 0, 10, 10, 10, 0]) 

# Polygon 62 | BND
create_polygon(
    bound_number = 62, 
    hud_color = '#F2B935', 
    vertex_coordinates = [
        (-50, 15.0, 80), 		
        (-40, 15.0, 80), 
        (-40, 25.0, 50), 
        (-50, 25.0, 50)])
      
# Generate BMS for Polygon 62
save_bms( 
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness= [0, 1, 2, 3], tex_coords = [0, 10, 0, 0, 10, 10, 10, 0])     

# Polygon 63| BND WALL7 4
create_polygon(
    bound_number = 63, 
    vertex_coordinates = [
        (-40, 15.0, 80), 
        (-39.99, 40.0, 80), 
        (-39.99, 40.0, 50), 
        (-40, 15.0, 50)], wall_side = "outside")
    
# Generate BMS for Polygon 63 WALL7 4
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 5, 0, -5, -5, -5, -5, 5]) 

# Polygon 40 | BND
create_polygon(
    bound_number = 40, 
    hud_color = '#F2B935', 
    vertex_coordinates = [
        (-25, 25.0, 40), 		
        (-50, 25.0, 40), 
        (-50, 25.0, 50), 
        (-25, 25.0, 50)])
    
# Generate BMS for Polygon 40
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 10, 0, 0, 10, 10, 10, 0])    
    
# Polygon 41 | BND
create_polygon(
    bound_number = 41, 
    hud_color = '#F2B935', 
    vertex_coordinates = [
        (-10, 30.0, 50), 		
        (-10, 30.0, 40), 
        (-25, 25.0, 40), 
        (-25, 25.0, 50)])
    
# Generate BMS for Polygon 41
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [0, 1, 2, 3], tex_coords = [0, 10, 0, 0, 10, 10, 10, 0])   

# Polygon 34 | BND
create_polygon(
    bound_number = 34, 
    vertex_coordinates = [
        (-10.01, 30.0, 50), 		
        (-10.0, 15.0, 50), 
        (-10.0, 15.0, 40), 
        (-10.01, 30.0, 40)], wall_side = "inside")
    
# Generate BMS for Polygon 34
save_bms(
    texture_name = ["R_BLDG1_DOOR_01"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 34, mode = "vertical")) 

# Polygon 71 | BND | hill triangle 
create_polygon(
    bound_number = 71, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (-90, 4.0, -115), 
        (-115, 4.0, -115), 
        (-90, 15.0, -90), 
        (-89.9, 15.0, -90)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 71, mode = "r.H", tile_x = 5, tile_y = 5)) 

# Polygon 72 | BND | hill triangle 
create_polygon(
    bound_number = 72, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (-115, 4.0, -115), 
        (-115, 4.0, -90), 
        (-90, 15.0, -89.9), 
        (-90, 15.0, -90)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 72, mode = "r.H", tile_x = 5, tile_y = 5))

# Polygon 73 | BND | hill triangle 
create_polygon(
    bound_number = 73, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (-115, 4.0, 90), 
        (-115, 4.0, 115), 
        (-90, 15.0, 90), 
        (-90, 15.0, 89.9)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 73, mode = "r.H", tile_x = 5, tile_y = 5))

# Polygon 74 | BND | hill triangle 
create_polygon(
    bound_number = 74, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (-115, 4.0, 115), 
        (-90, 4.0, 115), 
        (-89.9, 15.0, 90), 
        (-90, 15.0, 90)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 74, mode = "r.H", tile_x = 5, tile_y = 5))

# Polygon 75 | BND | hill triangle 
create_polygon(
    bound_number = 75, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (115, 4.0, 115), 
        (115, 4.0, 90), 
        (90, 15.0, 89.9), 
        (90, 15.0, 90)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 75, mode = "r.H", tile_x = 5, tile_y = 5))

# Polygon 76 | BND | hill triangle 
create_polygon(
    bound_number = 76, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (90, 4.0, 115), 
        (115, 4.0, 115), 
        (90, 15.0, 90), 
        (89.9, 15.0, 90)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 76, mode = "r.H", tile_x = 5, tile_y = 5))

# Polygon 77 | BND | hill triangle 
create_polygon(
    bound_number = 77, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (115, 4.0, -90), 
        (115, 4.0, -115), 
        (90, 15.0, -90), 
        (90, 15.0, -89.9)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 77, mode = "r.H", tile_x = 5, tile_y = 5))

# Polygon 78 | BND | hill triangle 
create_polygon(
    bound_number = 78, 
    material_index = GRASS_MTL, 
    hud_color = GRASS_HUD, 
    vertex_coordinates = [
        (115, 4.0, -115), 
        (90, 4.0, -115), 
        (89.9, 15.0, -90), 
        (90, 15.0, -90)])

save_bms(
    texture_name = ["T_GRASS"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 78, mode = "r.H", tile_x = 5, tile_y = 5))

# Polygon 90 | BND | Water Missing Part 1
create_polygon(
    bound_number = 90, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,  
    vertex_coordinates = [
        (115, 4.0, 500), 		
        (500, 4.0, 500), 
        (500, 4.0, 115), 
        (115, 4.0, 115)])
    
# Generate BMS for Polygon 90
save_bms(
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 90, mode = "r.H", tile_x = 25, tile_y = 25))

# Polygon 91 | BND | Water Missing Part 2
create_polygon(
    bound_number = 91, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,  
    vertex_coordinates = [
        (-500, 4.0, -115), 		
        (-115, 4.0, -115), 
        (-115, 4.0, -500), 
        (-500, 4.0, -500)])
    
# Generate BMS for Polygon 91
save_bms(
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 91, mode = "r.H", tile_x = 25, tile_y = 25))   

# Polygon 92 | BND | Water Missing Part 3
create_polygon(
    bound_number = 92, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,  
    vertex_coordinates = [
        (500, 4.0, -115), 		
        (500, 4.0, -500), 
        (115, 4.0, -500), 
        (115, 4.0, -115)])
    
# Generate BMS for Polygon 92
save_bms(
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 92, mode = "r.V", tile_x = 25, tile_y = 25))   

# Polygon 93 | BND | Water Missing Part 4
create_polygon(
    bound_number = 93, 
    material_index = WATER_MTL, 
    cell_type = WATER_DRIFT, 
    hud_color = WATER_HUD,  
    vertex_coordinates = [
         (-500, 4.0, 115),                 
         (-500, 4.0, 500),                 
         (-115, 4.0, 500),                 
         (-115, 4.0, 115)]), 

# Generate BMS for Polygon 93
save_bms(
    texture_name = ["T_WATER"], 
    texture_darkness = [2, 2, 2, 2], 
    tex_coords = compute_uv(bound_number = 93, mode = "r.V", tile_x = 25, tile_y = 25))   

# Polygon 991 | BND floor roof
create_polygon(
    bound_number = 991, 
    vertex_coordinates = [
        (-10, 35.0, -10), 
        (-10, 35.0, -80), 	
        (-80, 35.0, -80), 
        (-80, 35.0, -10)])

# Polygon 991 | Texture roof
save_bms(
    texture_name = ["T_WOOD"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 991, mode = "repeating_vertical", tile_x = 7, tile_y = 7)) 

# Polygon 992 | BND road floor roof
create_polygon(
    bound_number = 992, 
    vertex_coordinates = [
        (80, 25.0, -10), 
        (80, 25.0, -80), 	
        (40, 25.0, -80), 
        (40, 25.0, -10)])
    
# Generate BMS for Polygon 992 roof
save_bms(
    texture_name = ["IND_WALL"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 992, mode = "repeating_vertical", tile_x = 4, tile_y = 7))   

# Polygon 993 | BND floor roof
create_polygon(
    bound_number = 993, 
    vertex_coordinates = [
        (10, 25.0, 10), 		
        (10, 25.0, 40), 
        (80, 25.0, 40), 
        (80, 25.0, 10)])
    
# Generate BMS for Polygon 993 floor roof
save_bms(
    texture_name = ["OT_BAR_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 993, mode = "repeating_vertical", tile_x = 7, tile_y = 3))  

# Polygon 994 | BND floor roof
create_polygon(
    bound_number = 994, 
    vertex_coordinates = [
        (10, 25.0, 50), 		
        (10, 25.0, 80), 
        (80, 25.0, 80), 
        (80, 25.0, 50)])
    
# Generate BMS for Polygon 994 floor roof
save_bms(
    texture_name = ["CT_SHOP_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 994, mode = "repeating_vertical", tile_x = 7, tile_y = 3))  

# Polygon 995 | BND floor roof
create_polygon(
    bound_number = 995, 
    vertex_coordinates = [
        (-10, 40.0, 10), 		
        (-40, 40.0, 10), 
        (-40, 40.0, 40), 
        (-10, 40.0, 40)])
    
# Generate BMS for Polygon 995 floor roof
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 995, mode = "repeating_vertical", tile_x = 3, tile_y = 3))   

# Polygon 996 | BND floor roof
create_polygon(
    bound_number = 996, 
    vertex_coordinates = [
        (-10, 40.0, 50), 		
        (-40, 40.0, 50), 
        (-40, 40.0, 80), 
        (-10, 40.0, 80)])
    
# Generate BMS for Polygon 996 floor roof
save_bms(
    texture_name = ["OT_MALL_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 996, mode = "repeating_vertical", tile_x = 4, tile_y = 3))   

# Polygon 997 | BND floor roof
create_polygon(
    bound_number = 997, 
    vertex_coordinates = [
        (-80, 35.0, 80), 		
        (-50, 35.0, 80), 
        (-50, 35.0, 10), 
        (-80, 35.0, 10)])
    
# Generate BMS for Polygon 997 floor roof
save_bms(
    texture_name = ["OT_MARKT_BRICK"], 
    texture_darkness = [1, 1, 1, 1], 
    tex_coords = compute_uv(bound_number = 997, mode = "repeating_vertical", tile_x = 3, tile_y = 7))   

# Polygon 999 BND Garage
create_polygon(
    bound_number = 999, 
    vertex_coordinates = [
        (90, 0, 90), 
        (90, 0, -90), 
        (-90, 0, -90), 
        (-90, 0, 90)]), 

save_bms(
    texture_name = ["ROAD"], 
    texture_darkness = [1, 1, 1, 1], tex_coords = compute_uv(bound_number = 999, mode = "horizontal"))  

# Polygon 998 BND Garage HILL
create_polygon(
    bound_number = 998, 
    vertex_coordinates = [
        (-10, -0.5, -10), 
        (-10, 15, -60), 
        (10, 15, -60), 
        (10, -0.5, -10)])

save_bms(
    texture_name = ["ROAD"], 
    texture_darkness = [1, 1, 1, 1], tex_coords = compute_uv(bound_number = 998, mode = "horizontal"))