
############################
###### Made by fati ########
############################

# Last Update : August 23, 2025

create_polygon(
    bound_number = 1,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 0.0, -63.68),
		(55.21, 0.0, -63.68),
		(55.21, 0.0, -123.68),
		(-52.12, 0.0, -123.68)])

save_mesh(
    texture_name = ["T_ASPHALTLINES"],
    tex_coords = compute_uv(bound_number = 1, tile_x = 15.00, tile_y = 5.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 32,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 0.0, -123.68),
		(55.21, 0.0, -123.68),
		(55.21, -5.11, -132.24),
		(-52.12, -5.11, -132.24)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 32, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 3,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 0.0, -63.68),
		(-52.12, 0.0, -123.68),
		(-60.69, -5.11, -123.68),
		(-60.69, -5.11, -63.68)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 3, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 4,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 0.0, -123.68),
		(55.21, 0.0, -63.68),
		(63.77, -5.11, -63.68),
		(63.77, -5.11, -123.68)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 4, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 6,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, -59.80),
		(-5.12, 1.71, -59.80),
		(-5.12, 0.0, -63.68),
		(-52.12, 0.0, -63.68)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 6, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 5,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (8.21, 1.71, -59.80),
		(55.21, 1.71, -59.80),
		(55.21, 0.0, -63.68),
		(8.21, 0.0, -63.68)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 5, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 7,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-5.12, 1.71, -59.80),
		(8.21, 1.71, -59.80),
		(8.21, 0.0, -63.68),
		(-5.12, 0.0, -63.68)])

save_mesh(
    texture_name = ["T_ASPHALTLINES"],
    tex_coords = compute_uv(bound_number = 7, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 8,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-5.12, 1.71, 46.91),
		(8.21, 1.71, 46.91),
		(8.21, 1.71, -59.80),
		(-5.12, 1.71, -59.80)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 8, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 9,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (8.21, 1.71, 46.91),
		(55.21, 1.71, 46.91),
		(55.21, 1.71, -59.80),
		(8.21, 1.71, -59.80)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 9, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 10,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, 46.91),
		(-5.12, 1.71, 46.91),
		(-5.12, 1.71, -59.80),
		(-52.12, 1.71, -59.80)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 10, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 11,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-76.19, 15.36, 117.92),
		(-72.27, 15.36, 121.84),
		(-1.26, 1.71, 50.83),
		(-5.19, 1.71, 46.91)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 11, tile_x = 5.00, tile_y = 5.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 12,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (75.29, 15.36, 121.84),
		(79.22, 15.36, 117.92),
		(8.21, 1.71, 46.91),
		(4.29, 1.71, 50.83)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 12, tile_x = 5.00, tile_y = 5.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 13,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-1.26, 1.71, 50.83),
		(4.29, 1.71, 50.83),
		(8.21, 1.71, 46.91),
		(-5.19, 1.71, 46.91)])

save_mesh(
    texture_name = [Texture.ZEBRA_CROSSING],
    tex_coords = compute_uv(bound_number = 13, tile_x = 2.00, tile_y = 2.00, angle_degrees = -90.00))



create_polygon(
    bound_number = 14,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-77.82, 15.36, 351.85),
		(-72.27, 15.36, 351.85),
		(-72.27, 15.36, 121.84),
		(-77.82, 15.36, 121.84)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 14, tile_x = 10.00, tile_y = 20.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 15,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (75.29, 15.36, 351.85),
		(80.84, 15.36, 351.85),
		(80.84, 15.36, 121.84),
		(75.29, 15.36, 121.84)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 15, tile_x = 10.00, tile_y = 20.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 22,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-72.27, 15.36, 351.85),
		(75.29, 15.36, 351.85),
		(75.29, 15.36, 121.84),
		(-72.27, 15.36, 121.84)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 22, tile_x = 50.00, tile_y = 25.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 23,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-72.27, 15.36, 121.84),
		(-1.26, 1.71, 50.83),
		(-1.26, 15.36, 121.84)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 23, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 24,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (4.29, 15.36, 121.84),
		(75.29, 15.36, 121.84),
		(4.29, 1.71, 50.83)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 24, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 17,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-1.26, 15.36, 121.84),
		(4.29, 15.36, 121.84),
		(4.29, 1.71, 50.83),
		(-1.26, 1.71, 50.83)])

