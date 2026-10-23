from dataclasses import dataclass, field
from enum import IntEnum, IntFlag, auto
from pprint import pprint

from BaseClasses import Region
from rule_builder.rules import Has, HasAll, Rule


class CardAbilityFlags(IntFlag):
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

    Purify = PurifyFire | PurifyDiscard
    Elevate = ElevateFire | ElevateDiscard
    Godspeed = GodspeedFire | GodspeedDiscard
    Stomp = StompFire | StompDiscard
    Fireball = FireballFire | FireballDiscard
    Dominion = DominionFire | DominionDiscard

    AllFire = PurifyFire | ElevateFire | GodspeedFire | StompFire | FireballFire | DominionFire | Katana
    AllDiscard = PurifyDiscard | ElevateDiscard | GodspeedDiscard | StompDiscard | FireballDiscard | DominionDiscard | BookOfLife

    Everything = AllFire | AllDiscard
    EverythingXBoof = Everything & ~BookOfLife

    @staticmethod
    def solo_to_string(solo: "CardAbilityFlags", prefix="") -> str:
        if solo not in CARDABILITY_STR:
            return "Unknown Card"
        return prefix + CARDABILITY_STR[solo]

    @staticmethod
    def string_to_solo(string: str) -> "CardAbilityFlags":
        if string.endswith("(Fire)"):
            return CardAbilityFlags[string.split(maxsplit=1)[0] + "Fire"]
        if string.endswith("(Discard)"):
            return CardAbilityFlags[string.split(maxsplit=1)[0] + "Discard"]
        if string == "Katana":
            return CardAbilityFlags.Katana
        if string == "Book of Life":
            return CardAbilityFlags.BookOfLife
        return CardAbilityFlags.FistOnly

    def to_list(self) -> list[str]:
        return [
            CardAbilityFlags.solo_to_string(x) for x in self
        ]

    def to_set(self) -> set[str]:
        return {
            CardAbilityFlags.solo_to_string(x) for x in self
        }

    @staticmethod
    def from_list(lst: list[str]) -> "CardAbilityFlags":
        ret = CardAbilityFlags.FistOnly
        for x in lst:
            ret |= CardAbilityFlags.string_to_solo(x)
        return ret

    # a copy of c#'s
    def has_(self, other: "CardAbilityFlags") -> bool:
        # __contains__ without the check
        return self._value_ & other._value_ == self._value_

    def or_(self, other: "CardAbilityFlags"):
        # __or__ without the check
        return CardAbilityFlags(self._value_ | other._value_)

    def to_rule(self) -> "Rule":
        # this is never hit bc it's checked for
        # if self.count == 0:
        #     return True_()
        if self.bit_count() == 1:
            return Has(CardAbilityFlags.solo_to_string(self))
        return HasAll(*self.to_list())

CAF = CardAbilityFlags

# fmt: off
CARDABILITY_STR = {
    CAF.FistOnly:          "Fists",
    CAF.Katana:            "Katana",
    CAF.PurifyFire:        "Purify (Fire)",
    CAF.PurifyDiscard:     "Purify (Discard)",
    CAF.ElevateFire:       "Elevate (Fire)",
    CAF.ElevateDiscard:    "Elevate (Discard)",
    CAF.GodspeedFire:      "Godspeed (Fire)",
    CAF.GodspeedDiscard:   "Godspeed (Discard)",
    CAF.StompFire:         "Stomp (Fire)",
    CAF.StompDiscard:      "Stomp (Discard)",
    CAF.FireballFire:      "Fireball (Fire)",
    CAF.FireballDiscard:   "Fireball (Discard)",
    CAF.DominionFire:      "Dominion (Fire)",
    CAF.DominionDiscard:   "Dominion (Discard)",
    CAF.BookOfLife:        "Book of Life"
}
# fmt: on

