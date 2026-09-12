# pyright: reportUnannotatedClassAttribute=false
# pyright: reportMatchNotExhaustive=false

import base64
import json
import zlib
from typing import Any, override

from BaseClasses import Item, MultiWorld, Tutorial
from rule_builder.rules import CanReachLocation, Rule

from worlds.AutoWorld import WebWorld, World

from .items import NWItem, get_items_from_category, nw_item_groups, nw_items
from .locations import (
    checks_in_sets_lvl,
    neon_white_get_locations,
    neon_white_level_name_internal,
    neon_white_levels_giftless,
    neon_white_levels_normal,
    neon_white_levels_sidequests,
)

#from .Locations import PTLocation, pt_locations, pt_location_groups
from .options import (
    ExecutionDifficulty,
    Goal,
    KnowledgeDifficulty,
    MissionUnlockMethod,
    NeonWhiteOptions,
)
from .regions import create_regions
from .rules import (
    LevelRequirements,
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


# Keeping World slim so that it's easier to comprehend
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

    requirements: dict[int, LevelRequirementSet] = {}

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)

        self.ordered_levels: list[str] = []   # Post-rando level list, to be split into missions every 11 levels
        self.early_levels: list[str] = []
        self.ranks_required: int = 0
        self.use_levels: bool = False

        self.requirement: LevelRequirementSet

    @override
    def generate_early(self) -> None:
        if not self.player_name.isascii():
            raise ValueError("Neon White yaml's slot name has invalid character(s).")
        if not all(x in nw_item_groups["Filler"] for x in self.options.filler_weights):
            raise ValueError("Non-filler in filler_weights")

        self.ordered_levels = []

        ut_regen = getattr(self.multiworld, "re_gen_passthrough", {})
        if (self.game in ut_regen):
            ut_regen: dict[str, Any] = ut_regen[self.game]
            self.ordered_levels = ut_regen["levels"]
            self.early_levels = ut_regen["early_levels"]
            self.ranks_required = ut_regen["rank_requirement"]
            self.options.mission_count.value = ut_regen["mission_count"]
            self.options.difficulty_knowledge.value = ut_regen["difficulty_knowledge"]
            self.options.difficulty_execution.value = ut_regen["difficulty_execution"]
            self.options.boof_shenanigans.value = ut_regen["boof_shenanigans"]
            self.options.unlock_method = ut_regen["unlock_method"]
            self.options.total_ranks.value = ut_regen["total_ranks"]

        self.use_levels = self.options.unlock_method == MissionUnlockMethod.option_levels

        req_select = int(self.options.difficulty_knowledge)
        req_select += int(self.options.difficulty_execution) * 10

        if (req_select not in NeonWhiteWorld.requirements):
            NeonWhiteWorld.requirements[req_select] = import_json_to_data(
                self.options.difficulty_knowledge, self.options.difficulty_execution)

        self.requirement = NeonWhiteWorld.requirements[req_select]
        medal_capped = max([Medal(x) for x in self.options.medal_select], default=Medal.Bronze)

        if not ut_regen:
            self.early_levels = []

            for level in neon_white_levels_normal:
                if (self.requirement.can_complete_level(level, medal_capped, LevelRequirements.FistOnly)
                    and self.requirement.can_complete_level(level, Medal.Gift, LevelRequirements.FistOnly)):
                    self.early_levels.append(level)

            cutoff = min(self.options.starting_level_count, len(self.early_levels))

            self.multiworld.random.shuffle(self.early_levels)
            self.early_levels = self.early_levels[:cutoff]

        if self.use_levels:
            remain: int = self.options.starting_level_count - len(self.early_levels)
            if remain > 0:
                levels = neon_white_levels_normal + neon_white_levels_giftless
                if self.options.sidequests:
                    levels.extend(neon_white_levels_sidequests)

                self.early_levels += self.multiworld.random.choices(
                    [x for x in levels if x not in self.early_levels],
                    k = remain)

            for x in self.early_levels:
                self.multiworld.push_precollected(self.create_item(x))

        if (self.options.difficulty_knowledge <= KnowledgeDifficulty.option_vanilla
            or self.options.difficulty_execution <= ExecutionDifficulty.option_casual):
                self.multiworld.push_precollected(self.create_item("Katana"))

    @override
    def create_item(self, name: str) -> NWItem:
        return NWItem(name, nw_items[name].classification, nw_items[name].id, self.player)

    @override
    def create_regions(self):
        create_regions(self.player, self.multiworld, self.options)

    def get_filler_rando(self, k: int = 1):
        fillers = self.options.filler_weights;
        choices = self.multiworld.random.choices(list(fillers.keys()), weights=list(fillers.values()), k=k)
        generics = [x for x in nw_item_groups["Filler"] if nw_items[x].id % 100 < 50]
        return [self.multiworld.random.choice(generics) if x == "Generic" else x for x in choices]

    @override
    def create_items(self):
        itempool: list[Item] = []

        loc_count = len(self.get_locations())  # pyright: ignore[reportArgumentType]

        # Add soul cards
        itempool += [self.create_item(card) for card in get_items_from_category("Card")]

        match self.options.unlock_method:
            case MissionUnlockMethod.option_missions:
                # Add a number of mission unlock items equal to the mission count - 1
                itempool.extend(self.create_item("Mission Unlock") for _ in range(self.options.mission_count.value - 1))
            case MissionUnlockMethod.option_ranks:
                # Make sure we add the neon ranks that we need
                total_ranks_clamp: int = min(self.options.total_ranks.value, loc_count - len(itempool))

                if (not getattr(self.multiworld, "re_gen_passthrough", {})):
                    self.ranks_required = int(total_ranks_clamp * (self.options.ranks_required_percent / 100))

                itempool.extend(self.create_item("Neon Rank") for _ in range(total_ranks_clamp))
            case MissionUnlockMethod.option_levels:
                levels = neon_white_levels_normal + neon_white_levels_giftless
                if self.options.sidequests:
                    levels.extend(neon_white_levels_sidequests)

                itempool.extend(self.create_item(x) for x in levels)

        prec = self.multiworld.precollected_items[self.player].copy()

        for item in itempool:
            if item in prec:
                itempool.remove(item)
                prec.remove(item)

        # Fill the rest with filler
        itempool += [self.create_item(x) for x in self.get_filler_rando(k=loc_count - len(itempool))]

        self.multiworld.itempool += itempool

    @override
    def get_filler_item_name(self) -> str:
        return self.get_filler_rando()[0]

    @override
    def set_rules(self):
        set_rules(self.multiworld, self, self.options)
        rule: Rule | None = None
        match self.options.goal:
            case Goal.option_3bosses:
                # intentionally fail if no medal select
                medalname = max([Medal(x) for x in self.options.medal_select]).name
                rule = (
                    CanReachLocation(f"The Clocktower {medalname} Completion") &
                    CanReachLocation(f"The Third Temple {medalname} Completion") &
                    CanReachLocation(f"Absolution {medalname} Completion")
                )

        if rule is None:
            raise NotImplementedError("end goal not configured")

        self.set_completion_rule(rule)

    @override
    def extend_hint_information(self, hint_data: dict[int, dict[int, str]]):
        hint_data[self.player] = {}

        for location in self.multiworld.get_locations(self.player):
            if location.address is not None and location.parent_region is not None:
                p_region = location.parent_region
                if p_region.name.startswith("Level: ") and p_region.entrances[0].parent_region is not None:
                    hint_data[self.player][location.address] = f"{p_region.entrances[0].parent_region.name}"

    @override
    def fill_slot_data(self):

        extra: dict[str, Any] = {}  # pyright: ignore[reportExplicitAny]

        if self.options.unlock_method != MissionUnlockMethod.option_levels:
            dumps = json.dumps([neon_white_level_name_internal[x] for x in self.ordered_levels], separators=(",", ":"))

            cpobj = zlib.compressobj(level=9, wbits=-15, memLevel=9)
            encoded_levels = base64.a85encode(cpobj.compress(dumps.encode()) + cpobj.flush()).decode()

            extra["level_order"] = encoded_levels

            if self.options.unlock_method == MissionUnlockMethod.option_missions:
                extra["mission_costs"] = list(range(self.options.mission_count))
            elif self.options.unlock_method == MissionUnlockMethod.option_ranks:
                extra["mission_costs"] = [
                    get_mission_rank_required(self, i + 1)
                        for i in range(self.options.mission_count)
                ]

        options_to_show = [
            "difficulty_knowledge", "difficulty_execution", "boof_shenanigans",
            "medal_select", "gifts", "sidequests", "unlock_method", "goal",
            "death_link"]

        if self.options.death_link:
            options_to_show.extend(["death_link_amn", "death_link_res"])

        return {
            "options": self.options.as_dict(*options_to_show)
        } | extra

    def interpret_slot_data(self, slot_data: dict[str, Any]) -> dict[str, Any]:
        reverse = {v: k for k, v in neon_white_level_name_internal.items()}

        dcobj = zlib.decompressobj(-15)
        decoded = json.loads(dcobj.decompress(base64.a85decode(slot_data["level_order"])) + dcobj.flush())

        ret = {
            "levels": [reverse[x] for x in decoded],
            "early_levels": slot_data["early_levels"],
            "rank_requirement": slot_data["mission_costs"][-1],
            "mission_count": len(slot_data["mission_costs"]),
            "difficulty_knowledge": slot_data["options"]["difficulty_knowledge"],
            "difficulty_execution": slot_data["options"]["difficulty_execution"],
            "boof_shenanigans": slot_data["options"]["boof_shenanigans"],
            "unlock_method": slot_data["options"]["unlock_method"],
            "total_ranks": slot_data["options"]["total_ranks"]
        }

        return ret