save_mesh(
    texture_name = ["IND_ROAD"],
    tex_coords = compute_uv(bound_number = 17, tile_x = 5.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 29,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-1.26, 15.36, 351.85),
		(-72.27, 15.36, 351.85),
		(-1.26, 1.71, 422.86)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 29, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 25,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (75.29, 15.36, 351.85),
		(4.29, 1.71, 422.86),
		(4.29, 15.36, 351.85)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 25, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 67,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (4.29, 15.36, 351.85),
		(-1.26, 15.36, 351.85),
		(-1.26, 1.71, 422.86),
		(4.29, 1.71, 422.86)])

save_mesh(
    texture_name = ["IND_ROAD"],
    tex_coords = compute_uv(bound_number = 67, tile_x = 5.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 19,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (4.29, 1.71, 422.86),
		(-1.26, 1.71, 422.86),
		(-5.19, 1.71, 426.78),
		(8.21, 1.71, 426.78)])

save_mesh(
    texture_name = [Texture.ZEBRA_CROSSING],
    tex_coords = compute_uv(bound_number = 19, tile_x = 2.00, tile_y = 2.00, angle_degrees = -90.00))



create_polygon(
    bound_number = 20,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-72.27, 15.36, 351.85),
		(-76.19, 15.36, 355.78),
		(-5.19, 1.71, 426.78),
		(-1.26, 1.71, 422.86)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 20, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 21,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (79.22, 15.36, 355.78),
		(75.29, 15.36, 351.85),
		(4.29, 1.71, 422.86),
		(8.21, 1.71, 426.78)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 21, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 31,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (27.81, 20.71, 269.82),
		(-24.79, 20.71, 269.82),
		(-24.79, 15.36, 270.75),
		(27.81, 15.36, 270.75)])

save_mesh(
    texture_name = ["T_WALL02"],
    tex_coords = compute_uv(bound_number = 31, tile_x = 10.00, tile_y = 1.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 33,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (27.81, 20.71, 203.88),
		(-24.79, 20.71, 203.88),
		(-24.79, 20.71, 269.82),
		(27.81, 20.71, 269.82)])

save_mesh(
    texture_name = ["IND_CONCRETE"],
    tex_coords = compute_uv(bound_number = 33, tile_x = 10.00, tile_y = 10.00, angle_degrees = -90.00))



create_polygon(
    bound_number = 41,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (27.81, 20.71, 203.88),
		(27.81, 15.36, 202.95),
		(28.74, 15.36, 202.95)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 41, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 40,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (28.74, 15.36, 203.88),
		(27.81, 20.71, 203.88),
		(28.74, 15.36, 202.95)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 40, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 42,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-24.79, 20.71, 203.88),
		(27.81, 20.71, 203.88),
		(27.81, 15.36, 202.95),
		(-24.79, 15.36, 202.95)])

save_mesh(
    texture_name = ["T_WALL02"],
    tex_coords = compute_uv(bound_number = 42, tile_x = 10.00, tile_y = 1.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 43,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-24.79, 20.71, 269.82),
		(-24.79, 20.71, 203.88),
		(-25.72, 15.36, 203.88),
		(-25.72, 15.36, 269.82)])

save_mesh(
    texture_name = ["T_WALL02"],
    tex_coords = compute_uv(bound_number = 43, tile_x = 10.00, tile_y = 1.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 44,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (27.81, 20.71, 203.88),
		(27.81, 20.71, 269.82),
		(28.74, 15.36, 269.82),
		(28.74, 15.36, 203.88)])

save_mesh(
    texture_name = ["T_WALL02"],
    tex_coords = compute_uv(bound_number = 44, tile_x = 10.00, tile_y = 1.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 48,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-24.79, 20.71, 203.88),
		(-25.72, 15.36, 203.88),
		(-25.72, 15.36, 202.95)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 48, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 45,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-24.79, 15.36, 202.95),
		(-24.79, 20.71, 203.88),
		(-25.72, 15.36, 202.95)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 45, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 49,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-24.79, 20.71, 269.82),
		(-24.79, 15.36, 270.75),
		(-25.72, 15.36, 270.75)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 49, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 46,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-25.72, 15.36, 269.82),
		(-24.79, 20.71, 269.82),
		(-25.72, 15.36, 270.75)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 46, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 50,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (27.81, 20.71, 269.82),
		(28.74, 15.36, 269.82),
		(28.74, 15.36, 270.75)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 50, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 47,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (27.81, 15.36, 270.75),
		(27.81, 20.71, 269.82),
		(28.74, 15.36, 270.75)])

save_mesh(
    texture_name = ["IND_TRUCK_SIDE"],
    tex_coords = compute_uv(bound_number = 47, tile_x = 1.00, tile_y = 1.00, angle_degrees = 90.00))