class Medal(IntEnum):
    Bronze = 0
    Silver = 1
    Gold = 2
    Ace = 3
    Dev = 4
    Gift = 5

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str) and value.title() in cls.__members__:
            return cls.__members__[value.title()]
        return super()._missing_(value)


@dataclass(slots=True)
class LevelInfo:
    id: str
    cards: CardAbilityFlags
    giftless: bool = field(default=False)
    sidequest: bool = field(default=False)
    alias: str = field(default="", kw_only=True)

    name: str = field(init=False, hash=False, default="")
    regions: dict[int, Region] = field(init=False, hash=False)

    def __post_init__(self):
        self.regions = {}
        self.cards |= CardAbilityFlags.Katana
        if self.sidequest:
            self.giftless = True

    def __repr__(self) -> str:
        return self.name + ": " + repr(self.cards)#', '.join(self.cards.to_list())


MEDALS = [x.name for x in Medal if x != Medal.Gift]

# fmt: off
LEVEL_INFO = {
"Movement":                 LevelInfo("TUT_MOVEMENT",
    CAF.FistOnly),
"Pummel":                   LevelInfo("TUT_SHOOTINGRANGE",
    CAF.Purify),
"Gunner":                   LevelInfo("SLUGGER",
    CAF.Purify),
"Cascade":                  LevelInfo("TUT_FROG",
    CAF.Elevate),
"Elevate":                  LevelInfo("TUT_JUMP",
    CAF.Elevate | CAF.Purify),
"Bounce":                   LevelInfo("GRID_TUT_BALLOON",
    CAF.Elevate),
"Purify":                   LevelInfo("TUT_BOMB2",
    CAF.Purify),
"Climb":                    LevelInfo("TUT_BOMBJUMP",
    CAF.Purify),
"Fasttrack":                LevelInfo("TUT_FASTTRACK",
    CAF.Purify | CAF.Elevate),
"Glass Port":               LevelInfo("GRID_PORT",
    CAF.Purify | CAF.Elevate),
"Take Flight":              LevelInfo("GRID_PAGODA",
    CAF.Purify | CAF.Elevate),
"Godspeed":                 LevelInfo("TUT_RIFLE",
    CAF.Godspeed),
"Dasher":                   LevelInfo("TUT_RIFLEJOCK",
    CAF.Elevate | CAF.Godspeed),
"Thrasher":                 LevelInfo("TUT_DASHENEMY",
    CAF.Elevate | CAF.Godspeed),
"Outstretched":             LevelInfo("GRID_JUMPDASH",
    CAF.Elevate | CAF.Godspeed),
"Smackdown":                LevelInfo("GRID_SMACKDOWN",
    CAF.Elevate | CAF.Godspeed),
"Catwalk":                  LevelInfo("GRID_MEATY_BALLOONS",
    CAF.Godspeed),
"Fastlane":                 LevelInfo("GRID_FAST_BALLOON",
    CAF.Godspeed),
"Distinguish":              LevelInfo("GRID_DRAGON2",
    CAF.Elevate | CAF.Godspeed),
"Dancer":                   LevelInfo("GRID_DASHDANCE",
    CAF.Elevate | CAF.Godspeed),
"Guardian":                 LevelInfo("TUT_GUARDIAN",
    CAF.Purify | CAF.Elevate | CAF.Godspeed),
"Stomp":                    LevelInfo("TUT_UZI",
    CAF.Elevate | CAF.Stomp),
"Jumper":                   LevelInfo("TUT_JUMPER",
    CAF.Elevate | CAF.Stomp),
"Dash Tower":               LevelInfo("TUT_BOMB",
    CAF.Elevate | CAF.Stomp | CAF.Godspeed),
"Descent":                  LevelInfo("GRID_DESCEND",
    CAF.Godspeed | CAF.Stomp),
"Driller":                  LevelInfo("GRID_STAMPEROUT",
    CAF.Godspeed | CAF.Stomp),
"Canals":                   LevelInfo("GRID_CRUISE",
    CAF.Purify | CAF.Elevate | CAF.Stomp),
"Sprint":                   LevelInfo("GRID_SPRINT",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Mountain":                 LevelInfo("GRID_MOUNTAIN",
    CAF.Purify | CAF.Stomp),
"Superkinetic":             LevelInfo("GRID_SUPERKINETIC",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Arrival":                  LevelInfo("GRID_ARRIVAL",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Forgotten City":           LevelInfo("FLOATING",
    CAF.Godspeed | CAF.Stomp),
"The Clocktower":           LevelInfo("GRID_BOSS_YELLOW",
    CAF.Purify | CAF.Elevate | CAF.Godspeed | CAF.Stomp,
    giftless=True),
"Fireball":                 LevelInfo("GRID_HOPHOP",
    CAF.Fireball),
"Ringer":                   LevelInfo("GRID_RINGER_TUTORIAL",
    CAF.Fireball | CAF.Elevate),
"Cleaner":                  LevelInfo("GRID_RINGER_EXPLORATION",
    CAF.Fireball | CAF.Godspeed),
"Warehouse":                LevelInfo("GRID_HOPSCOTCH",
    CAF.Fireball | CAF.Elevate),
"Boom":                     LevelInfo("GRID_BOOM",
    CAF.Fireball | CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Streets":                  LevelInfo("GRID_SNAKE_IN_MY_BOOT",
    CAF.Fireball | CAF.Godspeed),
"Steps":                    LevelInfo("GRID_FLOCK",
    CAF.Fireball | CAF.Godspeed),
"Demolition":               LevelInfo("GRID_BOMBS_AHOY",
    CAF.Fireball | CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Arcs":                     LevelInfo("GRID_ARCS",
    CAF.Elevate | CAF.Stomp),
"Apartment":                LevelInfo("GRID_APARTMENT",
    CAF.EverythingXBoof & ~(CAF.Dominion)),
"Hanging Gardens":          LevelInfo("TUT_TRIPWIRE",
    CAF.Purify | CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Tangled":                  LevelInfo("GRID_TANGLED",
    CAF.Purify | CAF.Elevate | CAF.Stomp | CAF.Fireball),
"Waterworks":               LevelInfo("GRID_HUNT",
    CAF.Elevate | CAF.Godspeed),
"Killswitch":               LevelInfo("GRID_CANNONS",
    CAF.Elevate | CAF.Godspeed),
"Falling":                  LevelInfo("GRID_FALLING",
    CAF.Stomp | CAF.Fireball),
"Shocker":                  LevelInfo("TUT_SHOCKER2",
    CAF.Elevate | CAF.Godspeed | CAF.Fireball),
"Bouquet":                  LevelInfo("TUT_SHOCKER",
    CAF.EverythingXBoof & ~(CAF.Dominion)),
"Prepare":                  LevelInfo("GRID_PREPARE",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Fireball),
"Triptrack":                LevelInfo("GRID_TRIPMAZE",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Fireball),
"Race":                     LevelInfo("GRID_RACE",
    CAF.Godspeed),
"Bubble":                   LevelInfo("TUT_FORCEFIELD2",
    CAF.Purify | CAF.Elevate | CAF.Stomp),
"Shield":                   LevelInfo("GRID_SHIELD",
    CAF.EverythingXBoof & ~(CAF.Dominion)),
"Overlook":                 LevelInfo("SA L VAGE2",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Pop":                      LevelInfo("GRID_VERTICAL",
    CAF.Purify | CAF.Elevate | CAF.Godspeed | CAF.Fireball),
"Minefield":                LevelInfo("GRID_MINEFIELD",
    CAF.Elevate | CAF.Godspeed),
"Mimic":                    LevelInfo("TUT_MIMIC",
    CAF.Purify | CAF.Elevate | CAF.Godspeed | CAF.Fireball),
"Trigger":                  LevelInfo("GRID_MIMICPOP",
    CAF.Purify | CAF.Elevate | CAF.Fireball),
"Greenhouse":               LevelInfo("GRID_SWARM",
    CAF.Elevate | CAF.Stomp | CAF.Fireball),
"Sweep":                    LevelInfo("GRID_SWITCH",
    CAF.Purify | CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Fuse":                     LevelInfo("GRID_TRAPS2",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Fireball),
"Heaven's Edge":            LevelInfo("TUT_ROCKETJUMP",
    CAF.Dominion),
"Zipline":                  LevelInfo("TUT_ZIPLINE",
    CAF.Dominion | CAF.Stomp),
"Swing":                    LevelInfo("GRID_CLIMBANG",
    CAF.Dominion | CAF.Godspeed),
"Chute":                    LevelInfo("GRID_ROCKETUZI",
    CAF.Dominion | CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Crash":                    LevelInfo("GRID_CRASHLAND",
    CAF.Dominion | CAF.Stomp | CAF.Fireball),
"Ascent":                   LevelInfo("GRID_ESCALATE",
    CAF.Dominion),
"Straightaway":             LevelInfo("GRID_SPIDERCLAUS",
    CAF.Dominion | CAF.Godspeed | CAF.Stomp),
"Firecracker":              LevelInfo("GRID_FIRECRACKER_2",
    CAF.Dominion | CAF.Elevate | CAF.Godspeed),
"Streak":                   LevelInfo("GRID_SPIDERMAN",
    CAF.Dominion | CAF.Godspeed | CAF.Stomp),
"Mirror":                   LevelInfo("GRID_DESTRUCTION",
    CAF.EverythingXBoof & ~(CAF.Purify)),
"Escalation":               LevelInfo("GRID_HEAT",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Fireball),
"Bolt":                     LevelInfo("GRID_BOLT",
    CAF.Stomp | CAF.Fireball | CAF.Dominion),
"Godstreak":                LevelInfo("GRID_PON",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Dominion),
"Plunge":                   LevelInfo("GRID_CHARGE",
    CAF.EverythingXBoof & ~(CAF.Dominion)),
"Mayhem":                   LevelInfo("GRID_MIMICFINALE",
    CAF.Purify | CAF.Godspeed | CAF.Stomp | CAF.Fireball),
"Barrage":                  LevelInfo("GRID_BARRAGE",
    CAF.Purify | CAF.Elevate | CAF.Godspeed | CAF.Stomp),
"Estate":                   LevelInfo("GRID_1GUN",
    CAF.EverythingXBoof & ~(CAF.Dominion)),
"Trapwire":                 LevelInfo("GRID_HECK",
    CAF.Elevate | CAF.Stomp | CAF.Fireball),
"Ricochet":                 LevelInfo("GRID_ANTFARM",
    CAF.EverythingXBoof & ~(CAF.Dominion)),
"Fortress":                 LevelInfo("GRID_FORTRESS",
    CAF.EverythingXBoof),
"Holy Ground":              LevelInfo("GRID_GODTEMPLE_ENTRY",
    CAF.EverythingXBoof & ~(CAF.Purify)),
"The Third Temple":         LevelInfo("GRID_BOSS_GODSDEATHTEMPLE",
    CAF.Elevate | CAF.Stomp | CAF.Fireball | CAF.Dominion,
    giftless=True, alias="The Third Temple (Level)"),
"Spree":                    LevelInfo("GRID_EXTERMINATOR",
    CAF.BookOfLife | CAF.Elevate | CAF.Godspeed),
"Breakthrough":             LevelInfo("GRID_FEVER",
    CAF.Everything | ~CAF.Dominion),
"Glide":                    LevelInfo("GRID_SKIPSLIDE",
    CAF.Everything),
"Closer":                   LevelInfo("GRID_CLOSER",
    CAF.BookOfLife | CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Dominion),
"Hike":                     LevelInfo("GRID_HIKE",
    CAF.Everything & ~CAF.Purify),
"Switch":                   LevelInfo("GRID_SKIP",
    CAF.Everything & ~CAF.Purify),
"Access":                   LevelInfo("GRID_CEILING",
    CAF.Everything & ~CAF.Purify),
"Congregation":             LevelInfo("GRID_BOOP",
    CAF.BookOfLife | CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Fireball),
"Sequence":                 LevelInfo("GRID_TRIPRAP",
    CAF.BookOfLife | CAF.Elevate),
"Marathon":                 LevelInfo("GRID_ZIPRAP",
    CAF.Everything),
"Sacrifice":                LevelInfo("TUT_ORIGIN",
    CAF.EverythingXBoof & ~(CAF.Dominion),
    giftless=True),
"Absolution":               LevelInfo("GRID_BOSS_RAPTURE",
    CAF.Everything & ~CAF.Purify,
    giftless=True),
"Elevate Traversal I":      LevelInfo("SIDEQUEST_OBSTACLE_PISTOL",
    CAF.Elevate, sidequest=True),
"Elevate Traversal II":     LevelInfo("SIDEQUEST_OBSTACLE_PISTOL_SHOOT",
    CAF.Elevate, sidequest=True),
"Purify Traversal":         LevelInfo("SIDEQUEST_OBSTACLE_MACHINEGUN",
    CAF.Purify, sidequest=True),
"Godspeed Traversal":       LevelInfo("SIDEQUEST_OBSTACLE_RIFLE_2",
    CAF.Godspeed, sidequest=True),
"Stomp Traversal":          LevelInfo("SIDEQUEST_OBSTACLE_UZI2",
    CAF.Stomp, sidequest=True),
"Fireball Traversal":       LevelInfo("SIDEQUEST_OBSTACLE_SHOTGUN",
    CAF.Fireball, sidequest=True),
"Dominion Traversal":       LevelInfo("SIDEQUEST_OBSTACLE_ROCKETLAUNCHER",
    CAF.Dominion, sidequest=True),
"Book of Life Traversal":   LevelInfo("SIDEQUEST_RAPTURE_QUEST",
    CAF.BookOfLife, sidequest=True),
"Doghouse":                 LevelInfo("SIDEQUEST_DODGER",
    CAF.Purify | CAF.Elevate, sidequest=True),
"Choker":                   LevelInfo("GRID_GLASSPATH",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp, sidequest=True),
"Chain":                    LevelInfo("GRID_GLASSPATH2",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp, sidequest=True),
"Hellevator":               LevelInfo("GRID_HELLVATOR",
    CAF.Godspeed | CAF.Stomp, sidequest=True),
"Razor":                    LevelInfo("GRID_GLASSPATH3",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Fireball, sidequest=True),
"All Seeing Eye":           LevelInfo("SIDEQUEST_ALL_SEEING_EYE",
    CAF.EverythingXBoof & ~CAF.Dominion, sidequest=True),
"Resident Saw I":           LevelInfo("SIDEQUEST_RESIDENTSAWB",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp | CAF.Fireball, sidequest=True),
"Resident Saw II":          LevelInfo("SIDEQUEST_RESIDENTSAW",
    CAF.Elevate | CAF.Godspeed | CAF.Stomp, sidequest=True),
"Sunset Flip Powerbomb":    LevelInfo("SIDEQUEST_SUNSET_FLIP_POWERBOMB",
    CAF.PurifyFire, sidequest=True),
"Balloon Mountain":         LevelInfo("GRID_BALLOONLAIR",
    CAF.FistOnly, sidequest=True),
"Climbing Gym":             LevelInfo("SIDEQUEST_BARREL_CLIMB",
    (CAF.Purify | CAF.Elevate | CAF.Stomp | CAF.Godspeed) & CAF.AllFire,
    sidequest=True),
"Fisherman Suplex":         LevelInfo("SIDEQUEST_FISHERMAN_SUPLEX",
    (CAF.Elevate | CAF.Godspeed) & CAF.AllFire,
    sidequest=True),
"STF":                      LevelInfo("SIDEQUEST_STF",
    (CAF.Purify | CAF.Godspeed) & CAF.AllFire,
    sidequest=True),
"Arena":                    LevelInfo("SIDEQUEST_ARENASIXNINE",
    (CAF.Elevate | CAF.Godspeed | CAF.Stomp) & CAF.AllFire,
    sidequest=True),
"Attitude Adjustment":      LevelInfo("SIDEQUEST_ATTITUDE_ADJUSTMENT",
    (CAF.Stomp | CAF.Fireball) & CAF.AllFire,
    sidequest=True),
"Rocket":                   LevelInfo("SIDEQUEST_ROCKETGODZ",
    CAF.DominionFire, sidequest=True),
}
# fmt: on

# code outside of a function!?? how scandalous...
_LEVELIMPORT = False
if not _LEVELIMPORT:
    _LEVELIMPORT = True
    for (name, level) in LEVEL_INFO.items():
        level.name = name
        # print(level)

@dataclass(slots=True)
class MissionInfo:
    level_names: tuple[str, ...] = field(repr=False)
    cards: CardAbilityFlags = field(init=False, default=CardAbilityFlags.FistOnly)
    sidequest: bool = field(default=False, kw_only=True)
    alias: str = field(default="", kw_only=True)

    name: str = field(init=False, hash=False, default="")
    levels: tuple[LevelInfo, ...] = field(init=False, hash=False)
    regions: dict[int, Region] = field(init=False, hash=False)

    def __post_init__(self):
        self.regions = {}
        self.levels = tuple([LEVEL_INFO[level] for level in self.level_names])
        for level in self.levels:
            self.cards |= level.cards

MISSION_INFO = {
    "Rebirth": MissionInfo(
        (
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
        )
    ),
    "Killer Inside": MissionInfo(
        (
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
        )
    ),
    "Only Shallow": MissionInfo(
        (
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
        )
    ),
    "The Old City": MissionInfo(("Arrival", "Forgotten City", "The Clocktower")),
    "The Burn That Cures": MissionInfo(
        (
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
        )
    ),
    "Covenant": MissionInfo(
        (
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
        )
    ),
    "Reckoning": MissionInfo(
        (
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
        )
    ),
    "Benediction": MissionInfo(
        (
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
        )
    ),
    "Apocrypha": MissionInfo(
        (
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
        )
    ),
    "The Third Temple": MissionInfo(("Holy Ground", "The Third Temple"), alias="The Third Temple (Mission)"),
    "Thousand Pound Butterfly": MissionInfo(
        (
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
        )
    ),
    "Hand of God": MissionInfo(("Sacrifice", "Absolution")),
    "Red Sidequests": MissionInfo(
        (
            "Elevate Traversal I",
            "Elevate Traversal II",
            "Purify Traversal",
            "Godspeed Traversal",
            "Stomp Traversal",
            "Fireball Traversal",
            "Dominion Traversal",
            "Book of Life Traversal",
        ), sidequest=True),
    "Violet Sidequests": MissionInfo(
        (
            "Doghouse",
            "Choker",
            "Chain",
            "Hellevator",
            "Razor",
            "All Seeing Eye",
            "Resident Saw I",
            "Resident Saw II",
        ), sidequest=True),
    "Yellow Sidequests": MissionInfo(
        (
            "Sunset Flip Powerbomb",
            "Balloon Mountain",
            "Climbing Gym",
            "Fisherman Suplex",
            "STF",
            "Arena",
            "Attitude Adjustment",
            "Rocket"
        ), sidequest=True),
}

# TWICE?!/!?!? oh DEARY ME.....
_MISSIONIMPORT = False
if not _MISSIONIMPORT:
    _MISSIONIMPORT = True
    for (name, level) in MISSION_INFO.items():
        level.name = name
