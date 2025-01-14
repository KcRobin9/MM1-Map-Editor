from src.Constants.races import TimeOfDay, Weather


lighting_configs = [
    {
        # Custom lighting config for Night and Clear (purple color)
        "time_of_day": TimeOfDay.NIGHT,
        "weather": Weather.CLEAR,
        "sun_pitch": 10.0,
        "sun_color": (40.0, 0.0, 40.0),
        "fill_1_pitch": 10.0,
        "fill_1_color": (40.0, 0.0, 40.0),
        "fill_2_pitch": 10.0,
        "fill_2_color": (40.0, 0.0, 40.0),
    },
    {   
        # Actual lighting config for Evening and Cloudy
        "time_of_day": TimeOfDay.EVENING,
        "weather": Weather.CLOUDY,
        "sun_heading": 3.14,
        "sun_pitch": 0.65,
        "sun_color": (1.0, 0.6, 0.3),
        "fill_1_heading": -2.5,
        "fill_1_pitch": 0.45,
        "fill_1_color": (0.8, 0.9, 1.0),
        "fill_2_heading": 0.0,
        "fill_2_pitch": 0.45,
        "fill_2_color": (0.75, 0.8, 1.0),
        "ambient_color": (0.1, 0.1, 0.2),
        "fog_end": 600.0,
        "fog_color": (230.0, 100.0, 35.0),
        "shadow_alpha": 180.0,
        "shadow_color": (15.0, 20.0, 30.0)
    }
]