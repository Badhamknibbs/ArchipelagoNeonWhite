# Locations are specific points that you would obtain an item at.
from BaseClasses import Location

from .info import LEVEL_INFO, MEDALS


class NWLocation(Location):
    game: str = "Neon White"
    starting_id: int = 500


def neon_white_get_locations() -> dict[str, int]:
    locations_dict: dict[str, int] = {}
    level_id = NWLocation.starting_id

    for (level, info) in LEVEL_INFO.items():
        if not info.sidequest:
            for medal in MEDALS:
                locations_dict[level + " " + medal + " Completion"] = level_id
                level_id += 1
            if not info.giftless:
                locations_dict[level + " Gift"] = level_id
                level_id += 1
        else:
            locations_dict[level + " Completion"] = level_id
            level_id += 1

    return locations_dict


checks_in_sets_lvl = {
                         i.name: {
                             i.name + " " + medal + " Completion" for medal in MEDALS
                         } for i in LEVEL_INFO.values() if not i.sidequest
                     } | {
                         i.name: {
                             i.name + " Gift"
                         } for i in LEVEL_INFO.values() if not i.giftless
                     } | {
                         i.name: {
                             i.name + " Completion"
                         } for i in LEVEL_INFO.values() if i.sidequest
                     }
