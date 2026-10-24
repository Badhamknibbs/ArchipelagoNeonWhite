from collections.abc import Iterator
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
                check_names = [f"{level.name} {medal.name.title()} Completion" for medal in world.medals]
                if options.gifts and not level.giftless:
                    check_names.append(f"{level.name} Gift")

                check_region.locations.extend([
                    NWLocation(world.player, check_name, neon_white_locations[check_name], check_region)
                    for check_name in check_names
                ])
            else:
                check_name = f"{level.name} Completion"
                new_location = NWLocation(world.player, check_name, neon_white_locations[check_name], check_region)
                #new_location.progress_type = LocationProgressType.PRIORITY
                check_region.locations.append(new_location)

            mission_region.connect(check_region, f"{mission_region.name} to {check_region.name}")

            level.regions[world.player] = check_region
            heaven_regions.append(check_region)

    multiworld.regions += heaven_regions

def level_rando(world: "NeonWhiteWorld", level_req: dict[str, set[str]], cards: set[str], k: int) -> Iterator[str]:
    variance = world.options.level_gradient.value / 100.0

    weights = {l: float(len(req - cards)) for l, req in level_req.items()}
    if variance:
        maxweights = max(x for x in weights.values())
        for l in weights:
            weights[l] *= 1 - variance
            weights[l] += world.random.random() * maxweights * variance

    change: set[str] = set()
    diffmaxkey = lambda itm: len(itm[1])

    for _ in range(k):
        if not level_req:
            yield "Absolution"
            return
        if change:
            diff = list[str]()
            for l, c in level_req.items():
                if not c.isdisjoint(change):
                    level_req[l] = c - change
                    diff.append(l)
            if diff:
                # recalculate weights only for diff
                # this has the effect of keeping things more 'themed'
                if variance:
                    maxweights = len(max(diff, key=diffmaxkey)[1])
                    for l in diff:
                        weights[l] = (1 - variance) * len(level_req[l]) + world.random.random() * maxweights * variance
                else:
                    for l in diff:
                        weights[l] = float(len(level_req[l]))
            change.clear()

        # https://stackoverflow.com/a/3282904
        # typechecker don't like .get
        least = min(weights, key=weights.__getitem__)
        # print(least, len(cards), level_req[least])
        newc = level_req[least]
        change = newc - cards
        cards |= newc
        del level_req[least]
        del weights[least]
        yield least
