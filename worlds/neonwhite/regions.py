from BaseClasses import Region, MultiWorld
from .locations import NWLocation, neon_white_get_locations, neon_white_levels_checks, neon_white_levels_normal, \
    neon_white_levels_giftless, neon_white_levels_sidequests, NWLocation
from .options import NeonWhiteOptions
import itertools


def create_regions(player: int, multiworld: MultiWorld, options: NeonWhiteOptions):
    # 121 levels split into 11 missions of 11 levels, differing from the base game
    mission_list = [
        "Mission 1",
        "Mission 2",
        "Mission 3",
        "Mission 4",
        "Mission 5",
        "Mission 6",
        "Mission 7",
        "Mission 8",
        "Mission 9",
        "Mission 10",
        "Mission 11"
    ]

    heaven_regions: list[Region] = [Region("Central Heaven", player, multiworld, None)]

    neon_white_locations = neon_white_get_locations()

    # Create regions and add locations
    for mission in mission_list:
        heaven_regions.append(Region(mission, player, multiworld, mission))

    for level in neon_white_levels_normal:
        check_region = Region(level, player, multiworld, None)
        for check in neon_white_levels_checks:
            check_name = level + " " + check
            new_location = NWLocation(player, check_name, neon_white_locations[check_name], check_region)
            check_region.locations.append(new_location)
        heaven_regions.append(check_region)

    for level in itertools.chain(neon_white_levels_giftless, neon_white_levels_sidequests):
        check_region = Region(level, player, multiworld, None)
        check_name = level + " Completion"
        new_location = NWLocation(player, check_name, neon_white_locations[check_name], check_region)
        check_region.locations.append(new_location)
        heaven_regions.append(check_region)

    multiworld.regions += heaven_regions
