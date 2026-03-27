import csv
import itertools
from enum import IntEnum, IntFlag, auto
from math import floor

from . import data
from BaseClasses import MultiWorld, CollectionState
from worlds.AutoWorld import World
from worlds.generic.Rules import set_rule, add_rule
from worlds.neonwhite import NeonWhiteOptions
from worlds.neonwhite.locations import neon_white_levels_giftless, neon_white_levels_normal, \
    neon_white_levels_sidequests
from .items import get_items_from_category


class Difficulty(IntEnum):
    Easy = 1
    Normal = 2
    Hard = 3
    Brutal = 4

class Medal(IntEnum):
    Bronze = 0
    Silver = 1
    Gold = 2
    Ace = 3
    Dev = 4
    Gift = 5


class LevelRequirements(IntFlag):
    FistOnly = 0
    Katana = auto()
    PurifyFire = auto()
    PurifyDiscard = auto()
    ElevateFire = auto()
    ElevateDiscard = auto()
    GodspeedFire = auto()
    GodspeedDiscard = auto()
    StompFire = auto()
    StompDiscard = auto()
    FireballFire = auto()
    FireballDiscard = auto()
    DominionFire = auto()
    DominionDiscard = auto()
    BookOfLife = auto()


# This only represents a single difficulty
class LevelRequirementSet:
    def __init__(self, levels: list[str]):
        # String is the level name, list is 0..5, in order: dev,ace,gold,bronze,silver,gift
        self.requirements = dict[str, list[set[LevelRequirements]]]()
        for level in levels:
            new_list = self.requirements[level] = list[set[LevelRequirements]]()
            new_list.append(set[LevelRequirements]())
            new_list.append(set[LevelRequirements]())
            new_list.append(set[LevelRequirements]())
            new_list.append(set[LevelRequirements]())
            new_list.append(set[LevelRequirements]())
            new_list.append(set[LevelRequirements]())

    # Note - Medal 0-4 is dev-bronze, 5 is gift
    # Cards are what is available at that point
    def can_complete_level(self, level:str, medal:Medal, cards:LevelRequirements) -> bool:
        for solution in self.requirements[level][medal]:
            # Bitwise check, e.g. 0001 & 1111 == 0001, success; 1001 & 0101 == 0001, failure
            # If Fist-Only is a solution, & will return 0 (because it's all zeroes) and thus will == 0, always success
            if solution & cards == solution:
                return True
        return False

    def get_necessary_items(self, level:str, medal:Medal) -> list[list[str]]:
        required_cards = list[list[str]]()
        for solution in self.requirements[level][medal]:
            solution_cards = list[str]()
            if solution & LevelRequirements.Katana: solution_cards.append("Katana")
            if solution & LevelRequirements.PurifyFire: solution_cards.append("Purify - Fire")
            if solution & LevelRequirements.PurifyDiscard: solution_cards.append("Purify - Discard")
            if solution & LevelRequirements.ElevateFire: solution_cards.append("Elevate - Fire")
            if solution & LevelRequirements.ElevateDiscard: solution_cards.append("Elevate - Discard")
            if solution & LevelRequirements.GodspeedFire: solution_cards.append("Godspeed - Fire")
            if solution & LevelRequirements.GodspeedDiscard: solution_cards.append("Godspeed - Discard")
            if solution & LevelRequirements.StompFire: solution_cards.append("Stomp - Fire")
            if solution & LevelRequirements.StompDiscard: solution_cards.append("Stomp - Discard")
            if solution & LevelRequirements.FireballFire: solution_cards.append("Fireball - Fire")
            if solution & LevelRequirements.FireballDiscard: solution_cards.append("Fireball - Discard")
            if solution & LevelRequirements.DominionFire: solution_cards.append("Dominion - Fire")
            if solution & LevelRequirements.DominionDiscard: solution_cards.append("Dominion - Discard")
            if solution & LevelRequirements.BookOfLife: solution_cards.append("Book of Life")
            required_cards.append(solution_cards)
        return required_cards



def string_to_level_req_flag(level: str) -> LevelRequirements:
    match level:
        case "Kf":
            return LevelRequirements.Katana
        case "Pf":
            return LevelRequirements.PurifyFire
        case "Pd":
            return LevelRequirements.PurifyDiscard
        case "Ef":
            return LevelRequirements.ElevateFire
        case "Ed":
            return LevelRequirements.ElevateDiscard
        case "Gf":
            return LevelRequirements.GodspeedFire
        case "Gd":
            return LevelRequirements.GodspeedDiscard
        case "Sf":
            return LevelRequirements.StompFire
        case "Sd":
            return LevelRequirements.StompDiscard
        case "Ff":
            return LevelRequirements.FireballFire
        case "Fd":
            return LevelRequirements.FireballDiscard
        case "Df":
            return LevelRequirements.DominionFire
        case "Dd":
            return LevelRequirements.DominionDiscard
        case "Bd":
            return LevelRequirements.BookOfLife
        case _:
            # Unexpected symbol/fist only
            return LevelRequirements.FistOnly

