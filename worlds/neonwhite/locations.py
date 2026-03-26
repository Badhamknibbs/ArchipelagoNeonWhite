# Locations are specific points that you would obtain an item at.
import itertools
from enum import IntFlag, auto, IntEnum
import csv

from BaseClasses import Location


class NWLocation(Location):
    game: str = "Neon White"


neon_white_levels_normal = [
    "Movement",
    "Pummel",
    "Gunner",
    "Cascade",
    "Elevate",
    "Bounce",
    "Purify",
    "Climb",
    "Fasttrack",
    "Glass Port",
    "Take Flight",
    "Godspeed",
    "Dasher",
    "Thrasher",
    "Outstretched",
    "Smackdown",
    "Catwalk",
    "Fastlane",
    "Distinguish",
    "Dancer",
    "Guardian",
    "Stomp",
    "Jumper",
    "Dash Tower",
    "Descent",
    "Driller",
    "Canals",
    "Sprint",
    "Mountain",
    "Superkinetic",
    "Arrival",
    "Forgotten City",
    "Fireball",
    "Ringer",
    "Cleaner",
    "Warehouse",
    "Boom",
    "Streets",
    "Steps",
    "Demolition",
    "Arcs",
    "Apartment",
    "Hanging Gardens",
    "Tangled",
    "Waterworks",
    "Killswitch",
    "Falling",
    "Shocker",
    "Bouquet",
    "Prepare",
    "Triptrack",
    "Race",
    "Bubble",
    "Shield",
    "Overlook",
    "Pop",
    "Minefield",
    "Mimic",
    "Trigger",
    "Greenhouse",
    "Sweep",
    "Fuse",
    "Heaven's Edge",
    "Zipline",
    "Swing",
    "Chute",
    "Crash",
    "Ascent",
    "Straightaway",
    "Firecracker",
    "Streak",
    "Mirror",
    "Escalation",
    "Bolt",
    "Godstreak",
    "Plunge",
    "Mayhem",
    "Barrage",
    "Estate",
    "Trapwire",
    "Ricochet",
    "Fortress",
    "Holy Ground",
    "Spree",
    "Breakthrough",
    "Glide",
    "Closer",
    "Hike",
    "Switch",
    "Access",
    "Congregation",
    "Sequence",
    "Marathon",
]

neon_white_levels_giftless = [
    "The Clocktower",
    "The Third Temple",
    "Sacrifice",
    "Absolution"
]

neon_white_levels_sidequests = [  # No gifts either
    "Elevate Traversal I",
    "Elevate Traversal II",
    "Purify Traversal",
    "Godspeed Traversal",
    "Stomp Traversal",
    "Fireball Traversal",
    "Dominion Traversal",
    "Book of Life Traversal",
    "Doghouse",
    "Choker",
    "Chain",
    "Hellevator",
    "Razor",
    "All Seeing Eye",
    "Resident Saw I",
    "Resident Saw II",
    "Sunset Flip Powerbomb",
    "Balloon Mountain",
    "Climbing Gym",
    "Fisherman Suplex",
    "STF",
    "Arena",
    "Attitude Adjustment",
    "Rocket"
]

neon_white_levels_checks = [
    "Completion",
    "Gift"
]


