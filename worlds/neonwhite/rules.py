import dataclasses
import itertools
import json
import statistics
from collections import deque
from collections.abc import Callable
from functools import partial, reduce
from math import floor
from operator import or_
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeAlias, final
from weakref import WeakValueDictionary

from BaseClasses import CollectionState, Location, MultiWorld
from NetUtils import JSONMessagePart
from rule_builder.rules import False_, Has, Rule, True_
from typing_extensions import override

from . import NeonWhiteOptions, data
from .info import LEVEL_INFO, CardAbilityFlags, Medal
from .options import (
    ExecutionDifficulty,
    KnowledgeDifficulty,
    MissionUnlockMethod,
)

if TYPE_CHECKING:
    from . import NeonWhiteWorld

RES_F: TypeAlias = tuple[tuple[tuple[str, ...], "RES_F"], ...] | None
RES_T: TypeAlias = deque[tuple[tuple[str, ...], "RES_F"]]

@dataclasses.dataclass()
class LevelReqRule(Rule["NeonWhiteWorld"], game="Neon White"):
    reqs: frozenset[CardAbilityFlags] = dataclasses.field(init=False)
    _built: RES_F | Rule | None = dataclasses.field(init=False)
    _resregistry: WeakValueDictionary = dataclasses.field(init=False)

    # https://stackoverflow.com/a/71563134
    _registry: ClassVar[WeakValueDictionary] = WeakValueDictionary()
    def __new__(cls, reqs: frozenset[CardAbilityFlags], *args, **kwargs) -> Self:
        if reqs in cls._registry:
            return cls._registry[reqs]
        i = super().__new__(cls)
        cls._registry[reqs] = i
        return i

    def __init__(self, reqs: frozenset[CardAbilityFlags]) -> None:
        if hasattr(self, "_rule"):
            return
        self.reqs = reqs
        self._built = None
        self._resregistry = WeakValueDictionary()

    @staticmethod
    # @lru_cache(maxsize=512) # enable when this ends up being more expensive
    def _make_rule(reqs: frozenset[CardAbilityFlags], ignore = CardAbilityFlags.FistOnly) -> RES_F:
        # print("CALLB", reqs, ignore)
        total = reduce(or_, reqs, CardAbilityFlags.FistOnly) & ~ignore
        consumed = set[CardAbilityFlags]()
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

            cat = CardAbilityFlags.FistOnly

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
    def _merge_O(rule: Rule, req: CardAbilityFlags) -> Rule:
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
        reqs: frozenset[CardAbilityFlags]
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
    def can_complete_level(self, level: str, medal: Medal, cards: CardAbilityFlags) -> bool:
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

    def get_necessary_items(self, level: str, medal: Medal) -> frozenset[CardAbilityFlags]:
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
        solutions = [set[CardAbilityFlags]() for _ in range(6)]
        for solution in NWJSON_DATA[entry]:
            capped: int = solution["m"]
            if CardAbilityFlags.FistOnly in solutions[capped]:
                continue # don't even bother

            if solution["k"] > know_diff or solution["e"] > exec_diff:
                continue
            reqs = CardAbilityFlags(solution["r"])

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
    level_queue = [x.name for x in LEVEL_INFO.values() if not x.sidequest or world.options.sidequests]

    if world.use_levels:
        return level_queue

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

def _set_rule(world: "NeonWhiteWorld", medal: Medal, level: str, location: Location):
    world.set_rule(location, world.requirement.make_rule(level, medal))

def set_rules(multiworld: MultiWorld, world: "NeonWhiteWorld", options: NeonWhiteOptions):
    medals = [Medal(x) for x in options.medal_select]
    maxmedal = max(medals, default=Medal.Bronze)

    # Place one relevant discard ability into the early items pool to give the player something to work with
    relevant_discards: set[str] = set()
    for level in world.ordered_levels:
        itercombo = itertools.chain(
            world.requirement.get_necessary_items(level, maxmedal),
            world.requirement.get_necessary_items(level, Medal.Gift))
        for solution in itercombo:
            for card in solution:
                cardstr = CardAbilityFlags.solo_to_string(card)
                if cardstr and ("Discard" in cardstr or "Book of Life" in cardstr):
                    relevant_discards.add(cardstr)
    relevant_discards_list = list(relevant_discards)

    if world.use_levels:
        multiworld.random.shuffle(relevant_discards_list)

    multiworld.local_early_items[world.player][relevant_discards_list
        [world.random.randint(0, len(relevant_discards_list) - 1)]] = 1

    # Connect central heaven to every mission

    for i, mission in enumerate(world.missions):
        entrance = mission.regions[world.player].entrances[0]

        if i != 0:
            match options.unlock_method:  # pyright: ignore[reportMatchNotExhaustive]
                case MissionUnlockMethod.option_missions:
                    world.set_rule(entrance, Has("Mission Unlock", i))
                case MissionUnlockMethod.option_ranks:
                    neonrank_count = get_mission_rank_required(world, i + 1)
                    world.set_rule(entrance, Has("Neon Rank", neonrank_count))

        for level in mission.levels:
            level_region = level.regions[world.player]
            level_region.get_locations()

            if world.use_levels:
                world.set_rule(level_region.entrances[0], Has(level.name))


            if not level.sidequest:
                setters: dict[str, Callable[[Location]]] = {}
                for medal in medals:
                    setters[f"{level.name} {medal.name} Completion"] = partial(_set_rule, world, medal, level.name)
                if options.gifts and not level.giftless:
                    setters[f"{level.name} Gift"] = partial(_set_rule, world, Medal.Gift, level.name)

                for location in level_region.get_locations():
                    setters[location.name](location)
            else:
                _set_rule(world, maxmedal, level.name, level_region.get_locations()[0])
