import dataclasses
import itertools
import json
import statistics
from collections import deque
from enum import IntEnum, IntFlag, auto
from functools import reduce
from math import floor
from operator import or_
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeAlias, final
from weakref import WeakValueDictionary

from BaseClasses import CollectionState, MultiWorld
from NetUtils import JSONMessagePart
from rule_builder.rules import False_, Has, HasAll, Rule, True_
from typing_extensions import override

from . import NeonWhiteOptions, data
from .locations import (
    neon_white_level_name_internal,
    neon_white_levels_giftless,
    neon_white_levels_normal,
    neon_white_levels_sidequests,
)
from .options import (
    ExecutionDifficulty,
    KnowledgeDifficulty,
    MissionUnlockMethod,
)
from .regions import neon_white_missions, neon_white_missions_sq

if TYPE_CHECKING:
    from . import NeonWhiteWorld

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

    @staticmethod
    def solo_to_string(solo: "LevelRequirements") -> str:
        if not solo.name:
            return "Unknown Card"

        if (solo.name.endswith("Fire")):
            return solo.name.removesuffix("Fire") + " - Fire"
        if (solo.name.endswith("Discard")):
            return solo.name.removesuffix("Discard") + " - Discard"
        if solo == LevelRequirements.Katana:
            return "Katana"
        if solo == LevelRequirements.BookOfLife:
            return "Book of Life"
        return "Fists" # fists?

    @staticmethod
    def string_to_solo(string: str) -> "LevelRequirements":
        if (string.endswith("- Fire")):
            return LevelRequirements[string.split(maxsplit=1)[0] + "Fire"]
        if (string.endswith("- Discard")):
            return LevelRequirements[string.split(maxsplit=1)[0] + "Discard"]
        if string == "Katana":
            return LevelRequirements.Katana
        if string == "Book of Life":
            return LevelRequirements.BookOfLife
        return LevelRequirements.FistOnly

    def to_list(self) -> list[str]:
        return [LevelRequirements.solo_to_string(x) for x in LevelRequirements if x in self]

    def to_set(self) -> set[str]:
        return {LevelRequirements.solo_to_string(x) for x in LevelRequirements if x in self}

    @staticmethod
    def from_list(lst: list[str]) -> "LevelRequirements":
        ret = LevelRequirements.FistOnly
        for x in lst:
            ret |= LevelRequirements.string_to_solo(x)
        return ret

    @staticmethod
    def from_state(state: CollectionState, player: int):
        player_i = state.prog_items[player]
        ret = LevelRequirements.FistOnly
        for (i, c) in player_i.items():
            if c:
                ret |= LevelRequirements.string_to_solo(i)
        return ret

    # a copy of c#'s
    def has_flags(self, other: "LevelRequirements") -> bool:
        return self & other == self

    def to_rule(self) -> "Rule":
        # this is never hit bc it's checked for
        # if self.count == 0:
        #     return True_()
        if self.bit_count() == 1:
            return Has(LevelRequirements.solo_to_string(self))
        return HasAll(*self.to_list())

RES_F: TypeAlias = tuple[tuple[tuple[str, ...], "RES_F"], ...] | None
RES_T: TypeAlias = deque[tuple[tuple[str, ...], "RES_F"]]

@dataclasses.dataclass()
class LevelReqRule(Rule["NeonWhiteWorld"], game="Neon White"):
    reqs: frozenset[LevelRequirements] = dataclasses.field(init=False)
    _built: RES_F | Rule | None = dataclasses.field(init=False)
    _resregistry: WeakValueDictionary = dataclasses.field(init=False)

    # https://stackoverflow.com/a/71563134
    _registry: ClassVar[WeakValueDictionary] = WeakValueDictionary()
    def __new__(cls, reqs: frozenset[LevelRequirements], *args, **kwargs) -> Self:
        if reqs in cls._registry:
            return cls._registry[reqs]
        i = super().__new__(cls)
        cls._registry[reqs] = i
        return i

    def __init__(self, reqs: frozenset[LevelRequirements]) -> None:
        if hasattr(self, "_rule"):
            return
        self.reqs = reqs
        self._built = None
        self._resregistry = WeakValueDictionary()

    @staticmethod
    # @lru_cache(maxsize=512) # enable when this ends up being more expensive
    def _make_rule(reqs: frozenset[LevelRequirements], ignore = LevelRequirements.FistOnly) -> RES_F:
        # print("CALLB", reqs, ignore)
        total = reduce(or_, reqs, LevelRequirements.FistOnly) & ~ignore
        consumed = set[LevelRequirements]()
        cats = {
            x: {r for r in reqs if x.has_flags(r)}
            for x in total
        }

        res: RES_T = deque()

        while True:
            s = sorted(cats.items(), key=lambda itm: len(itm[1]), reverse=True)

            catr = s[0][1].copy()
            if len(catr) <= 1:
                break

            cat = LevelRequirements.FistOnly

            for sCat, sCatr in s:
                if len(catr) > len(sCatr):
                    break
                if (sCatr != catr):
                    continue
                cat |= sCat

            res.appendleft((tuple(cat.to_list()), LevelReqRule._make_rule(frozenset(catr), ignore=ignore | cat)))

            for cat in total:
                cats[cat] -= catr
            consumed |= catr

        res.extendleft([(tuple(r.to_list()), None)
            for r in
            sorted(((x & ~ignore) for x in reqs if x not in consumed), key=lambda x: x.bit_count())])

        return tuple(res)

    @staticmethod
    def _merge_O(rule: Rule, req: LevelRequirements) -> Rule:
        return req.to_rule() | rule

    def _make_rule_O(self) -> "Rule":
        return reduce(LevelReqRule._merge_O, sorted(self.reqs, key=lambda x: x.bit_count(), reverse=True), False_())

    @override
    def _instantiate(self, world: "NeonWhiteWorld") -> Rule.Resolved:
        if world in self._resregistry:
            return self._resregistry[world]

        if not self.reqs:
            res = False_().resolve(world)
        elif not next(iter(self.reqs)):
            res = True_().resolve(world)
        else:
            if self._built is None:
                self._built = self._make_rule(self.reqs)

            res = self.Resolved(
                self.reqs,
                self._built,
                player=world.player)

        self._resregistry[world] = res
        return res

    class Resolved(Rule.Resolved):
        reqs: frozenset[LevelRequirements]
        built: RES_F

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            iterstack = [iter(self.built)]  # pyright: ignore[reportArgumentType, reportCallIssue]
            playeri = state.prog_items[self.player]

            while iterstack:
                it = iterstack[-1]
                for items, dig in it:
                    for item in items:
                        if not playeri[item]:
                            break
                    else:
                        if not dig:
                            return True
                        iterstack.append(iter(dig))
                        break
                else:
                    iterstack.pop()

            return False


        @override
        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            return [] # TODO this is easy it's just 5:43am

