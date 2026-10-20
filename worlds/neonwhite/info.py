from dataclasses import dataclass, field
from enum import IntEnum, IntFlag, auto

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

    @staticmethod
    def solo_to_string(solo: "CardAbilityFlags") -> str:
        if not solo.name:
            return "Unknown Card"

        if solo.name.endswith("Fire"):
            return solo.name.removesuffix("Fire") + " (Fire)"
        if solo.name.endswith("Discard"):
            return solo.name.removesuffix("Discard") + " (Discard)"
        if solo == CardAbilityFlags.Katana:
            return "Katana"
        if solo == CardAbilityFlags.BookOfLife:
            return "Book of Life"
        return "Fists"  # fists?

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
            CardAbilityFlags.solo_to_string(x) for x in CardAbilityFlags if x in self
        ]

    def to_set(self) -> set[str]:
        return {
            CardAbilityFlags.solo_to_string(x) for x in CardAbilityFlags if x in self
        }

    @staticmethod
    def from_list(lst: list[str]) -> "CardAbilityFlags":
        ret = CardAbilityFlags.FistOnly
        for x in lst:
            ret |= CardAbilityFlags.string_to_solo(x)
        return ret

    # a copy of c#'s
    def has_flags(self, other: "CardAbilityFlags") -> bool:
        return self & other == self

    def to_rule(self) -> "Rule":
        # this is never hit bc it's checked for
        # if self.count == 0:
        #     return True_()
        if self.bit_count() == 1:
            return Has(CardAbilityFlags.solo_to_string(self))
        return HasAll(*self.to_list())


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


MEDALS = [x.name for x in Medal if x != Medal.Gift]

