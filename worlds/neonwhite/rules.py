import dataclasses
import inspect
from collections import deque
from collections.abc import Callable
from functools import partial, reduce
from math import floor
from operator import or_
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeAlias, final
from weakref import WeakKeyDictionary, WeakValueDictionary

from BaseClasses import CollectionState, Location, MultiWorld
from NetUtils import JSONMessagePart
from rule_builder.rules import False_, Has, Rule, True_
from typing_extensions import override

from . import NeonWhiteOptions
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
    _rule: Rule | None = dataclasses.field(init=False)
    _reqstotal: CardAbilityFlags = dataclasses.field(init=False)
    _built: RES_F | None = dataclasses.field(init=False)
    _oreligible: bool = dataclasses.field(init=False)
    _resregistry: WeakKeyDictionary = dataclasses.field(init=False)

    # https://stackoverflow.com/a/71563134
    _registry: ClassVar[WeakValueDictionary] = WeakValueDictionary()
    def __new__(cls, *args, **kwargs) -> Self:
        if args in cls._registry:
            return cls._registry[args]
        i = super().__new__(cls)
        cls._registry[args] = i
        return i

    _true: ClassVar[Rule] = True_()
    _false: ClassVar[Rule] = False_()

    def __init__(self, reqs: frozenset[CardAbilityFlags], level: str) -> None:
        if hasattr(self, "_rule"):
            return
        self.reqs = reqs
        self.level = level
        self._reqstotal = CardAbilityFlags.FistOnly
        for x in reqs:
            self._reqstotal = self._reqstotal.or_(x)
        self._built = None
        self._oreligible = True
        self._resregistry = WeakKeyDictionary()

        self._rule = None
        first = next(iter(self.reqs), None)
        if first is None:
            self._rule = self._false
        elif not first:
            self._rule = self._true

        if True:
            # debug check
            total = reduce(CardAbilityFlags.or_, reqs, CardAbilityFlags.FistOnly)  # pyright: ignore[reportUnreachable]
            assert (total.has_(LEVEL_INFO[level].cards)
                ), f"{level}'s reqs are {total!r}, but only {LEVEL_INFO[level].cards!r} is valid"

    @staticmethod
    def _mkrl_key(itm: tuple[Any, set[CardAbilityFlags]]): return -len(itm[1])

    @staticmethod
    # @lru_cache(maxsize=512) # enable when this ends up being more expensive
    def _make_rule(reqs: frozenset[CardAbilityFlags], ignore = CardAbilityFlags.FistOnly, *, depth=False) -> RES_F:
        # print("CALLB", reqs, ignore)

        total = CardAbilityFlags.FistOnly
        for x in reqs:
            total = total.or_(x)
        total = total.remove_(ignore)

        consumed = set[CardAbilityFlags]()
        cats = {
            x: {r for r in reqs if x.has_(r)}
            for x in total
        }

        res: RES_T = deque()

        key=LevelReqRule._mkrl_key

        while True:
            s = sorted(cats.items(), key=key)

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
                cat = cat.or_(sCat)

            res.appendleft((tuple(cat.to_list()),
                LevelReqRule._make_rule(frozenset(catr), ignore=ignore.or_(cat), depth=True)))

            for cat in cats:
                cats[cat] -= catr
            consumed |= catr

        if not depth and not res:
            # we didn't do shit; we're eligible for just using raw rules
            return ()

        res.extendleft([(tuple(r.to_list()), None)
            for r in
            sorted(((x.remove_(ignore)) for x in reqs if x not in consumed), key=CardAbilityFlags.bit_count)])

        return tuple(res)

    @staticmethod
    def _translate(resf: RES_F, prefix: str, globals: set[str]) -> RES_F:
        if not prefix or not resf:
            return resf
        rest = []
        for items, dig in resf:
            itnew = tuple([prefix + x if x not in globals else x for x in items])
            rest.append((itnew, LevelReqRule._translate(dig, prefix, globals)))
        return tuple(rest)

    @override
    def _instantiate(self, world: "NeonWhiteWorld") -> Rule.Resolved:
        if world in self._resregistry:
            return self._resregistry[world]

        if self._rule is not None:
            res = self._rule.Resolved(player=world.player)
        elif self._built is None:
            self._built = self._make_rule(self.reqs)
            self._oreligible = True
            for _, dig in self._built:  # pyright: ignore[reportOptionalIterable]
                if dig:
                    self._oreligible = False
                    break

            return self._instantiate(world)
        else:
            prefix = world.get_prefix(self.level)
            trimmed = world.global_cards.and_(self._reqstotal)

            if self._oreligible:
                if len(self.reqs) == 1:
                    res = next(iter(self.reqs)).to_rule(prefix, trimmed).resolve(world)
                else:
                    res = reduce(or_, [x.to_rule(prefix, trimmed) for x in self.reqs]).resolve(world)

                if inspect.isfunction(res.explain_json):
                    object.__setattr__(res, 'explain_json', partial(
                        self.explain_json,
                        self.reqs,
                        prefix,
                        trimmed
                    ))

            elif trimmed == self._reqstotal or not prefix:
                prefix = world.get_prefix(self.level)
                trimmed = world.global_cards.and_(self._reqstotal)
                res = self.Resolved(
                    self.reqs,
                    self._built,
                    prefix,
                    trimmed,
                    player=world.player)
            else:
                res = self.Resolved(
                    self.reqs,
                    self._translate(self._built, prefix, trimmed.to_set()),
                    prefix,
                    trimmed,
                    player=world.player)

        self._resregistry[world] = res
        return res

    @staticmethod
    def explain_json(reqs: frozenset[CardAbilityFlags], prefix: str, globals: CardAbilityFlags,
        rule: Rule.Resolved, state: CollectionState | None = None) -> list[JSONMessagePart]:
            return [{'text': repr(r)} for r in reqs]

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
            total = reduce(CardAbilityFlags.or_, self.reqs)
            return {
                CardAbilityFlags.solo_to_string(c, self.prefix if not c.has_(self.globals) else ""): {id(self)}
                for c in total
            }

        @override
        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            return LevelReqRule.explain_json(self.reqs, self.prefix, self.globals, self, state)

        def __str__(self):
            return str(self.built)

