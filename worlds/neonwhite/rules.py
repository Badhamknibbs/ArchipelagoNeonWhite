import dataclasses
import json
from collections import deque
from collections.abc import Callable, Iterator
from functools import partial, reduce
from math import floor
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeAlias, final
from weakref import WeakValueDictionary

from BaseClasses import CollectionState, Location, MultiWorld
from NetUtils import JSONMessagePart
from rule_builder.rules import False_, Has, Rule, True_
from typing_extensions import override

from . import NeonWhiteOptions, data
from .info import LEVEL_INFO, CardAbilityFlags, Medal
from .options import (
    MissionUnlockMethod,
)

if TYPE_CHECKING:
    from . import NeonWhiteWorld

RES_F: TypeAlias = tuple[tuple[tuple[str, ...], "RES_F"], ...] | None
RES_T: TypeAlias = deque[tuple[tuple[str, ...], "RES_F"]]

@dataclasses.dataclass()
class LevelReqRule(Rule["NeonWhiteWorld"], game="Neon White"):
    reqs: frozenset[CardAbilityFlags] = dataclasses.field(init=False)
    level: str = dataclasses.field(init=False)
    _reqstotal: CardAbilityFlags = dataclasses.field(init=False)
    _built: RES_F | None = dataclasses.field(init=False)
    _resregistry: WeakValueDictionary = dataclasses.field(init=False)

    # https://stackoverflow.com/a/71563134
    _registry: ClassVar[WeakValueDictionary] = WeakValueDictionary()
    def __new__(cls, *args, **kwargs) -> Self:
        if args in cls._registry:
            return cls._registry[args]
        i = super().__new__(cls)
        cls._registry[args] = i
        return i

    def __init__(self, reqs: frozenset[CardAbilityFlags], level: str) -> None:
        if hasattr(self, "_rule"):
            return
        self.reqs = reqs
        self.level = level
        self._reqstotal = reduce(CardAbilityFlags.or_, self.reqs, CardAbilityFlags.FistOnly)
        self._built = None
        self._resregistry = WeakValueDictionary()
        if False:
            # debug check
            total = reduce(CardAbilityFlags.or_, reqs, CardAbilityFlags.FistOnly)  # pyright: ignore[reportUnreachable]
            if not total.has_flags(LEVEL_INFO[level].cards):
                raise Exception(f"{level}'s reqs are {total!r}, but only {LEVEL_INFO[level].cards!r} is valid")  # noqa: TRY002


    @staticmethod
    # @lru_cache(maxsize=512) # enable when this ends up being more expensive
    def _make_rule(reqs: frozenset[CardAbilityFlags], ignore = CardAbilityFlags.FistOnly) -> RES_F:
        # print("CALLB", reqs, ignore)
        total = reduce(CardAbilityFlags.or_, reqs, CardAbilityFlags.FistOnly) & ~ignore
        consumed = set[CardAbilityFlags]()
        cats = {
            x: {r for r in reqs if x.has_(r)}
            for x in total
        }

        res: RES_T = deque()

        key=lambda itm: len(itm[1])
        while True:
            s = sorted(cats.items(), key=key, reverse=True)

            catr = s[0][1].copy()
            catrlen = len(catr)
            if catrlen <= 1:
                break

            cat = CardAbilityFlags.FistOnly

            for sCat, sCatr in s:
                if catrlen > len(sCatr):
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
            sorted(((x & ~ignore) for x in reqs if x not in consumed), key=CardAbilityFlags.bit_count)])

        return tuple(res)

    @staticmethod
    def _merge_O(rule: Rule, req: CardAbilityFlags) -> Rule:
        return req.to_rule() | rule

    def _make_rule_O(self) -> "Rule":
        return reduce(LevelReqRule._merge_O, sorted(self.reqs, key=lambda x: x.bit_count(), reverse=True), False_())

    @staticmethod
    def _translate(resf: RES_F, prefix: str, globals: set[str]) -> RES_F:
        if not resf:
            return resf
        rest = []
        for items, dig in resf:
            itnew = tuple([prefix + x if x not in globals else x for x in items])
            rest.append((itnew, LevelReqRule._translate(dig, prefix, globals)))
        return tuple(rest)

    @override
    def _instantiate(self, world: "NeonWhiteWorld") -> Rule.Resolved:
        whash = hash(world)
        if whash in self._resregistry:
            return self._resregistry[whash]

        if not self.reqs:
            res = False_().resolve(world)
        elif not next(iter(self.reqs)):
            res = True_().resolve(world)
        else:
            if self._built is None:
                self._built = self._make_rule(self.reqs)

            prefix = world.get_prefix(self.level)
            trimmed = world.global_cards & self._reqstotal
            if trimmed == self._reqstotal or not prefix:
                res = self.Resolved(
                    self.reqs,
                    self._built,
                    prefix,
                    trimmed,
                    player=world.player)
            else:
                res = self.Resolved(
                    self.reqs,
                    LevelReqRule._translate(self._built, prefix, trimmed.to_set()),
                    prefix,
                    trimmed,
                    player=world.player)

        self._resregistry[whash] = res
        return res

    class Resolved(Rule.Resolved):
        reqs: frozenset[CardAbilityFlags]
        built: RES_F
        prefix: str
        globals: CardAbilityFlags

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            iterstack = [iter(self.built)]  # pyright: ignore[reportArgumentType, reportCallIssue]
            playeri = state.prog_items[self.player]

            while iterstack:
                it = iterstack[-1]
                for items, dig in it: # one of the funniest lines of code i've written
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
        def item_dependencies(self) -> dict[str, set[int]]:
            total = reduce(CardAbilityFlags.or_, self.reqs, CardAbilityFlags.FistOnly)
            return {
                CardAbilityFlags.solo_to_string(c, self.prefix if not c.has_(self.globals) else ""): {id(self)}
                for c in total
            }

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

    def get_useful_items(self, world: "NeonWhiteWorld", level: str, medal: Medal | None) -> set[str]:
        if medal is None:
            ret = self.get_useful_items(world, level, max([Medal(x) for x in world.options.medal_select]))
            if world.options.gifts and not LEVEL_INFO[level].giftless:
                return ret | self.get_useful_items(world, level, Medal.Gift)
            return ret

        cards = set()
        total = reduce(CardAbilityFlags.or_, self.get_necessary_items(level, medal), CardAbilityFlags.FistOnly)
        prefix = world.get_prefix(level)
        for c in total:
            cards.add(CardAbilityFlags.solo_to_string(c, prefix if not c.has_(world.global_cards) else ""))

        return cards


