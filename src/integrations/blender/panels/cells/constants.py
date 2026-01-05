CELL_IMPORT = [
    (str(Room.DEFAULT), "Default", "", "", Room.DEFAULT),
    (str(Room.TUNNEL), "Tunnel", "", "", Room.TUNNEL),
    (str(Room.INDOORS), "Indoors", "", "", Room.INDOORS),
    (str(Room.DRIFT), "Drift", "", "", Room.DRIFT),
    (str(Room.NO_SKIDS), "No Skids", "", "", Room.NO_SKIDS)
    ]

CELL_EXPORT = {
    str(Room.TUNNEL): "Room.TUNNEL",
    str(Room.INDOORS): "Room.INDOORS",
    str(Room.DRIFT): "Room.DRIFT",
    str(Room.NO_SKIDS): "Room.NO_SKIDS"
}