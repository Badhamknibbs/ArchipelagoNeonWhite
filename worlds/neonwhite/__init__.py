# pyright: reportUnannotatedClassAttribute=false
# pyright: reportMatchNotExhaustive=false

import base64
import itertools
import json
import zlib
from collections import Counter
from collections.abc import Callable
from functools import reduce
from operator import or_
from typing import TYPE_CHECKING, Any

from BaseClasses import (
    CollectionRule,
    Item,
    ItemClassification,
    Location,
    MultiWorld,
    Tutorial,
)
from Options import Option, OptionError
from rule_builder.rules import Has, Rule

from worlds.AutoWorld import WebWorld, World

from . import data
from .info import LEVEL_INFO, MISSION_INFO, CardAbilityFlags, MissionInfo
from .items import NWItem, get_items_from_category, nw_item_groups, nw_items
from .locations import (
    checks_in_sets_lvl,
    neon_white_get_locations,
)

#from .Locations import PTLocation, pt_locations, pt_location_groups
from .options import (
    CardTypes,
    ExecutionDifficulty,
    Goal,
    MissionUnlockMethod,
    NeonWhiteOptions,
)
from .regions import create_regions, level_rando
from .rules import (
    LevelRequirementSet,
    Medal,
    get_mission_rank_required,
    import_json_to_data,
    set_rules,
)


class NeonWhiteWeb(WebWorld):
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Neon White integration for Archipelago multiworld games.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Badhamknibbs", "stxticOVFL"]
    )]
    theme = "partyTime"
    bug_report_page = "https://github.com/Badhamknibbs/ArchipelagoNeonWhite/issues"