# fmt: off
LEVEL_INFO = {
"Movement":                 LevelInfo("TUT_MOVEMENT",
    CardAbilityFlags.FistOnly),
"Pummel":                   LevelInfo("TUT_SHOOTINGRANGE",
    CardAbilityFlags.Purify),
"Gunner":                   LevelInfo("SLUGGER",
    CardAbilityFlags.Purify),
"Cascade":                  LevelInfo("TUT_FROG",
    CardAbilityFlags.Elevate),
"Elevate":                  LevelInfo("TUT_JUMP",
    CardAbilityFlags.Elevate),
"Bounce":                   LevelInfo("GRID_TUT_BALLOON",
    CardAbilityFlags.Elevate),
"Purify":                   LevelInfo("TUT_BOMB2",
    CardAbilityFlags.Purify),
"Climb":                    LevelInfo("TUT_BOMBJUMP",
    CardAbilityFlags.Purify),
"Fasttrack":                LevelInfo("TUT_FASTTRACK",
    CardAbilityFlags.Purify | CardAbilityFlags.Elevate),
"Glass Port":               LevelInfo("GRID_PORT",
    CardAbilityFlags.Purify | CardAbilityFlags.Elevate),
"Take Flight":              LevelInfo("GRID_PAGODA",
    CardAbilityFlags.Purify | CardAbilityFlags.Elevate),
"Godspeed":                 LevelInfo("TUT_RIFLE",
    CardAbilityFlags.Godspeed),
"Dasher":                   LevelInfo("TUT_RIFLEJOCK",
    CardAbilityFlags.Elevate | CardAbilityFlags.Godspeed),
"Thrasher":                 LevelInfo("TUT_DASHENEMY",
    CardAbilityFlags.Elevate | CardAbilityFlags.Godspeed),
"Outstretched":             LevelInfo("GRID_JUMPDASH",
    CardAbilityFlags.Elevate | CardAbilityFlags.Godspeed),
"Smackdown":                LevelInfo("GRID_SMACKDOWN",
    CardAbilityFlags.Elevate | CardAbilityFlags.Godspeed),
"Catwalk":                  LevelInfo("GRID_MEATY_BALLOONS",
    CardAbilityFlags.Godspeed),
"Fastlane":                 LevelInfo("GRID_FAST_BALLOON",
    CardAbilityFlags.Godspeed),
"Distinguish":              LevelInfo("GRID_DRAGON2",
    CardAbilityFlags.Elevate | CardAbilityFlags.Godspeed),
"Dancer":                   LevelInfo("GRID_DASHDANCE",
    CardAbilityFlags.Elevate | CardAbilityFlags.Godspeed),
"Guardian":                 LevelInfo("TUT_GUARDIAN",
    CardAbilityFlags.Purify | CardAbilityFlags.Elevate | CardAbilityFlags.Godspeed),
"Stomp":                    LevelInfo("TUT_UZI",
    CardAbilityFlags.Elevate | CardAbilityFlags.Stomp),
"Jumper":                   LevelInfo("TUT_JUMPER",
    CardAbilityFlags.Elevate | CardAbilityFlags.Stomp),
"Dash Tower":               LevelInfo("TUT_BOMB",
    CardAbilityFlags.Elevate | CardAbilityFlags.Stomp | CardAbilityFlags.Godspeed),
"Descent":                  LevelInfo("GRID_DESCEND",
    CardAbilityFlags.FistOnly),
"Driller":                  LevelInfo("GRID_STAMPEROUT",
    CardAbilityFlags.FistOnly),
"Canals":                   LevelInfo("GRID_CRUISE",
    CardAbilityFlags.FistOnly),
"Sprint":                   LevelInfo("GRID_SPRINT",
    CardAbilityFlags.FistOnly),
"Mountain":                 LevelInfo("GRID_MOUNTAIN",
    CardAbilityFlags.FistOnly),
"Superkinetic":             LevelInfo("GRID_SUPERKINETIC",
    CardAbilityFlags.FistOnly),
"Arrival":                  LevelInfo("GRID_ARRIVAL",
    CardAbilityFlags.FistOnly),
"Forgotten City":           LevelInfo("FLOATING",
    CardAbilityFlags.FistOnly),
"The Clocktower":           LevelInfo("GRID_BOSS_YELLOW",
    CardAbilityFlags.FistOnly, giftless=True),
"Fireball":                 LevelInfo("GRID_HOPHOP",
    CardAbilityFlags.FistOnly),
"Ringer":                   LevelInfo("GRID_RINGER_TUTORIAL",
    CardAbilityFlags.FistOnly),
"Cleaner":                  LevelInfo("GRID_RINGER_EXPLORATION",
    CardAbilityFlags.FistOnly),
"Warehouse":                LevelInfo("GRID_HOPSCOTCH",
    CardAbilityFlags.FistOnly),
"Boom":                     LevelInfo("GRID_BOOM",
    CardAbilityFlags.FistOnly),
"Streets":                  LevelInfo("GRID_SNAKE_IN_MY_BOOT",
    CardAbilityFlags.FistOnly),
"Steps":                    LevelInfo("GRID_FLOCK",
    CardAbilityFlags.FistOnly),
"Demolition":               LevelInfo("GRID_BOMBS_AHOY",
    CardAbilityFlags.FistOnly),
"Arcs":                     LevelInfo("GRID_ARCS",
    CardAbilityFlags.FistOnly),
"Apartment":                LevelInfo("GRID_APARTMENT",
    CardAbilityFlags.FistOnly),
"Hanging Gardens":          LevelInfo("TUT_TRIPWIRE",
    CardAbilityFlags.FistOnly),
"Tangled":                  LevelInfo("GRID_TANGLED",
    CardAbilityFlags.FistOnly),
"Waterworks":               LevelInfo("GRID_HUNT",
    CardAbilityFlags.FistOnly),
"Killswitch":               LevelInfo("GRID_CANNONS",
    CardAbilityFlags.FistOnly),
"Falling":                  LevelInfo("GRID_FALLING",
    CardAbilityFlags.FistOnly),
"Shocker":                  LevelInfo("TUT_SHOCKER2",
    CardAbilityFlags.FistOnly),
"Bouquet":                  LevelInfo("TUT_SHOCKER",
    CardAbilityFlags.FistOnly),
"Prepare":                  LevelInfo("GRID_PREPARE",
    CardAbilityFlags.FistOnly),
"Triptrack":                LevelInfo("GRID_TRIPMAZE",
    CardAbilityFlags.FistOnly),
"Race":                     LevelInfo("GRID_RACE",
    CardAbilityFlags.FistOnly),
"Bubble":                   LevelInfo("TUT_FORCEFIELD2",
    CardAbilityFlags.FistOnly),
"Shield":                   LevelInfo("GRID_SHIELD",
    CardAbilityFlags.FistOnly),
"Overlook":                 LevelInfo("SA L VAGE2",
    CardAbilityFlags.FistOnly),
"Pop":                      LevelInfo("GRID_VERTICAL",
    CardAbilityFlags.FistOnly),
"Minefield":                LevelInfo("GRID_MINEFIELD",
    CardAbilityFlags.FistOnly),
"Mimic":                    LevelInfo("TUT_MIMIC",
    CardAbilityFlags.FistOnly),
"Trigger":                  LevelInfo("GRID_MIMICPOP",
    CardAbilityFlags.FistOnly),
"Greenhouse":               LevelInfo("GRID_SWARM",
    CardAbilityFlags.FistOnly),
"Sweep":                    LevelInfo("GRID_SWITCH",
    CardAbilityFlags.FistOnly),
"Fuse":                     LevelInfo("GRID_TRAPS2",
    CardAbilityFlags.FistOnly),
"Heaven's Edge":            LevelInfo("TUT_ROCKETJUMP",
    CardAbilityFlags.FistOnly),
"Zipline":                  LevelInfo("TUT_ZIPLINE",
    CardAbilityFlags.FistOnly),
"Swing":                    LevelInfo("GRID_CLIMBANG",
    CardAbilityFlags.FistOnly),
"Chute":                    LevelInfo("GRID_ROCKETUZI",
    CardAbilityFlags.FistOnly),
"Crash":                    LevelInfo("GRID_CRASHLAND",
    CardAbilityFlags.FistOnly),
"Ascent":                   LevelInfo("GRID_ESCALATE",
    CardAbilityFlags.FistOnly),
"Straightaway":             LevelInfo("GRID_SPIDERCLAUS",
    CardAbilityFlags.FistOnly),
"Firecracker":              LevelInfo("GRID_FIRECRACKER_2",
    CardAbilityFlags.FistOnly),
"Streak":                   LevelInfo("GRID_SPIDERMAN",
    CardAbilityFlags.FistOnly),
"Mirror":                   LevelInfo("GRID_DESTRUCTION",
    CardAbilityFlags.FistOnly),
"Escalation":               LevelInfo("GRID_HEAT",
    CardAbilityFlags.FistOnly),
"Bolt":                     LevelInfo("GRID_BOLT",
    CardAbilityFlags.FistOnly),
"Godstreak":                LevelInfo("GRID_PON",
    CardAbilityFlags.FistOnly),
"Plunge":                   LevelInfo("GRID_CHARGE",
    CardAbilityFlags.FistOnly),
"Mayhem":                   LevelInfo("GRID_MIMICFINALE",
    CardAbilityFlags.FistOnly),
"Barrage":                  LevelInfo("GRID_BARRAGE",
    CardAbilityFlags.FistOnly),
"Estate":                   LevelInfo("GRID_1GUN",
    CardAbilityFlags.FistOnly),
"Trapwire":                 LevelInfo("GRID_HECK",
    CardAbilityFlags.FistOnly),
"Ricochet":                 LevelInfo("GRID_ANTFARM",
    CardAbilityFlags.FistOnly),
"Fortress":                 LevelInfo("GRID_FORTRESS",
    CardAbilityFlags.FistOnly),
"Holy Ground":              LevelInfo("GRID_GODTEMPLE_ENTRY",
    CardAbilityFlags.FistOnly),
"The Third Temple":         LevelInfo("GRID_BOSS_GODSDEATHTEMPLE",
    CardAbilityFlags.FistOnly, giftless=True, alias="The Third Temple (Level)"),
"Spree":                    LevelInfo("GRID_EXTERMINATOR",
    CardAbilityFlags.BookOfLife),
"Breakthrough":             LevelInfo("GRID_FEVER",
    CardAbilityFlags.BookOfLife),
"Glide":                    LevelInfo("GRID_SKIPSLIDE",
    CardAbilityFlags.BookOfLife),
"Closer":                   LevelInfo("GRID_CLOSER",
    CardAbilityFlags.BookOfLife),
"Hike":                     LevelInfo("GRID_HIKE",
    CardAbilityFlags.BookOfLife),
"Switch":                   LevelInfo("GRID_SKIP",
    CardAbilityFlags.BookOfLife),
"Access":                   LevelInfo("GRID_CEILING",
    CardAbilityFlags.BookOfLife),
"Congregation":             LevelInfo("GRID_BOOP",
    CardAbilityFlags.BookOfLife),
"Sequence":                 LevelInfo("GRID_TRIPRAP",
    CardAbilityFlags.BookOfLife),
"Marathon":                 LevelInfo("GRID_ZIPRAP",
    CardAbilityFlags.BookOfLife),
"Sacrifice":                LevelInfo("TUT_ORIGIN",
    CardAbilityFlags.FistOnly, giftless=True),
"Absolution":               LevelInfo("GRID_BOSS_RAPTURE",
    CardAbilityFlags.BookOfLife, giftless=True),
"Elevate Traversal I":      LevelInfo("SIDEQUEST_OBSTACLE_PISTOL",
    CardAbilityFlags.Elevate, sidequest=True),
"Elevate Traversal II":     LevelInfo("SIDEQUEST_OBSTACLE_PISTOL_SHOOT",
    CardAbilityFlags.Elevate, sidequest=True),
"Purify Traversal":         LevelInfo("SIDEQUEST_OBSTACLE_MACHINEGUN",
    CardAbilityFlags.Purify, sidequest=True),
"Godspeed Traversal":       LevelInfo("SIDEQUEST_OBSTACLE_RIFLE_2",
    CardAbilityFlags.Godspeed, sidequest=True),
"Stomp Traversal":          LevelInfo("SIDEQUEST_OBSTACLE_UZI2",
    CardAbilityFlags.Stomp, sidequest=True),
"Fireball Traversal":       LevelInfo("SIDEQUEST_OBSTACLE_SHOTGUN",
    CardAbilityFlags.Fireball, sidequest=True),
"Dominion Traversal":       LevelInfo("SIDEQUEST_OBSTACLE_ROCKETLAUNCHER",
    CardAbilityFlags.Dominion, sidequest=True),
"Book of Life Traversal":   LevelInfo("SIDEQUEST_RAPTURE_QUEST",
    CardAbilityFlags.BookOfLife, sidequest=True),
"Doghouse":                 LevelInfo("SIDEQUEST_DODGER",
    CardAbilityFlags.FistOnly, sidequest=True),
"Choker":                   LevelInfo("GRID_GLASSPATH",
    CardAbilityFlags.FistOnly, sidequest=True),
"Chain":                    LevelInfo("GRID_GLASSPATH2",
    CardAbilityFlags.FistOnly, sidequest=True),
"Hellevator":               LevelInfo("GRID_HELLVATOR",
    CardAbilityFlags.FistOnly, sidequest=True),
"Razor":                    LevelInfo("GRID_GLASSPATH3",
    CardAbilityFlags.FistOnly, sidequest=True),
"All Seeing Eye":           LevelInfo("SIDEQUEST_ALL_SEEING_EYE",
    CardAbilityFlags.FistOnly, sidequest=True),
"Resident Saw I":           LevelInfo("SIDEQUEST_RESIDENTSAWB",
    CardAbilityFlags.FistOnly, sidequest=True),
"Resident Saw II":          LevelInfo("SIDEQUEST_RESIDENTSAW",
    CardAbilityFlags.FistOnly, sidequest=True),
"Sunset Flip Powerbomb":    LevelInfo("SIDEQUEST_SUNSET_FLIP_POWERBOMB",
    CardAbilityFlags.FistOnly, sidequest=True),
"Balloon Mountain":         LevelInfo("GRID_BALLOONLAIR",
    CardAbilityFlags.FistOnly, sidequest=True),
"Climbing Gym":             LevelInfo("SIDEQUEST_BARREL_CLIMB",
    CardAbilityFlags.FistOnly, sidequest=True),
"Fisherman Suplex":         LevelInfo("SIDEQUEST_FISHERMAN_SUPLEX",
    CardAbilityFlags.FistOnly, sidequest=True),
"STF":                      LevelInfo("SIDEQUEST_STF",
    CardAbilityFlags.FistOnly, sidequest=True),
"Arena":                    LevelInfo("SIDEQUEST_ARENASIXNINE",
    CardAbilityFlags.FistOnly, sidequest=True),
"Attitude Adjustment":      LevelInfo("SIDEQUEST_ATTITUDE_ADJUSTMENT",
    CardAbilityFlags.FistOnly, sidequest=True),
"Rocket":                   LevelInfo("SIDEQUEST_ROCKETGODZ",
    CardAbilityFlags.FistOnly, sidequest=True),
}
# fmt: on

# code outside of a function!?? how scandalous...
_LEVELIMPORT = False
if not _LEVELIMPORT:
    _LEVELIMPORT = True
    for (name, level) in LEVEL_INFO.items():
        level.name = name

@dataclass(slots=True)
class MissionInfo:
    level_names: tuple[str, ...]
    cards: CardAbilityFlags = field(init=False, default=CardAbilityFlags.FistOnly)
    sidequest: bool = field(default=False, kw_only=True)
    alias: str = field(default="", kw_only=True)

    name: str = field(init=False, hash=False, default="")
    levels: tuple[LevelInfo, ...] = field(init=False, hash=False, repr=False)
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