create_polygon(
    bound_number = 60,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-5.12, 1.71, 426.78),
		(-52.12, 1.71, 426.78),
		(-52.12, 1.71, 533.49),
		(-5.12, 1.71, 533.49)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 60, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 59,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (8.21, 1.71, 426.78),
		(-5.12, 1.71, 426.78),
		(-5.12, 1.71, 533.49),
		(8.21, 1.71, 533.49)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 59, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 58,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (8.21, 1.71, 533.49),
		(-5.12, 1.71, 533.49),
		(-5.12, 0.0, 537.37),
		(8.21, 0.0, 537.37)])

save_mesh(
    texture_name = ["T_ASPHALTLINES"],
    tex_coords = compute_uv(bound_number = 58, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 56,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, 533.49),
		(8.21, 1.71, 533.49),
		(8.21, 0.0, 537.37),
		(55.21, 0.0, 537.37)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 56, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 55,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-5.12, 1.71, 533.49),
		(-52.12, 1.71, 533.49),
		(-52.12, 0.0, 537.37),
		(-5.12, 0.0, 537.37)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 55, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 54,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 0.0, 597.37),
		(-52.12, 0.0, 537.37),
		(-60.68, -5.11, 537.37),
		(-60.68, -5.11, 597.37)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 54, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 53,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 0.0, 537.37),
		(55.21, 0.0, 597.37),
		(63.78, -5.11, 597.37),
		(63.78, -5.11, 537.37)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 53, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 52,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 0.0, 597.37),
		(-52.12, 0.0, 597.37),
		(-52.12, -5.11, 605.93),
		(55.21, -5.11, 605.93)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 52, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 61,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, 426.78),
		(8.21, 1.71, 426.78),
		(8.21, 1.71, 533.49),
		(55.21, 1.71, 533.49)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 61, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 51,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 0.0, 537.37),
		(-52.12, 0.0, 537.37),
		(-52.12, 0.0, 597.37),
		(55.21, 0.0, 597.37)])

save_mesh(
    texture_name = ["T_ASPHALTLINES"],
    tex_coords = compute_uv(bound_number = 51, tile_x = 15.00, tile_y = 5.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 64,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-77.82, 15.36, 351.85),
		(-77.82, 15.36, 121.84),
		(-86.39, -3.40, 121.84),
		(-86.39, -3.40, 351.85)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 64, tile_x = 20.00, tile_y = 5.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 85,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, -59.80),
		(55.21, 1.71, 46.91),
		(63.77, -3.40, 46.91),
		(63.77, -3.40, -59.80)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 85, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 76,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, 426.78),
		(55.21, 1.71, 533.49),
		(63.78, -3.40, 533.49),
		(63.78, -3.40, 426.78)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 76, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 73,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, 533.49),
		(-52.12, 1.71, 426.78),
		(-60.68, -3.40, 426.78),
		(-60.68, -3.40, 533.49)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 73, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 84,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (8.21, 1.71, 46.91),
		(14.26, -3.40, 40.86),
		(79.22, 15.36, 117.92)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 84, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 83,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (79.22, 15.36, 117.92),
		(89.72, -3.40, 116.31),
		(14.26, -3.40, 40.86)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 83, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 65,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-76.19, 15.36, 117.92),
		(-86.71, -3.40, 116.31),
		(-11.25, -3.40, 40.85)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 65, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 66,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-5.19, 1.71, 46.91),
		(-76.19, 15.36, 117.92),
		(-11.25, -3.40, 40.85)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 66, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 72,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-5.19, 1.71, 426.78),
		(-11.24, -3.40, 432.83),
		(-76.19, 15.36, 355.78)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 72, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 71,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-76.19, 15.36, 355.78),
		(-86.70, -3.40, 357.38),
		(-11.24, -3.40, 432.83)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 71, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 75,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (79.22, 15.36, 355.78),
		(89.73, -3.40, 357.38),
		(14.27, -3.40, 432.84)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 75, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 74,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (8.21, 1.71, 426.78),
		(79.22, 15.36, 355.78),
		(14.27, -3.40, 432.84)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 74, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 114,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (80.84, 15.36, 121.84),
		(80.84, 15.36, 351.85),
		(89.41, -3.40, 351.85),
		(89.41, -3.40, 121.84)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 114, tile_x = 20.00, tile_y = 5.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 86,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, 46.91),
		(-52.12, 1.71, -59.80),
		(-60.69, -3.40, -59.80),
		(-60.69, -3.40, 46.91)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 86, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 63,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, 46.91),
		(-52.12, 1.71, 46.91),
		(-52.12, -3.40, 55.47),
		(55.21, -3.40, 55.47)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 63, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 77,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, 426.78),
		(55.21, 1.71, 426.78),
		(55.21, -3.40, 418.22),
		(-52.12, -3.40, 418.22)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 77, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 88,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-77.82, 15.36, 121.84),
		(-76.19, 15.36, 117.92),
		(-72.27, 15.36, 121.84)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 88, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 89,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (80.84, 15.36, 121.84),
		(75.29, 15.36, 121.84),
		(79.22, 15.36, 117.92)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 89, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 90,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (80.84, 15.36, 351.85),
		(79.22, 15.36, 355.78),
		(75.29, 15.36, 351.85)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 90, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 99,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (80.84, 15.36, 351.85),
		(89.41, -3.40, 351.85),
		(89.73, -3.40, 357.38)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 99, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 100,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (79.22, 15.36, 117.92),
		(89.72, -3.40, 116.31),
		(80.84, 15.36, 121.84)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 100, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 101,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (80.84, 15.36, 121.84),
		(89.41, -3.40, 121.84),
		(89.72, -3.40, 116.31)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 101, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 102,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (79.22, 15.36, 355.78),
		(80.84, 15.36, 351.85),
		(89.73, -3.40, 357.38)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 102, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 103,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-76.19, 15.36, 355.78),
		(-77.82, 15.36, 351.85),
		(-72.27, 15.36, 351.85)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 103, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 91,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-77.82, 15.36, 121.84),
		(-86.39, -3.40, 121.84),
		(-86.71, -3.40, 116.31)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 91, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 92,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-76.19, 15.36, 355.78),
		(-86.70, -3.40, 357.38),
		(-77.82, 15.36, 351.85)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 92, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 93,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-76.19, 15.36, 117.92),
		(-77.82, 15.36, 121.84),
		(-86.71, -3.40, 116.31)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 93, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 94,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-77.82, 15.36, 351.85),
		(-86.39, -3.40, 351.85),
		(-86.70, -3.40, 357.38)])