# This only represents a single difficulty
@final
class LevelRequirementSet:
    def __init__(self):
        # String is the level name, list is 0..5, in order: dev,ace,gold,silver,bronze,gift
        self.requirements = dict[str, list[LevelReqRule]]()

    # Note - Medal 0-4 is dev-bronze, 5 is gift
    # Cards are what is available at that point
    def can_complete_level(self, level: str, medal: Medal, cards: LevelRequirements) -> bool:
        medal_idx = int(medal) if medal == Medal.Gift else 4 - int(medal)

        for solution in self.requirements[level][medal_idx].reqs:
            # Bitwise check, e.g. 0001 & 1111 == 0001, success; 1001 & 0101 == 0001, failure
            # If Fist-Only is a solution, & will return 0 (because it's all zeroes) and thus will == 0, always success
            if solution & cards == solution:
                return True
        return False

    def make_rule(self, level: str, medal: Medal) -> LevelReqRule:
        medal_idx = int(medal) if medal == Medal.Gift else 4 - int(medal)

        return self.requirements[level][medal_idx]

    def get_necessary_items(self, level: str, medal: Medal) -> frozenset[LevelRequirements]:
        medal_idx = int(medal) if medal == Medal.Gift else 4 - int(medal)
        return self.requirements[level][medal_idx].reqs

NWJSON_DATA: Any = {}

def import_json_to_data(know_diff: KnowledgeDifficulty, exec_diff: ExecutionDifficulty) -> LevelRequirementSet:
    global NWJSON_DATA
    if not NWJSON_DATA:
        # See archipelago requirements sheet for formatting
        from importlib.resources import files
        file = files(data).joinpath("nw_cr.json").open()
        NWJSON_DATA = json.loads(file.read())
    new_requirements = LevelRequirementSet()
    for entry in NWJSON_DATA:
        solutions = [set[LevelRequirements]() for _ in range(6)]
        for solution in NWJSON_DATA[entry]:
            capped: int = solution["m"]
            if LevelRequirements.FistOnly in solutions[capped]:
                continue # don't even bother

            if solution["k"] > know_diff or solution["e"] > exec_diff:
                continue
            reqs = LevelRequirements(solution["r"])

            if solution["m"] == 5:
                if any(x.has_flags(reqs) for x in solutions[5]):
                    continue

                solutions[5].add(reqs)
            else:
                for i in range(capped, 5):
                    if any(x.has_flags(reqs) for x in solutions[i]):
                        continue

                    solutions[i].add(reqs)

        new_requirements.requirements[entry] = [LevelReqRule(frozenset(x)) for x in solutions]
    return new_requirements

# Actual functions related to rules start here
def level_rando(world: "NeonWhiteWorld") -> list[str]:
    if world.use_levels:
        return list(neon_white_level_name_internal.keys())

    level_queue = neon_white_levels_normal + neon_white_levels_giftless
    if world.options.sidequests:
        level_queue.extend(neon_white_levels_sidequests)
    level_queue.remove("Absolution") # This will always be placed at the end

    level_queue = [x for x in level_queue if x not in world.early_levels]

    # Solve weights for weighted shuffle
    level_reqs = [world.requirement.requirements[x] for x in level_queue]

    weights = [statistics.mean(
            statistics.mean(
                req.bit_count() + 1 for req in reqs.reqs
            ) for reqs in medal_reqs if reqs.reqs
        ) for medal_reqs in level_reqs]

    variance: float = world.options.level_gradient / 100

    # https://softwareengineering.stackexchange.com/a/344274
    def weighted_shuffle(items: list[str]):
        norm = [x / max(weights) for x in weights]
        v = [norm[i] + variance * (world.random.random() - norm[i]) for i in range(len(items))]
        order = sorted(range(len(items)), key=lambda i: v[i])

        return [items[i] for i in order]

    # Shuffle the rest, append, then put Absolution at the end
    level_queue = weighted_shuffle(level_queue)

    return world.early_levels + level_queue + ["Absolution"]

