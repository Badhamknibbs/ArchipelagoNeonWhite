# Locations are specific points that you would obtain an item at.
from BaseClasses import Location

from .info import LEVEL_INFO, MEDALS


class NWLocation(Location):
    game: str = "Neon White"
    starting_id: int = 500

nw_locations: dict[str, int] = {}

def neon_white_get_locations() -> dict[str, int]:
    global nw_locations
    if nw_locations:
        return nw_locations

    locations_dict: dict[str, int] = {}
    level_id = NWLocation.starting_id

    for (level, info) in LEVEL_INFO.items():
        if not info.sidequest:
            for medal in MEDALS:
                locations_dict[f"{level} {medal} Completion"] = level_id
                level_id += 1
            if not info.giftless:
                locations_dict[f"{level} Gift"] = level_id
                level_id += 1
        else:
            locations_dict[f"{level} Completion"] = level_id
            level_id += 1

    nw_locations = locations_dict
    return nw_locations


checks_in_sets_lvl = {
                         i.name: {
                             f"{i.name} {medal} Completion" for medal in MEDALS
                         } for i in LEVEL_INFO.values() if not i.sidequest
                     } | {
                         i.name: {
                             f"{i.name} Gift"
                         } for i in LEVEL_INFO.values() if not i.giftless
                     } | {
                         i.name: {
                             f"{i.name} Completion"
                         } for i in LEVEL_INFO.values() if i.sidequest
                     }