def neon_white_level_name_internal(level: str) -> str:
    match level:
        case "Movement": return "TUT_MOVEMENT"
        case "Pummel": return "TUT_SHOOTINGRANGE"
        case "Gunner": return "SLUGGER"
        case "Cascade": return "TUT_FROG"
        case "Elevate": return "TUT_JUMP"
        case "Bounce": return "GRID_TUT_BALLOON"
        case "Purify": return "TUT_BOMB2"
        case "Climb": return "TUT_BOMBJUMP"
        case "Fasttrack": return "TUT_FASTTRACK"
        case "Glass Port": return "GRID_PORT"
        case "Take Flight": return "GRID_PAGODA"
        case "Godspeed": return "TUT_RIFLE"
        case "Dasher": return "TUT_RIFLEJOCK"
        case "Thrasher": return "TUT_DASHENEMY"
        case "Outstretched": return "GRID_JUMPDASH"
        case "Smackdown": return "GRID_SMACKDOWN"
        case "Catwalk": return "GRID_MEATY_BALLOONS"
        case "Fastlane": return "GRID_FAST_BALLOON"
        case "Distinguish": return "GRID_DRAGON2"
        case "Dancer": return "GRID_DASHDANCE"
        case "Guardian": return "TUT_GUARDIAN"
        case "Stomp": return "TUT_UZI"
        case "Jumper": return "TUT_JUMPER"
        case "Dash Tower": return "TUT_BOMB"
        case "Descent": return "GRID_DESCEND"
        case "Driller": return "GRID_STAMPEROUT"
        case "Canals": return "GRID_CRUISE"
        case "Sprint": return "GRID_SPRINT"
        case "Mountain": return "GRID_MOUNTAIN"
        case "Superkinetic": return "GRID_SUPERKINETIC"
        case "Arrival": return "GRID_ARRIVAL"
        case "Forgotten City": return "FLOATING"
        case "The Clocktower": return "GRID_BOSS_YELLOW"
        case "Fireball": return "GRID_HOPHOP"
        case "Ringer": return "GRID_RINGER_TUTORIAL"
        case "Cleaner": return "GRID_RINGER_EXPLORATION"
        case "Warehouse": return "GRID_HOPSCOTCH"
        case "Boom": return "GRID_BOOM"
        case "Streets": return "GRID_SNAKE_IN_MY_BOOT"
        case "Steps": return "GRID_FLOCK"
        case "Demolition": return "GRID_BOMBS_AHOY"
        case "Arcs": return "GRID_ARCS"
        case "Apartment": return "GRID_APARTMENT"
        case "Hanging Gardens": return "TUT_TRIPWIRE"
        case "Tangled": return "GRID_TANGLED"
        case "Waterworks": return "GRID_HUNT"
        case "Killswitch": return "GRID_CANNONS"
        case "Falling": return "GRID_FALLING"
        case "Shocker": return "TUT_SHOCKER2"
        case "Bouquet": return "TUT_SHOCKER"
        case "Prepare": return "GRID_PREPARE"
        case "Triptrack": return "GRID_TRIPMAZE"
        case "Race": return "GRID_RACE"
        case "Bubble": return "TUT_FORCEFIELD2"
        case "Shield": return "GRID_SHIELD"
        case "Overlook": return "SA L VAGE2"
        case "Pop": return "GRID_VERTICAL"
        case "Minefield": return "GRID_MINEFIELD"
        case "Mimic": return "TUT_MIMIC"
        case "Trigger": return "GRID_MIMICPOP"
        case "Greenhouse": return "GRID_SWARM"
        case "Sweep": return "GRID_SWITCH"
        case "Fuse": return "GRID_TRAPS2"
        case "Heavens Edge": return "TUT_ROCKETJUMP"
        case "Zipline": return "TUT_ZIPLINE"
        case "Swing": return "GRID_CLIMBANG"
        case "Chute": return "GRID_ROCKETUZI"
        case "Crash": return "GRID_CRASHLAND"
        case "Ascent": return "GRID_ESCALATE"
        case "Straightaway": return "GRID_SPIDERCLAUS"
        case "Firecracker": return "GRID_FIRECRACKER_2"
        case "Streak": return "GRID_SPIDERMAN"
        case "Mirror": return "GRID_DESTRUCTION"
        case "Escalation": return "GRID_HEAT"
        case "Bolt": return "GRID_BOLT"
        case "Godstreak": return "GRID_PON"
        case "Plunge": return "GRID_CHARGE"
        case "Mayhem": return "GRID_MIMICFINALE"
        case "Barrage": return "GRID_BARRAGE"
        case "Estate": return "GRID_1GUN"
        case "Trapwire": return "GRID_HECK"
        case "Ricochet": return "GRID_ANTFARM"
        case "Fortress": return "GRID_FORTRESS"
        case "Holy Ground": return "GRID_GODTEMPLE_ENTRY"
        case "The Third Temple": return "GRID_BOSS_GODSDEATHTEMPLE"
        case "Spree": return "GRID_EXTERMINATOR"
        case "Breakthrough": return "GRID_FEVER"
        case "Glide": return "GRID_SKIPSLIDE"
        case "Closer": return "GRID_CLOSER"
        case "Hike": return "GRID_HIKE"
        case "Switch": return "GRID_SKIP"
        case "Access": return "GRID_CEILING"
        case "Congregation": return "GRID_BOOP"
        case "Sequence": return "GRID_TRIPRAP"
        case "Marathon": return "GRID_ZIPRAP"
        case "Sacrifice": return "TUT_ORIGIN"
        case "Absolution": return "GRID_BOSS_RAPTURE"
        case "Elevate Traversal I": return "SIDEQUEST_OBSTACLE_PISTOL"
        case "Elevate Traversal II": return "SIDEQUEST_OBSTACLE_PISTOL_SHOOT"
        case "Purify Traversal": return "SIDEQUEST_OBSTACLE_MACHINEGUN"
        case "Godspeed Traversal": return "SIDEQUEST_OBSTACLE_RIFLE_2"
        case "Stomp Traversal": return "SIDEQUEST_OBSTACLE_UZI2"
        case "Fireball Traversal": return "SIDEQUEST_OBSTACLE_SHOTGUN"
        case "Dominion Traversal": return "SIDEQUEST_OBSTACLE_ROCKETLAUNCHER"
        case "Book of Life Traversal": return "SIDEQUEST_RAPTURE_QUEST"
        case "Doghouse": return "SIDEQUEST_DODGER"
        case "Choker": return "GRID_GLASSPATH"
        case "Chain": return "GRID_GLASSPATH2"
        case "Hellevator": return "GRID_HELLVATOR"
        case "Razor": return "GRID_GLASSPATH3"
        case "All Seeing Eye": return "SIDEQUEST_ALL_SEEING_EYE"
        case "Resident Saw I": return "SIDEQUEST_RESIDENTSAWB"
        case "Resident Saw II": return "SIDEQUEST_RESIDENTSAW"
        case "Sunset Flip Powerbomb": return "SIDEQUEST_SUNSET_FLIP_POWERBOMB"
        case "Balloon Mountain": return "GRID_BALLOONLAIR"
        case "Climbing Gym": return "SIDEQUEST_BARREL_CLIMB"
        case "Fisherman Suplex": return "SIDEQUEST_FISHERMAN_SUPLEX"
        case "STF": return "SIDEQUEST_STF"
        case "Arena": return "SIDEQUEST_ARENASIXNINE"
        case "Attitude Adjustment": return "SIDEQUEST_ATTITUDE_ADJUSTMENT"
        case "Rocket": return "SIDEQUEST_ROCKETGODZ"
    return None


def neon_white_get_locations() -> dict[str, int]:
    locations_dict: dict[str, int] = {}
    level_id = 500
    for level in neon_white_levels_normal:
        locations_dict[level + " Completion"] = level_id
        level_id += 1
        locations_dict[level + " Gift"] = level_id
        level_id += 1
    for level in itertools.chain(neon_white_levels_giftless, neon_white_levels_sidequests):
        locations_dict[level + " Completion"] = level_id
        level_id += 1

    return locations_dict


checks_in_sets_lvl = {
                         lvl: {
                             lvl + " " + check for check in neon_white_levels_checks
                         } for lvl in neon_white_levels_normal
                     } | {
                         lvl: {
                             lvl + " Completion"
                         } for lvl in itertools.chain(neon_white_levels_giftless, neon_white_levels_sidequests)
                     }