save_mesh(
    texture_name = ["T_DIRT"],
    tex_coords = compute_uv(bound_number = 94, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 95,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, 426.78),
		(-52.12, -3.40, 418.22),
		(-60.68, -3.40, 426.78)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 95, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 96,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, 426.78),
		(63.77, -3.40, 426.78),
		(55.21, -3.40, 418.22)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 96, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 97,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, 46.91),
		(55.21, -3.40, 55.47),
		(63.77, -3.40, 46.91)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 97, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 98,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, 46.91),
		(-60.68, -3.40, 46.91),
		(-52.12, -3.40, 55.47)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 98, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 104,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 0.0, 597.37),
		(63.78, -5.11, 597.37),
		(55.21, -5.11, 605.93)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 104, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 105,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 0.0, 597.37),
		(-52.12, -5.11, 605.94),
		(-60.68, -5.11, 597.37)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 105, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 107,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-144.01, 15.36, 245.40),
		(-77.82, 15.36, 245.40),
		(-77.82, 15.36, 228.21),
		(-144.01, 15.36, 228.21)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 107, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 82,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-144.01, 15.36, 245.40),
		(-144.01, -5.79, 270.75),
		(-77.82, -5.79, 270.75),
		(-77.82, 15.36, 245.40)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 82, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 109,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 245.40),
		(-144.01, 15.36, 245.40),
		(-144.01, 15.36, 228.21),
		(-210.21, -1.21, 228.21)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 109, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 113,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-274.87, -1.21, 292.40),
		(-210.21, -1.21, 292.40),
		(-210.21, -1.21, 181.21),
		(-274.87, -1.21, 181.21)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 113, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 115,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-274.87, -1.21, 181.21),
		(-210.21, -1.21, 70.03),
		(-104.32, -1.21, 181.21)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 115, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 87,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 403.59),
		(-104.32, -1.21, 292.40),
		(-76.50, -1.21, 403.59)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 87, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 81,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-144.01, 15.36, 228.21),
		(-210.21, -1.21, 228.21),
		(-143.98, -5.79, 202.95)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 81, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 80,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-77.82, 15.36, 228.21),
		(-77.79, -5.79, 202.95),
		(-143.98, -5.79, 202.95),
		(-144.01, 15.36, 228.21)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 80, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 79,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 245.40),
		(-144.01, 15.36, 245.40),
		(-144.01, -5.79, 270.75)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 79, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 108,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 403.59),
		(-76.50, -1.21, 403.59),
		(-70.92, 1.77, 445.66)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 108, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 69,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-70.92, 1.77, 27.95),
		(-62.67, -2.13, 20.23),
		(-225.22, -5.11, 62.31),
		(-210.21, -1.21, 70.03)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 69, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 78,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-338.89, 9.39, 292.40),
		(-338.89, 9.39, 181.21),
		(-361.12, -4.66, 181.21),
		(-361.12, -4.66, 292.40)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 78, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 68,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 70.03),
		(-225.22, -5.11, 62.31),
		(-361.12, -4.66, 181.21),
		(-338.89, 9.39, 181.21)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 68, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 62,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-338.89, 9.39, 292.40),
		(-361.12, -4.66, 292.40),
		(-210.21, -7.22, 406.03),
		(-210.21, -1.21, 403.59)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 62, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 57,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 403.59),
		(-210.21, -7.22, 406.03),
		(-62.67, -3.57, 451.71),
		(-70.92, 1.77, 445.66)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 57, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 39,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 292.40),
		(-195.95, -5.79, 292.40),
		(-195.95, -5.79, 181.21),
		(-210.21, -1.21, 181.21)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 39, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 38,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-104.32, -1.21, 292.40),
		(-104.32, -5.79, 289.72),
		(-210.21, -5.79, 289.72),
		(-210.21, -1.21, 292.40)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 38, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 37,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-210.21, -1.21, 181.21),
		(-210.21, -5.57, 185.71),
		(-104.32, -5.57, 185.71),
		(-104.32, -1.21, 181.21)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 37, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 70,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-67.31, -3.57, 402.15),
		(-76.50, -1.21, 403.59),
		(-70.92, 1.77, 445.66),
		(-62.67, -3.57, 451.71)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 70, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 36,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-100.77, -6.82, 289.72),
		(-104.32, -1.21, 292.40),
		(-76.50, -1.21, 403.59),
		(-67.31, -3.57, 402.15)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 36, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 35,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-62.67, -2.13, 20.23),
		(-70.92, 1.77, 27.95),
		(-76.50, -1.21, 70.03),
		(-67.70, -5.07, 70.03)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 35, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 34,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-67.70, -5.07, 70.03),
		(-76.50, -1.21, 70.03),
		(-104.32, -1.21, 181.21),
		(-95.53, -5.07, 181.21)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 34, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 26,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-104.32, -1.21, 181.21),
		(-76.50, -1.21, 70.03),
		(-210.21, -1.21, 70.03)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 26, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 28,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-70.92, 1.77, 27.95),
		(-76.50, -1.21, 70.03),
		(-210.21, -1.21, 70.03)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 28, tile_x = 10.00, tile_y = 10.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 27,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-104.32, -1.21, 292.40),
		(-274.87, -1.21, 292.40),
		(-210.21, -1.21, 403.59)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 27, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 18,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-338.89, 9.39, 292.40),
		(-274.87, -1.21, 292.40),
		(-274.87, -1.21, 181.21),
		(-338.89, 9.39, 181.21)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 18, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 16,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-338.89, 9.39, 181.21),
		(-210.21, -1.21, 70.03),
		(-274.87, -1.21, 181.21)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 16, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 106,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-274.87, -1.21, 292.40),
		(-338.89, 9.39, 292.40),
		(-210.21, -1.21, 403.59)])

