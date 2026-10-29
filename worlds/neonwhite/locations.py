# Locations are specific points that you would obtain an item at.
from BaseClasses import Location

from .info import LEVEL_INFO, MEDALS, MISSION_INFO


class NWLocation(Location):
    game: str = "Neon White"

nw_locations: dict[str, int] = {}

def neon_white_get_locations() -> dict[str, int]:
    global nw_locations
    if nw_locations:
        return nw_locations

    locations_dict: dict[str, int] = {}
    mission_id = 0

    for mission in MISSION_INFO.values():
        level_id = 0
        for level in mission.levels:
            loc_id = 1 # movement bronze breaks if this is 0
            if not level.sidequest:
                for medal in MEDALS:
                    locations_dict[f"{level.name} {medal} Completion"] = mission_id + level_id + loc_id
                    loc_id += 1
                if not level.giftless:
                    locations_dict[f"{level.name} Gift"] = mission_id + level_id + loc_id
                    loc_id += 1
            else:
                locations_dict[f"{level.name} Completion"] = mission_id + level_id + loc_id
                loc_id += 1
            level_id += 10
        mission_id += 100

    nw_locations = locations_dict
    return nw_locations


checks_in_sets_lvl = {
                         i.name: {
                             f"{i.name} {medal} Completion" for medal in MEDALS
                         } | ({f"{i.name} Gift"} if not i.giftless else set())

                         for i in LEVEL_INFO.values() if not i.sidequest
                     } | {
                         i.name: {
                             f"{i.name} Completion"
                         } for i in LEVEL_INFO.values() if i.sidequest
                     }