class NeonWhiteWorld(World):
    """
    Neon White is a speedrunning FPS puzzle platformer made by freaks for freaks.
    Rush through a series of levels making smart use of your restricted cards to clear heaven of demons.
    """

    game = "Neon White"
    origin_region_name = "Central Heaven"
    options: NeonWhiteOptions  # pyright: ignore[reportIncompatibleVariableOverride]
    options_dataclass = NeonWhiteOptions
    web = NeonWhiteWeb()

    item_name_to_id = {name: data.id for name, data in nw_items.items()}  # noqa: RUF012

    location_name_to_id = neon_white_get_locations()

    item_name_groups = nw_item_groups
    location_name_groups = checks_in_sets_lvl

    requirements: dict[tuple[int, int], LevelRequirementSet] = {}  # noqa: RUF012
    logic_json: Any = None

    ut_can_gen_without_yaml = True

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)

        self.ordered_levels: list[str] = []   # Post-rando level list, to be split into missions every 11 levels
        self.ranks_required: int = 0
        self.use_levels: bool = False

        self.requirement: LevelRequirementSet

        self.missions: tuple[MissionInfo, ...] = ()
        self.missions_vanilla: tuple[MissionInfo, ...] = ()

        self.get_prefix: Callable[[str], str] = lambda _: ""

    def generate_early(self) -> None:
        if not self.player_name.isascii():
            raise OptionError("Neon White yaml's slot name has invalid character(s).")
        if not all(x in nw_item_groups["Filler"] for x in self.options.filler_weights):
            raise OptionError("Non-filler in filler_weights")
        if len(self.options.medal_select.value) < 2:
            raise OptionError("Not enough medals selected")

        ut_regen = getattr(self.multiworld, "re_gen_passthrough", {})
        if (self.game in ut_regen):
            ut_regen: dict[str, Any] = ut_regen[self.game]
            print(f"UT_REGEN: {ut_regen}")
            self.ordered_levels = ut_regen["levels"]
            self.ranks_required = ut_regen.get("rank_requirement", 0)

            # from the UT docs (sorry mario sunshine)
            for key, value in ut_regen.items():
                opt: Option | None = getattr(self.options, key, None)
                if opt is not None:
                    setattr(self.options, key, opt.from_any(value))

        self.medals = sorted([Medal(x) for x in self.options.medal_select])
        self.medalmax = max(self.medals)

        self.missions_vanilla = tuple([i for i in MISSION_INFO.values() if self.options.sidequests or not i.sidequest])
        self.use_levels = self.options.unlock_method.value == MissionUnlockMethod.option_levels

        match self.options.card_types.value:
            case CardTypes.option_ingame_missions:
                self.get_prefix = self._prefix_vanill
            case CardTypes.option_generated_missions:
                self.get_prefix = self._prefix_genert

        req_select = (self.options.difficulty_knowledge.value, self.options.difficulty_execution.value)

        if not NeonWhiteWorld.logic_json:
            from importlib.resources import files
            file = files(data).joinpath("nw_cr.json").open()
            NeonWhiteWorld.logic_json = json.loads(file.read())

        if (req_select not in NeonWhiteWorld.requirements):
            NeonWhiteWorld.requirements[req_select] = import_json_to_data(self,
                self.options.difficulty_knowledge.value, self.options.difficulty_execution.value)

        self.requirement = NeonWhiteWorld.requirements[req_select]

        if (self.options.difficulty_execution.value <= ExecutionDifficulty.option_casual):
            self.multiworld.push_precollected(self.create_item("Katana"))

        self.global_cards = CardAbilityFlags.FistOnly
        prec = self.multiworld.precollected_items[self.player]

        if (self.options.card_types != CardTypes.option_global):
            gcardset = set(get_items_from_category("Global Card"))
            mygcards = self.options.global_cards.value

            for item in prec:
                if item.name in gcardset:
                    mygcards.add(item.name)

            csfold = {x.casefold(): x for x in get_items_from_category("Global Card")}

            for card in mygcards:
                self.global_cards |= CardAbilityFlags(1 << (nw_items[csfold[card.casefold()]].id % 100 - 1))

    def create_item(self, name: str, force_useful: bool = False) -> NWItem:
        classific = ItemClassification.useful if force_useful else nw_items[name].classification
        return NWItem(name, classific, nw_items[name].id, self.player)

    def create_regions(self):
        # create levels and missions

        if self.use_levels:
            self.missions = self.missions_vanilla
            create_regions(self.multiworld, self, self.options)

        if not self.ordered_levels:
            total_level_count = 0

            prec = self.multiworld.precollected_items[self.player]
            starters = set[str]()
            early = list[str]()

            for item in prec:
                if "Card" in nw_items[item.name].category:
                    starters.add(item.name)

            global_filter = self.global_cards.to_set() | starters

            levels: dict[str, set[str]] = {}
            for level in itertools.chain.from_iterable([x.levels for x in self.missions_vanilla]):
                total_level_count += 1
                if level.name == "Absolution":
                    continue
                levels[level.name] = self.requirement.get_useful_items(self, level.name, None) - starters
                if not levels[level.name] and (not level.giftless or not self.options.gifts):
                    early.append(level.name)

            # preshuffle that shit
            litems = list(levels.items())
            self.random.shuffle(litems)
            levels = dict(litems)
        else:
            total_level_count = len(self.ordered_levels)

        if not self.use_levels:
            mission_count = self.options.mission_count.value
            levels_norm = total_level_count // mission_count
            offset = mission_count - (total_level_count % mission_count)

        if TYPE_CHECKING: # AGAIN??
            assert isinstance(mission_count, int)  # pyright: ignore[reportPossiblyUnboundVariable, reportArgumentType]
            assert isinstance(levels_norm, int) # pyright: ignore[reportPossiblyUnboundVariable, reportArgumentType]
            assert isinstance(offset, int) # pyright: ignore[reportPossiblyUnboundVariable, reportArgumentType]

        if not self.ordered_levels:
            cards = set[str]()
            if TYPE_CHECKING: # god
                assert isinstance(starters, set[str])  # pyright: ignore[reportPossiblyUnboundVariable, reportArgumentType]
                assert isinstance(global_filter, set[str]) # pyright: ignore[reportPossiblyUnboundVariable, reportArgumentType]
                assert isinstance(early, list[str]) # pyright: ignore[reportPossiblyUnboundVariable, reportArgumentType]
                assert isinstance(levels, dict[str, set[str]]) # pyright: ignore[reportPossiblyUnboundVariable, reportArgumentType]

            if self.options.unlock_method.value == MissionUnlockMethod.option_missions:
                for i in range(mission_count):
                    level_count = levels_norm
                    if i >= offset:
                        level_count += 1

                    bef = cards.copy()
                    for c in starters:
                        if c.startswith(f"Mission {i + 1}"):
                            cards.add(c.split(' - ')[1])

                    merge = (cards - global_filter) | starters
                    uniq = set(early)
                    for lname, lcards in levels.items():
                        if lname in uniq:
                            continue
                        level = LEVEL_INFO[lname]
                        if lcards.issubset(merge) and (not level.giftless or not self.options.gifts):
                            early.append(lname)

                    for l in level_rando(self, levels.copy(), cards, level_count):
                        levels.pop(l, None)
                        self.ordered_levels.append(l)

                    cards &= global_filter
                    if bef != cards:
                        diff = cards - bef
                        for l, c in levels.items():
                            if not c.isdisjoint(diff):
                                levels[l] = c - diff
            else:
                self.ordered_levels = list(level_rando(self, levels, cards, total_level_count))

            cutoff = min(self.options.starting_level_count.value, len(early))
            self.random.shuffle(early)
            early = early[:cutoff]

            self.ordered_levels = early + [x for x in self.ordered_levels if x not in early]

        if self.use_levels:
            early = [x for x in self.ordered_levels[:self.options.starting_level_count.value]]

            for x in early:
                self.multiworld.push_precollected(self.create_item(x))

            return # we're fully done here, rest of the code is missions generation

        missions: list[MissionInfo] = []

        level_total = 0
        for i in range(mission_count):
            level_count = levels_norm
            if i >= offset:
                level_count += 1

            missions.append(
                MissionInfo(
                    tuple(self.ordered_levels[level_total : (level_total + level_count)]),
                    alias=f"Mission {i + 1}"
                )
            )

            level_total += level_count

        self.missions = tuple(missions)
        if self.options.card_types.value == CardTypes.option_generated_missions:
            self.requirement.nuke_cache(self)

        # print(self.missions)

        create_regions(self.multiworld, self, self.options)

    def get_filler_rando(self, k: int = 1):
        fillers = self.options.filler_weights.value
        print(fillers)
        choices = self.random.choices(list(fillers.keys()), weights=list(fillers.values()), k=k)
        genc = choices.count("Generic")
        generics = [x for x in sorted(nw_item_groups["Filler"]) if nw_items[x].id % 100 < 50]
        return [x for x in choices if x != "Generic"] + self.random.choices(generics, k=genc)

    def create_items(self):
        itempool: list[Item] = []
        loc_count = len(self.multiworld.get_unfilled_locations(self.player))  # pyright: ignore[reportArgumentType]

        prog_cards: set[str] = reduce(or_,
            [self.requirement.get_useful_items(self, l.name, None)
                for l in itertools.chain.from_iterable([m.levels for m in self.missions])])

        # Add soul cards
        if self.options.card_types.value == CardTypes.option_global:
            itempool += [self.create_item(card, card not in prog_cards) for card in get_items_from_category("Global Card")]
        else:
            missions = self.missions
            if self.options.card_types.value == CardTypes.option_ingame_missions and not self.use_levels:
                missions = self.missions_vanilla

            itempool += [self.create_item(
                CardAbilityFlags.solo_to_string(c), CardAbilityFlags.solo_to_string(c) not in prog_cards)
                for c in self.global_cards]

            for mission in missions:
                itempool += [self.create_item(
                    f"{mission.name or mission.alias} - {CardAbilityFlags.solo_to_string(c)}",
                    f"{mission.name or mission.alias} - {CardAbilityFlags.solo_to_string(c)}" not in prog_cards)
                    for c in mission.cards if c not in self.global_cards]

        prec = self.multiworld.precollected_items[self.player].copy()
        # cleanse once: matters for ranks mode
        for item in itempool.copy():
            if item in prec:
                itempool.remove(item)
                prec.remove(item)

        match self.options.unlock_method.value:
            case MissionUnlockMethod.option_missions:
                # Add a number of mission unlock items equal to the mission count - 1
                itempool += [self.create_item("Mission Unlock") for _ in range(self.options.mission_count.value - 1)]
            case MissionUnlockMethod.option_ranks:
                # Make sure we add the neon ranks that we need
                total_ranks_clamp: int = min(self.options.total_ranks.value, loc_count - len(itempool))

                if (not getattr(self.multiworld, "re_gen_passthrough", {})):
                    self.ranks_required = int(total_ranks_clamp * (self.options.ranks_required_percent.value / 100.0))

                itempool += [self.create_item("Neon Rank", i >= self.ranks_required) for i in range(total_ranks_clamp)]
            case MissionUnlockMethod.option_levels:
                itempool += [self.create_item(x) for x in self.ordered_levels if x not in prec]

        # 2nd cleanse: matters mostly for levels mode
        for item in itempool.copy():
            if item in prec:
                itempool.remove(item)
                prec.remove(item)

        if len(itempool) > loc_count:
            raise OptionError(f"Settings create more items ({len(itempool)}) than there are locations ({loc_count})")

        # Fill the rest with filler
        itempool += [self.create_item(x) for x in self.get_filler_rando(k=loc_count - len(itempool))]

        self.multiworld.itempool += itempool

    def get_filler_item_name(self) -> str:
        return self.get_filler_rando()[0]

    def _prefix_vanill(self, level: str):
        mission = next((m for m in self.missions_vanilla if level in m.level_names), None)
        if mission:
            return f"{mission.name or mission.alias} - "
        return ""
    def _prefix_genert(self, level: str):
        mission = next((m for m in self.missions if level in m.level_names), None)
        if mission:
            return f"{mission.name or mission.alias} - "
        return ""

    def set_rules(self):
        set_rules(self.multiworld, self, self.options)
        rule: CollectionRule | Rule[NeonWhiteWorld] | None = None
        match self.options.goal.value:
            case Goal.option_3bosses:
                # intentionally fail if no medal select
                if len(self.options.medal_select.value) == 0:
                    raise OptionError("Not enough medals selected")

                postreq = (self.requirement.make_rule("Absolution", self.medalmax) &
                        self.requirement.make_rule("The Third Temple", self.medalmax) &
                        self.requirement.make_rule("The Clocktower", self.medalmax))

                match self.options.unlock_method.value:
                    case MissionUnlockMethod.option_ranks:
                        rule = Has("Neon Rank", self.ranks_required)
                    case MissionUnlockMethod.option_missions:
                        rule = Has("Mission Unlock", self.options.mission_count.value - 1)
                    case MissionUnlockMethod.option_levels:
                        rule = Has("Absolution") & Has("The Third Temple") & Has("The Clocktower")

                rule &= postreq  # pyright: ignore[reportOperatorIssue]/

        if rule is None:
            raise OptionError("End goal not configured")

        for mission in self.missions:
            print("- " + str(list(mission.regions[self.player].exits)))
            print(": " + str(mission.regions[self.player].entrances[0].access_rule))

            for level in mission.levels:
                for loc in level.regions[self.player].locations:
                    print("  - " + loc.name)
                    print("  : " + str(loc.access_rule))


        self.set_completion_rule(rule)

    def fill_hook(self,
            progitempool: list[Item],
            usefulitempool: list[Item],
            filleritempool: list[Item],
            fill_locations: list[Location]):
        # order every item to be as we want it to help fill gen
        # **keeping our items in the same general position across the multiworld**

        # from pprint import pprint

        # grab all of our items
        indices: list[int]
        items: list[NWItem]
        indices, items = [[*l] for l in zip(*[(i, item) for i, item in enumerate(progitempool)
                                if item.player == self.player])]

        def grab(itemname: str):
            i = next(i for (i, item) in enumerate(items) if item.name == itemname)
            return items.pop(i)

        newitems: list[Item] = self.multiworld.precollected_items[self.player].copy()
        precollected = len(newitems)
        done = {x.name for x in newitems}

        if self.use_levels:
            for level in self.ordered_levels:
                level_items = self.requirement.get_useful_items(self, level, None) - done

                done |= level_items
                newitems += [grab(x) for x in sorted(level_items)]
                if level not in done:
                    newitems.append(grab(level))
        else:
            have = sum(x.name ==
                ("Neon Rank" if self.options.unlock_method.value == MissionUnlockMethod.option_ranks else "Mission Unlock")
                for x in newitems)

            # sort all of the card abilities from most to least helpful
            # to try to hint to the fill which should probably go first
            for i, mission in enumerate(self.missions):
                itemcount = Counter(itertools.chain.from_iterable([
                    sorted(self.requirement.get_useful_items(self, l.name, None) - done)
                    for l in mission.levels]))

                done |= itemcount.keys()
                newitems += [grab(itemname) for itemname, _ in itemcount.most_common()]

                # put all the required unlocks ranks after the mission
                if self.options.unlock_method.value == MissionUnlockMethod.option_ranks:
                    req = get_mission_rank_required(self, i + 1)
                    if have < req:
                        newitems += [grab("Neon Rank") for _ in range(req - have)]
                    have = req
                else:
                    if have < i:
                        newitems += [grab("Mission Unlock") for _ in range(i - have)]
                    have = i


        # now copy them over to the prog item pool in our new order

        # print(len(indices), indices)
        # print(len(sorted), sorted)
        # print(len(items), items)
        for i, ind in enumerate(indices):
            progitempool[ind] = newitems[i + precollected]

        # print(progitempool)

    def extend_hint_information(self, hint_data: dict[int, dict[int, str]]):
        playerdata = {}

        for mission in self.missions:
            for level in mission.levels:
                for loc in level.regions[self.player].get_locations():
                    playerdata[loc.address] = mission.alias or mission.name

        hint_data[self.player] = playerdata

    def fill_slot_data(self):
        # pprint(self.missions)

        extra: dict[str, Any] = {}  # pyright: ignore[reportExplicitAny]

        dumps = json.dumps([LEVEL_INFO[x].id for x in self.ordered_levels], separators=(",", ":"))

        cpobj = zlib.compressobj(level=9, wbits=-15, memLevel=9)
        encoded_levels = base64.a85encode(cpobj.compress(dumps.encode()) + cpobj.flush()).decode()

        extra["level_order"] = encoded_levels

        if self.options.unlock_method.value == MissionUnlockMethod.option_missions:
            extra["mission_costs"] = list(range(self.options.mission_count))
        elif self.options.unlock_method.value == MissionUnlockMethod.option_ranks:
            extra["mission_costs"] = [
                get_mission_rank_required(self, i + 1)
                    for i in range(self.options.mission_count)
            ]

        options_to_show = [
            # "start_inventory", "start_inventory_from_pool", # these do influence level order
            "difficulty_knowledge", "difficulty_execution", # "boof_shenanigans",
            "medal_select", "gifts", "sidequests", "starting_level_count",
            "unlock_method", "goal", "card_types",
            "death_link"]

        if self.options.death_link:
            options_to_show += ["death_link_amn", "death_link_res"]

        if self.options.unlock_method.value == MissionUnlockMethod.option_ranks:
            options_to_show += ["total_ranks"]

        if self.options.card_types.value != CardTypes.option_global:
            options_to_show += ["global_cards"]

        print(f"OPTIONS: {({f: getattr(self.options, f).value for f in self.options.__class__.type_hints})}")

        return {
            "options": self.options.as_dict(*options_to_show)
        } | extra

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        extra: dict[str, Any] = {}  # pyright: ignore[reportExplicitAny]
        unlock = slot_data["options"]["unlock_method"]

        reverse = {l.id: l.name for l in LEVEL_INFO.values()}

        dcobj = zlib.decompressobj(-15)
        decoded = json.loads(dcobj.decompress(base64.a85decode(slot_data["level_order"])) + dcobj.flush())

        extra["levels"] = [reverse[x] for x in decoded]
        if unlock != MissionUnlockMethod.option_levels:
            extra["mission_count"] = len(slot_data["mission_costs"])
            extra["rank_requirement"] = slot_data["mission_costs"][-1]

            if (unlock == MissionUnlockMethod.option_ranks):
                extra["total_ranks"] = slot_data["options"]["total_ranks"]

        cardtypes = slot_data["options"]["card_types"]
        if cardtypes != CardTypes.option_global:
            extra["global_cards"] = slot_data["options"]["global_cards"]

        return {
            "unlock_method": unlock,
            "goal": slot_data["options"]["goal"],
            "difficulty_knowledge": slot_data["options"]["difficulty_knowledge"],
            "difficulty_execution": slot_data["options"]["difficulty_execution"],
            # "boof_shenanigans": slot_data["options"]["boof_shenanigans"],
            "starting_level_count": slot_data["options"]["starting_level_count"],
            "gifts": slot_data["options"]["gifts"],
            "sidequests": slot_data["options"]["sidequests"],
            "medal_select": slot_data["options"]["medal_select"],
            "card_types": cardtypes
        } | extra