def import_csv_to_data(diff: Difficulty) -> LevelRequirementSet:
    # See archipelago requirements sheet for formatting
    from importlib.resources import files
    file = files(data).joinpath("nw_cr.csv").open()
    csv_reader = csv.reader(file)
    csv_iter = iter(csv_reader)
    # Grab names, cells are merged and encompass the 4 difficulties so only take every multiple of 4
    level_names: list[str] = next(csv_iter)[0::4]
    new_requirements = LevelRequirementSet(level_names)  # Return value that will be filled
    diff_idx = 0  # 0 == Dev, 1 == Ace, ... 5 == Gift
    for row in csv_iter:
        for i in range(0, len(level_names)):
            level_name = level_names[i]
            # First copy any requirements from the medal above (unless it's the gift row)
            # Doesn't matter if there's mixed combos, that's dealt with (e.g. Ef and Ef+Ed can exist together)
            if diff_idx != 5:
                for j in range(0, diff_idx):
                    new_requirements.requirements[level_name][diff_idx] |= new_requirements.requirements[level_name][j]
            # Copy requirements from all easier difficulties
            # Requirements are checked as a "can beat x with these weapons?" so this works
            for j in range(0, diff):
                cell = row[(i * 4) + j]
                # F means fist completable, no requirements
                if cell == "F":
                    new_requirements.requirements[level_name][diff_idx].add(LevelRequirements.FistOnly)
                else:
                    for solution in cell.split('|'):
                        requirements_aggregate = LevelRequirements(LevelRequirements.FistOnly)
                        for requirement in solution.split(","):
                            requirements_aggregate |= string_to_level_req_flag(requirement)
                        if requirements_aggregate != LevelRequirements.FistOnly:
                            new_requirements.requirements[level_name][diff_idx].add(requirements_aggregate)
        diff_idx = diff_idx + 1
    return new_requirements

# Actual functions related to rules start here
def level_rando(world: World, requirements: LevelRequirementSet) -> list[str]:
    # TODO: Make this smarter, e.g. fill levels on a gradient from smallest minimum requirement to most
    rando_level_order = []

    level_queue = neon_white_levels_normal + neon_white_levels_giftless + neon_white_levels_sidequests
    level_queue.remove("Absolution") # This will always be placed at the end

    # Place 2 levels where the gift and gold medal can be obtained Fist-Only at the very start
    fist_only_levels = []
    for level in level_queue:
        if requirements.can_complete_level(level, Medal.Gold, LevelRequirements.FistOnly) and requirements.can_complete_level(level, Medal.Gift, LevelRequirements.FistOnly):
            fist_only_levels.append(level)
    world.random.shuffle(fist_only_levels)
    for i in range(2):
        rando_level_order.append(fist_only_levels[i])
        level_queue.remove(fist_only_levels[i])

    # Shuffle the rest, append, then put Absolution at the end
    world.random.shuffle(level_queue)
    rando_level_order.extend(level_queue)
    rando_level_order.append("Absolution")
    return rando_level_order

def can_complete_medal(state: CollectionState, player:int, requirements:list[list[str]]):
    if not requirements: return True # No requirements, technically unexpected but catches odd cases
    for solution in requirements:
        if state.has_all(solution, player): return True
    return False

# Mission is zero-indexed
def get_required_rank_for_mission(total_rank_count: int, mission:int) -> int:
    # TODO: Figure out a nice formula, for now to fix fill issues just make it super easy
    return mission
    # Neon rank requirement is exponential, requiring a tiny number of neon ranks for the first missions but quickly increasing
    mission_fraction = mission / 11
    lenience_value = 10
    normal_value = (pow(lenience_value, mission_fraction) - 1) / (lenience_value - 1)
    return floor(total_rank_count * normal_value)

def set_rules(multiworld: MultiWorld, world: World, options: NeonWhiteOptions, total_rank_count:int):
    requirements = import_csv_to_data(options.difficulty)

    if not world.ordered_levels:
        world.ordered_levels = level_rando(world, requirements)

    # Place half of the relevant discard abilities into the early items pool to alleviate fill errors
    # TODO find a nice balance, temporarily use all to make generation easy
    relevant_discards: set[str] = set()
    for i in range(12):
        for solution in itertools.chain(requirements.get_necessary_items(world.ordered_levels[i], Medal.Gold), requirements.get_necessary_items(world.ordered_levels[i], Medal.Gift)):
            for card in solution:
                if "Discard" in card or "Book of Life" in card:
                    relevant_discards.add(card)
    relevant_discards_list = list(relevant_discards)
    world.random.shuffle(relevant_discards_list)
    for i in range(floor(len(relevant_discards_list) / 1)):
        multiworld.local_early_items[world.player][relevant_discards_list[i]] = 1

    central_heaven = multiworld.get_region("Central Heaven", world.player)
    # Connect central heaven to every mission
    for i in range(1, 12):
        mission_region = multiworld.get_region(f"Mission {i}", world.player)
        entrance_name = f"Central Heaven to Mission {i}"
        central_heaven.connect(mission_region, entrance_name)
        if i != 1:
            required_neon_rank_count = get_required_rank_for_mission(total_rank_count, i)
            add_rule(multiworld.get_entrance(entrance_name, world.player), lambda state: state.has("Neon Rank", world.player, required_neon_rank_count))

        # Connect each mission to the levels they contain
        for j in range(11):
            level_name = world.ordered_levels[((i - 1) * 11) + j]
            mission_region.connect(multiworld.get_region(level_name, world.player), f"{mission_region.name} to {level_name}")
            if level_name in neon_white_levels_normal:
                set_rule(multiworld.get_location(level_name + " Completion", world.player), lambda state: can_complete_medal(state, world.player, requirements.get_necessary_items(level_name, Medal.Gold)))
                set_rule(multiworld.get_location(level_name + " Gift", world.player), lambda state: can_complete_medal(state, world.player, requirements.get_necessary_items(level_name, Medal.Gift)))
            else:
                set_rule(multiworld.get_location(level_name + " Completion", world.player), lambda state: can_complete_medal(state, world.player, requirements.get_necessary_items(level_name, Medal.Dev)))

    multiworld.completion_condition[world.player] = lambda state: state.has("Absolution Completion", world.player)

    from Utils import visualize_regions
    visualize_regions(central_heaven, "neon_white_regions.puml")