save_mesh(
    texture_name = ["T_ASPHALT"],
    tex_coords = compute_uv(bound_number = 106, tile_x = 15.00, tile_y = 15.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 111,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-60.69, -3.40, -59.80),
		(-52.12, 1.71, -59.80),
		(-52.12, 0.0, -63.68),
		(-60.69, -5.11, -63.68)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 111, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 110,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (55.21, 1.71, -59.80),
		(63.77, -3.40, -59.80),
		(63.77, -5.11, -63.68),
		(55.21, 0.0, -63.68)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 110, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 30,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (63.78, -3.40, 533.49),
		(55.21, 1.71, 533.49),
		(55.21, 0.0, 537.37),
		(63.78, -5.11, 537.37)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 30, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 112,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-52.12, 1.71, 533.49),
		(-60.68, -3.40, 533.49),
		(-60.68, -5.11, 537.37),
		(-52.12, 0.0, 537.37)])

save_mesh(
    texture_name = ["IND_ROCK"],
    tex_coords = compute_uv(bound_number = 112, tile_x = 10.00, tile_y = 2.00, angle_degrees = 180.00))



create_polygon(
    bound_number = 2,
	material_index = Material.WATER,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-504.66, -2.60, 797.61),
		(318.91, -2.60, 797.61),
		(318.91, -2.60, -336.45),
		(-504.66, -2.60, -336.45)])

save_mesh(
    texture_name = [Texture.WATER],
    tex_coords = compute_uv(bound_number = 2, tile_x = 75.00, tile_y = 75.00, angle_degrees = 180.00))