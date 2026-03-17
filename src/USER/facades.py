from src.constants.facades import Facade, FcdFlags


# ─── Orange building (box formation) ─────────────────────────────────────────

orange_building_one = {
    "flags": FcdFlags.FRONT | FcdFlags.BRIGHT,
    "offset": (-10.0, 0.0, -50.0),
    "end": (10.0, 0.0, -50.0),
    "separator": 10.0,
    "name": Facade.BUILDING_OLDTOWN_2,
    "axis": "x",
}

orange_building_two = {
    "flags": FcdFlags.FRONT | FcdFlags.BRIGHT,
    "offset": (10.0, 0.0, -70.0),
    "end": (-10.0, 0.0, -70.0),
    "separator": 10.0,
    "name": Facade.BUILDING_OLDTOWN_2,
    "axis": "x",
}

orange_building_three = {
    "flags": FcdFlags.FRONT | FcdFlags.BRIGHT,
    "offset": (-10.0, 0.0, -70.0),
    "end": (-10.0, 0.0, -50.0),
    "separator": 10.0,
    "name": Facade.BUILDING_OLDTOWN_2,
    "axis": "z",
}

orange_building_four = {
    "flags": FcdFlags.FRONT | FcdFlags.BRIGHT,
    "offset": (10.0, 0.0, -50.0),
    "end": (10.0, 0.0, -70.0),
    "separator": 10.0,
    "name": Facade.BUILDING_OLDTOWN_2,
    "axis": "z",
}


# ─── Highway row (z-axis, left side) ─────────────────────────────────────────

white_hotel_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-160.0, 0.0, -80.0),
    "end": (-160.0, 0.0, 20.0),
    "separator": 25.0,
    "name": Facade.BUILDING_RESIDENTIAL_5,
    "axis": "z",
}

red_hotel_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-160.0, 0.0, 35.0),
    "end": (-160.0, 0.0, 135.0),
    "separator": 20.0,
    "name": Facade.BUILDING_DOWNTOWN_6,
    "axis": "z",
}

grey_hotel_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-160.0, 0.0, 135.0),
    "end": (-160.0, 0.0, 235.0),
    "separator": 33.33,
    "name": Facade.SKYSCRAPER_DOWNTOWN_4,
    "axis": "z",
}

garage_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-160.0, 0.0, 235.0),
    "end": (-160.0, 0.0, 320.0),
    "separator": 40.0,
    "name": Facade.WAREHOUSE_INDUSTRIAL_2,
    "axis": "z",
}


# ─── Highway row (z-axis, further left) ──────────────────────────────────────

apartment_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-200.0, 0.0, 300.0),
    "end": (-200.0, 0.0, 320.0),
    "separator": 20.0,
    "scale": 20,
    "name": Facade.CONDO_HILLSIDE_3_UNUSED,
    "axis": "z",
}

pizza_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-200.0, 0.0, 246.0),
    "end": (-200.0, 0.0, 266.0),
    "separator": 20.0,
    "scale": 20,
    "name": Facade.SHOP_HILLSIDE_PIZZA_UNUSED,
    "axis": "z",
}

suitstore_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-200.0, 0.0, 218.0),
    "end": (-200.0, 0.0, 248.0),
    "separator": 30.0,
    "scale": 30,
    "name": Facade.SHOP_DOWNTOWN_SUIT,
    "axis": "z",
}

warehouse_four_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-200.0, 0.0, 188.0),
    "end": (-200.0, 0.0, 218.0),
    "separator": 30.0,
    "scale": 30,
    "name": Facade.WAREHOUSE_HILLSIDE_4,
    "axis": "z",
}

warehouse_three_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-200.0, 0.0, 158.0),
    "end": (-200.0, 0.0, 188.0),
    "separator": 30.0,
    "scale": 30,
    "name": Facade.WAREHOUSE_HILLSIDE_3_UNUSED,
    "axis": "z",
}

supermarket_highway = {
    "flags": FcdFlags.ALL_SIDES,
    "offset": (-200.0, 0.0, 113.0),
    "end": (-200.0, 0.0, 143.0),
    "separator": 30.0,
    "scale": 30,
    "name": Facade.SUPERMARKET_THELOOP,
    "axis": "z",
}


# ─── Facade list ──────────────────────────────────────────────────────────────

facade_list = [
    orange_building_one, orange_building_two, orange_building_three, orange_building_four,
    white_hotel_highway, red_hotel_highway, grey_hotel_highway, garage_highway,
    apartment_highway, pizza_highway, suitstore_highway,
    warehouse_four_highway, warehouse_three_highway, supermarket_highway,
]