# Mission is 1-indexed
def get_mission_rank_required(world: "NeonWhiteWorld", mission: int) -> int:
    # Neon rank requirement is exponential
    #    Requiring a tiny number of neon ranks for the first missions but quickly increasing for the last few missions
    # To visualize it in Desmos, do: y = (v^x - 1) / (v - 1), where v == lenience_value here
    #    X represents mission while Y represents ranks
    #    To get exact values, replace x with x - 1, then
    #       divide it by mission count and multiply the equation by rank total (floor fractions)
    #    E.g. 11 missions, 343 total ranks:
    #    y = ((v^((x-1) / 11) - 1) / (v - 1)) * 343
    mission_fraction: float = mission / world.options.mission_count
    lenience_value = 10 # How sharp the curve is, higher = slower rank req but sharper spike near the end
    normal_value = (pow(lenience_value, mission_fraction) - 1) / (lenience_value - 1)
    return floor(world.ranks_required * normal_value)

def set_rules(multiworld: MultiWorld, world: "NeonWhiteWorld", options: NeonWhiteOptions):
    medals = [Medal(x) for x in options.medal_select]

    if not world.ordered_levels:
        world.ordered_levels = level_rando(world)

    if options.unlock_method == MissionUnlockMethod.option_levels:
        # Basegame missions
        mission_list = [x[0] for x in neon_white_missions]
        if options.sidequests:
            mission_list.extend(x[0] for x in neon_white_missions_sq)
    else:
        # 121 levels split amongst X missions, differing from the base game
        mission_list = [f"Mission {x + 1}" for x in range(options.mission_count)]

    mission_count = len(mission_list)

    levels_norm = len(world.ordered_levels) // mission_count
    offset = mission_count - (len(world.ordered_levels) % mission_count)

    # Place one relevant discard ability into the early items pool to give the player something to work with
    relevant_discards: set[str] = set()
    for level in world.ordered_levels:
        itercombo = itertools.chain(
            world.requirement.get_necessary_items(level, max(medals, default=Medal.Bronze)),
            world.requirement.get_necessary_items(level, Medal.Gift))
        for solution in itercombo:
            for card in solution:
                cardstr = LevelRequirements.solo_to_string(card)
                if cardstr and ("Discard" in cardstr or "Book of Life" in cardstr):
                    relevant_discards.add(cardstr)
    relevant_discards_list = list(relevant_discards)

    if world.use_levels:
        multiworld.random.shuffle(relevant_discards_list)

    multiworld.local_early_items[world.player][relevant_discards_list
        [world.random.randint(0, len(relevant_discards_list) - 1)]] = 1

    central_heaven = world.get_region("Central Heaven")
    # Connect central heaven to every mission
    level_total = 0
    for i in range(mission_count):
        mission_region = world.get_region(mission_list[i])
        entrance_name = f"Central Heaven to {mission_region.name}"
        entrance = central_heaven.connect(mission_region, entrance_name)
        if i != 0:
            match options.unlock_method:  # pyright: ignore[reportMatchNotExhaustive]
                case MissionUnlockMethod.option_missions:
                    world.set_rule(entrance, Has("Mission Unlock", i))
                case MissionUnlockMethod.option_ranks:
                    neonrank_count = get_mission_rank_required(world, i + 1)
                    world.set_rule(entrance, Has("Neon Rank", neonrank_count))

        if world.use_levels:
            level_count = (neon_white_missions + neon_white_missions_sq)[i][1]
        else:
            # Connect each mission to the levels they contain
            level_count = levels_norm
            if i >= offset:
                level_count += 1

        for _ in range(level_count):
            level_name = world.ordered_levels[level_total]
            level_total += 1

            _ = mission_region.connect(world.get_region("Level: " + level_name),
                f"{mission_region.name} to {level_name}",
                Has(level_name) if world.options.unlock_method == MissionUnlockMethod.option_levels else None)
            if level_name in neon_white_levels_normal or level_name in neon_white_levels_giftless:
                for medal in medals:
                    world.set_rule(world.get_location(f"{level_name} {medal.name} Completion"),
                        world.requirement.make_rule(level_name, Medal(medal)))

                if level_name not in neon_white_levels_giftless and world.options.gifts:
                    world.set_rule(world.get_location(level_name + " Gift"),
                        world.requirement.make_rule(level_name, Medal.Gift))

            else:
                world.set_rule(world.get_location(level_name + " Completion"),
                    world.requirement.make_rule(level_name, max(medals, default=Medal.Bronze)))
