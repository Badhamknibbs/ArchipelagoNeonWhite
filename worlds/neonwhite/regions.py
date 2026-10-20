from typing import TYPE_CHECKING

from BaseClasses import MultiWorld, Region

from .locations import (
    NWLocation,
    neon_white_get_locations,
)
from .options import NeonWhiteOptions

if TYPE_CHECKING:
    from . import NeonWhiteWorld


def create_regions(multiworld: MultiWorld, world: "NeonWhiteWorld", options: NeonWhiteOptions):
    central = Region("Central Heaven", world.player, multiworld, None)
    heaven_regions: list[Region] = [central]

    neon_white_locations = neon_white_get_locations()

    # Create regions and add locations
    for mission in world.missions:
        mission_region = Region(mission.alias or mission.name, world.player, multiworld)
        central.connect(mission_region, f"{central.name} to {mission_region.name}")

        mission.regions[world.player] = mission_region
        heaven_regions.append(mission_region)

        for level in mission.levels:
            check_region = Region(level.alias or level.name, world.player, multiworld)
            if not level.sidequest:
                for medal in options.medal_select:
                    check_name: str = level.name + " " + medal.title() + " Completion"
                    new_location = NWLocation(world.player, check_name, neon_white_locations[check_name], check_region)
                    # Make the highest medal a priority location
                    #if medal == options.medal_cap - 1: new_location.progress_type = LocationProgressType.PRIORITY
                    check_region.locations.append(new_location)
                if options.gifts and not level.giftless:
                    check_name = level.name + " Gift"
                    new_location = NWLocation(world.player, check_name, neon_white_locations[check_name], check_region)
                    #new_location.progress_type = LocationProgressType.PRIORITY
                    check_region.locations.append(new_location)
            else:
                check_name = level.name + " Completion"
                new_location = NWLocation(world.player, check_name, neon_white_locations[check_name], check_region)
                #new_location.progress_type = LocationProgressType.PRIORITY
                check_region.locations.append(new_location)

            mission_region.connect(check_region, f"{mission_region.name} to {check_region.name}")

            level.regions[world.player] = check_region
            heaven_regions.append(check_region)

    multiworld.regions += heaven_regions
