from src.Constants.props import Prop
from src.Constants.constants import HUGE
from src.Constants.file_types import Axis

from src.Constants.races import RaceModeNum, RaceMode
from src.Constants.vehicles import PlayerCar


#trailer_set = {
 #   "offset": (-4, 15, 183),
  #  "end": (-4, 15, 195),
   # "name": Prop.TRAILER,
    #"separator": "x"  # Use the {}-axis dimension of the object as the spacing between each prop
#}

# Race specific props
########################

race2_barricade_1= {
    "offset": (9, 1, 34),
    "end": (25, 1, 6),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_2= {
    "offset": (-31, 1, -7),
    "end": (-18, 1, 25),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_3= {
    "offset": (43, 15, 166),
    "end": (51, 15, 194),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_4= {
    "offset": (62, 15, 289),
    "end": (27, 15, 322),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_5= {
    "offset": (-211, -2, 229),
    "end": (-229, -2, 233),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_6= {
    "offset": (-229, -2, 233),
    "end": (-239, -2, 306),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_7= {
    "offset": (-239, -2, 306),
    "end": (-101, -2, 402),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_8= {
    "offset": (27, 15, 151),
    "end": (40, 15, 163),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_9= {
    "offset": (79, 15, 288),
    "end": (66, 15, 288),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_10= {
    "offset": (5, 15, 335),
    "end": (-26, 15, 335),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }
race2_barricade_11= {
    "offset": (49, 15, 197),
    "end": (30, 15, 206),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_3], 
    "separator": "x"
    }









race_barricade_1= {
    "offset": (75, 15, 241.5),
    "end": (75, 15, 251),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_2], 
    "separator": "x"
    }
race_barricade_2= {
    "offset": (75.5, 15, 240.5),
    "end": (75.5, 15, 231),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_2], 
    "separator": "x"
    }
race_trash_1 = {
    "offset": (1, 0, 593),
    "face": (35, 0, 593),
    "race": [RaceModeNum.CHECKPOINT_2],
    "name": Prop.TRASH_BOXES}

race_trash_2 = {
    "offset": (1, 0, -120),
    "face": (-45, 0, -120),
    "race": [RaceModeNum.CHECKPOINT_2],
    "name": Prop.TRASH_BOXES}
    









uns_cone_1= {
    "offset": (-124, -1.5, 141),
    "end": (-156, -1.5, 165),
    "name": Prop.CONE,
    "race": [RaceModeNum.CHECKPOINT_1], 
    "separator": "x"
    }
uns_cone_2= {
    "offset": (-156, -1.5, 165),
    "end": (-223, -1.5, 170),
    "name": Prop.CONE,
    "race": [RaceModeNum.CHECKPOINT_1], 
    "separator": "x"
    }
uns_cone_3= {
    "offset": (-223, -1.5, 170),
    "end": (-223, -1.5, 232),
    "name": Prop.CONE,
    "race": [RaceModeNum.CHECKPOINT_1], 
    "separator": "x"
    }
uns_cone_4= {
    "offset": (-223, -1.5, 232),
    "end": (-211, -1.5, 245),
    "name": Prop.CONE,
    "race": [RaceModeNum.CHECKPOINT_1], 
    "separator": "x"
    }
uns_barricade_1= {
    "offset": (-40, 15.5, 278),
    "end": (1, 15.5, 278),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_1], 
    "separator": "6"
    }
uns_barricade_2= {
    "offset": (81, 15.5, 290),
    "end": (81, 15.5, 308),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CHECKPOINT_1], 
    "separator": "x"
    }
uns_glass_1= {
    "offset": (1, 15.5, 274),
    "face": (-5, 15.5, 274),
    "name": Prop.GLASS,
    "race": [RaceModeNum.CHECKPOINT_1], 
    "separator": "x"
    }










# / Snail Loop Props / #
snail_barricade_1= {
    "offset": (21, 19.5, 255),
    "end": (-18, 19.5, 255),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CIRCUIT_3], 
    "separator": "x"
    }
snail_barricade_2 = {
    "offset": (-18, 19.5, 211),
    "end": (-18, 19.5, 246),    
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CIRCUIT_3], 
    "separator": "x"}
snail_barricade_3 = {
    "offset": (21, 19.5, 255),
    "end": (21, 19.5, 211),
    "race": [RaceModeNum.CIRCUIT_3],
    "name": Prop.BARRICADE, 
    "separator": "x"}
snail_barricade_4 = {    
    "offset": (-18, 19.5, 211),
    "end": (21, 19.5, 211),
    "race": [RaceModeNum.CIRCUIT_3],
    "name": Prop.BARRICADE, 
    "separator": "x"
    } 
snail_barricade_5= {    
    "offset": (-25, 19.5, 255),
    "end": (-19, 19.5, 255),
    "race": [RaceModeNum.CIRCUIT_3],
    "name": Prop.BARRICADE, 
    "separator": "x"
    }                                                                    # Also possible: RaceModeNum.CIRCUIT_ALL


#######################################################



pp_beetle_1 = {
    "offset": (-1, 15, 183),
    "face": (-1, 15, 195),
    "name": PlayerCar.VW_BEETLE}


app_trailer_1 = {
    "offset": (-4, 15, 183),
    "face": (-4, 15, 195),
    "name": Prop.TRAILER}

app_trailer_2 = {
    "offset": (7, 15.25, 293),
    "face": (7, 15, 287),
    "name": Prop.TRAILER}

app_barricade_1 = {
    "offset": (12, 19.5, 222),
    "end": (-8, 19.5, 222),
    "name": Prop.BARRICADE, 
    "separator": "x"}
app_barricade_2 = {
    "offset": (-8, 19.5, 222),
    "end": (-8, 19.5, 242),
    "name": Prop.BARRICADE, 
    "separator": "x"}
app_barricade_3 = {
    "offset": (12, 19.5, 222),
    "end": (12, 19.5, 242),
    "name": Prop.BARRICADE, 
    "separator": "x"}
app_barricade_4 = {
    "offset": (-8, 19.5, 242),
    "end": (12, 19.5, 242),
    "name": Prop.BARRICADE, 
    "separator": "x"}
app_stop_1 = {
    "offset": (-140, 15, 237.4),
    "face": (-140, 15, 230),
    "name": Prop.WRONG_WAY}
app_phone_1 = {
    "offset": (4, 20, 234),
    "face": (8, 20, 234),
    "name": Prop.PHONE_BOOTH}
app_box_1 = {
    "offset": (-140, 15.2, 242),
    "face": (-140, 15.2, 246),
    "name": Prop.TRASH_BOXES}
app_box_2 = {
    "offset": (-140, 15.2, 231),
    "face": (-140, 15.2, 243),
    "name": Prop.TRASH_BOXES}
app_bench_1= {    
    "offset": (9, 1.5, -57),
    "end": (9, 1.5, 18),
    "face":(170000000, 0, 0),
    "name": Prop.BENCH, 
    "separator": "5"
    } 
app_bench_2= {    
    "offset": (-6, 1.5, -57),
    "end": (-6, 1.5, 15),
    "face":(-170000000, 0, 0),
    "name": Prop.BENCH, 
    "separator": "5"
    }  
app_bench_3= {    
    "offset": (9, 1.5, 532),
    "end": (9, 1.5, 460),
    "face":(170000000, 0, 0),
    "name": Prop.BENCH, 
    "separator": "5"
    } 
app_bench_4= {    
    "offset": (-6, 1.5, 532),
    "end": (-6, 1.5, 460),
    "face":(-170000000, 0, 0),
    "name": Prop.BENCH, 
    "separator": "5"
    }

dumpster_set = {
    "offset": (7, 15, 275),
    "face": (7, 15, 293),
    "name": Prop.DUMPSTER}


bridge_orange_buildling = {
    "offset": (35, 12.0, -70),
    "face": (35 * HUGE, 12.0, -70),
    "name": Prop.BRIDGE_SLIM
}

china_gate = {
    "offset": (0, 0.0, -20),
    "face": (1 * HUGE, 0.0, -20),
    "name": Prop.CHINATOWN_GATE,
    "race_mode": RaceMode.CIRCUIT,
    "race_num": 0  # Prop for CIRCUIT 0
}

# Put the non-randomized props here
prop_list = [app_trailer_1, app_trailer_2, dumpster_set,
              app_barricade_1, app_barricade_2, app_barricade_3,
                app_barricade_4, app_stop_1, app_phone_1, app_box_1,app_box_2,app_bench_1,app_bench_2,app_bench_3,app_bench_4,
                 snail_barricade_1,snail_barricade_2,snail_barricade_3,snail_barricade_4,
                  snail_barricade_5,uns_cone_1,uns_cone_2,uns_cone_3,uns_cone_4,uns_barricade_1,uns_barricade_2,uns_glass_1,
                   race_barricade_1,race_barricade_2,race_trash_1,race_trash_2,race2_barricade_1,race2_barricade_2,race2_barricade_3,
                    race2_barricade_4,race2_barricade_5,race2_barricade_6,race2_barricade_7,race2_barricade_8,race2_barricade_9,race2_barricade_10,
                     race2_barricade_11]


# Put the randomized props here (you will add them to the list "random props")
random_trees = {
    "offset_y": 15,
    "name": [Prop.TREE_WIDE] * 20
}
random_trees_1 = {
    "offset_y": 15,
    "name": [Prop.TREE_WIDE] * 20
}
random_trees_slim = {
    "offset_y": 15,
    "name": [Prop.TREE_SLIM] * 30
}  
random_trees_slim_1 = {
    "offset_y": 15,
    "name": [Prop.TREE_SLIM] * 30
}
random_trees_slim_2 = {
    "offset_y": 1,
    "name": [Prop.TREE_SLIM] * 35
}
random_trees_slim_3 = {
    "offset_y": 1,
    "name": [Prop.TREE_SLIM] * 35
}
random_sailboats = {
    "offset_y": -2,
    "name": [Prop.SAILBOAT] * 20
}

#random_cars = {
 #   "offset_y": 0.0,
#    "separator": 10.0,
 #   "name": [
  #      PlayerCar.VW_BEETLE, PlayerCar.CITY_BUS, PlayerCar.CADILLAC, PlayerCar.CRUISER, PlayerCar.FORD_F350,
   #     PlayerCar.FASTBACK, PlayerCar.MUSTANG99, PlayerCar.ROADSTER, PlayerCar.PANOZ_GTR_1, PlayerCar.SEMI
    #]
#}

# Configure the random props here
random_props = [
    
    #Trees around to the Building#
    {"seed": 123, "num_props": 1, "props_dict": random_trees, "x_range": (75, -72), "z_range": (124, 201)},
    {"seed": 123, "num_props": 1, "props_dict": random_trees_1, "x_range": (75, -72), "z_range": (350, 271)},
    {"seed": 341, "num_props": 1, "props_dict": random_trees_slim, "x_range": (75, -72), "z_range": (124, 201)},
    {"seed": 341, "num_props": 1, "props_dict": random_trees_slim_1, "x_range": (75, -72), "z_range": (350, 271)},
    
    #Spawn Area Trees#
    {"seed": 69, "num_props": 1, "props_dict": random_trees_slim_2, "x_range": (-5, -51), "z_range": (-59, 46)},
    {"seed": 69, "num_props": 1, "props_dict": random_trees_slim_3, "x_range": (8, 54), "z_range": (46, -59)},
    
    #The Parking Lot Green area (Away from Spawn)
    {"seed": 69, "num_props": 1, "props_dict": random_trees_slim_2, "x_range": (8, 54), "z_range": (533, 428)},
    {"seed": 69, "num_props": 1, "props_dict": random_trees_slim_3, "x_range": (-5, -51), "z_range": (426, 533)},
    
    #Sailboats#
    #{"seed": 27, "num_props": 4, "props_dict": random_sailboats, "x_range": (447, -419), "z_range": (-329, 812)},
    
    #{"seed": 1, "num_props": 2, "props_dict": random_cars, "x_range": (52, 138), "z_range": (-136, -68)}
]