NWJSON_DATA: Any = {}

def import_json_to_data(know_diff: int, exec_diff: int) -> LevelRequirementSet:
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
                if any(x.has_(reqs) for x in solutions[5]):
                    continue

                solutions[5].add(reqs)
            else:
                for i in range(capped, 5):
                    if any(x.has_(reqs) for x in solutions[i]):
                        continue

                    solutions[i].add(reqs)

        new_requirements.requirements[entry] = [LevelReqRule(frozenset(x), entry) for x in solutions]
    return new_requirements

# Actual functions related to rules start here
def level_rando(world: "NeonWhiteWorld", level_req: dict[str, set[str]], cards: set[str], k: int, *,
    shuffled: list[tuple[str, set[str]]] | None = None) -> Iterator[str]:
    variance = float(world.options.level_gradient) / 100
    if not shuffled:
        shuffled = list(level_req.items())
        world.random.shuffle(shuffled)

    weights = {l: float(len(req - cards)) for l, req in shuffled}
    maxweights = max(x for x in weights.values())
    for l in weights:
        weights[l] *= 1 - variance
        weights[l] += world.random.uniform(0, maxweights) * variance

    change = False
    for i in range(k):
        if not level_req:
            yield "Absolution"
            return
        if change:
            yield from level_rando(world, level_req, cards, k - i, shuffled=shuffled)
            return

        # https://stackoverflow.com/a/3282904
        # typechecker don't like .get
        least = min(weights, key=weights.__getitem__)
        # print(least, len(cards), level_req[least])
        newc = level_req[least]
        change = not newc.issubset(cards)
        cards |= level_req[least]
        del level_req[least]
        del weights[least]
        shuffled.remove((least, newc))
        yield least


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
    # set_rule without some fluff
    rule = world.requirement.make_rule(level, medal).resolve(world)
    world.register_rule_dependencies(rule)
    location.access_rule = rule

def set_rules(multiworld: MultiWorld, world: "NeonWhiteWorld", options: NeonWhiteOptions):
    medals = [Medal(x) for x in options.medal_select]
    maxmedal = max(medals, default=Medal.Bronze)

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

            if world.use_levels:
                world.set_rule(level_region.entrances[0], Has(level.name))


            if not level.sidequest:
                setters: dict[str, Callable[[Location]]] = {
                    f"{level.name} {medal.name} Completion": partial(_set_rule, world, medal, level.name)
                    for medal in medals
                }
                if options.gifts and not level.giftless:
                    setters[f"{level.name} Gift"] = partial(_set_rule, world, Medal.Gift, level.name)

                for location in level_region.get_locations():
                    setters[location.name](location)
            else:
                _set_rule(world, maxmedal, level.name, level_region.get_locations()[0])