# This only represents a single difficulty
@final
class LevelRequirementSet:
    def __init__(self):
        # String is the level name, list is 0..5, in order: dev,ace,gold,silver,bronze,gift
        self.requirements = dict[str, list[LevelReqRule]]()
        self._itemcache: WeakKeyDictionary[NeonWhiteWorld, dict[str, dict[Medal, set[str]]]] = WeakKeyDictionary()

    def nuke_cache(self, world: "NeonWhiteWorld"):
        self._itemcache[world].clear()

    def make_rule(self, level: str, medal: Medal) -> LevelReqRule:
        medal_idx = int(medal) if medal == Medal.Gift else 4 - int(medal)

        return self.requirements[level][medal_idx]

    def get_useful_items(self, world: "NeonWhiteWorld", level: str, medal: Medal | None) -> set[str]:
        if medal is None:
            ret = self.get_useful_items(world, level, world.medalmax)
            if world.options.gifts and not LEVEL_INFO[level].giftless:
                return ret | self.get_useful_items(world, level, Medal.Gift)
            return ret

        cache = self._itemcache.get(world, {}).get(level, {})
        if medal in cache:
            return cache[medal]

        medal_idx = int(medal) if medal == Medal.Gift else 4 - int(medal)
        flags = self.requirements[level][medal_idx].reqs
        if not flags:
            self._itemcache.setdefault(world, {}).setdefault(level, {})[medal] = set()
            return set()

        cards = set()
        total = CardAbilityFlags.FistOnly
        for x in flags:
            total = total.or_(x)

        prefix = world.get_prefix(level)
        for c in total:
            cards.add(CardAbilityFlags.solo_to_string(c, prefix if prefix and not c.has_(world.global_cards) else ""))

        self._itemcache.setdefault(world, {}).setdefault(level, {})[medal] = cards
        return cards

    def __str__(self) -> str:
        return f"LevelReqRule({self.requirements})"

def import_json_to_data(world: "NeonWhiteWorld", know_diff: int, exec_diff: int) -> LevelRequirementSet:
    new_requirements = LevelRequirementSet()
    for entry in world.logic_json:
        solutions = [set[CardAbilityFlags]() for _ in range(6)]
        for solution in world.logic_json[entry]:
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
    mission_fraction: float = float(mission) / world.options.mission_count.value
    lenience_value = 10 # How sharp the curve is, higher = slower rank req but sharper spike near the end
    normal_value = (pow(lenience_value, mission_fraction) - 1) / (lenience_value - 1)
    return floor(world.ranks_required * normal_value)

def _set_rule(world: "NeonWhiteWorld", medal: Medal, level: str, location: Location):
    # set_rule without some fluff
    rule = world.requirement.make_rule(level, medal).resolve(world)
    world.register_rule_dependencies(rule)
    location.access_rule = rule

def set_rules(multiworld: MultiWorld, world: "NeonWhiteWorld", options: NeonWhiteOptions):
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
                    for medal in world.medals
                }
                if options.gifts and not level.giftless:
                    setters[f"{level.name} Gift"] = partial(_set_rule, world, Medal.Gift, level.name)

                for location in level_region.get_locations():
                    setters[location.name](location)
            else:
                _set_rule(world, world.medalmax, level.name, level_region.get_locations()[0])
