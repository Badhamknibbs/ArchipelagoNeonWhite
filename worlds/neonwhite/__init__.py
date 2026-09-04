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
    neon_white_levels_medals,
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
        ["Badhamknibbs"]
    )]
    #theme = "partyTime"
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

    @override
    def create_items(self):
        itempool: list[Item] = []

        loc_count = len(self.get_locations())  # pyright: ignore[reportArgumentType]

        # Add soul cards
        itempool += [self.create_item(card) for card in get_items_from_category("Card")]
        total_ranks_clamp: int = min(self.options.total_ranks.value, loc_count - len(itempool))

        if (not getattr(self.multiworld, "re_gen_passthrough", {})):
            self.ranks_required = int(total_ranks_clamp * (self.options.ranks_required_percent / 100))

        match self.options.unlock_method:
            case MissionUnlockMethod.option_missions:
                # Add a number of mission unlock items equal to the mission count - 1
                itempool.extend(self.create_item("Mission Unlock") for _ in range(self.options.mission_count.value - 1))
            case MissionUnlockMethod.option_ranks:
                # Make sure we add the neon ranks that we need
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
        itempool += [self.create_filler() for _ in range(loc_count - len(itempool))]

        self.multiworld.itempool += itempool

    @override
    def get_filler_item_name(self) -> str:
        # Until we make more filler, just stuff the pool with heavenly delight tickets
        return "Heavenly Delight Ticket"

    @override
    def set_rules(self):
        set_rules(self.multiworld, self, self.options)
        rule: Rule | None = None
        match self.options.goal:
            case Goal.option_3bosses:
                medalname = neon_white_levels_medals[self.options.bosses_goal_cap - 1]
                rule = (
                    CanReachLocation(f"The Clocktower {medalname} Completion") &
                    CanReachLocation(f"The Third Temple {medalname} Completion") &
                    CanReachLocation(f"Absolution {medalname} Completion")
                )

        if rule is None:
            raise NotImplementedError("end goal not configured")

        self.set_completion_rule(rule)

    @override
    def fill_slot_data(self):
        dumps = json.dumps([neon_white_level_name_internal[x] for x in self.ordered_levels], separators=(",", ":"))

        cpobj = zlib.compressobj(level=9, wbits=-15, memLevel=9)
        encoded_levels = base64.a85encode(cpobj.compress(dumps.encode()) + cpobj.flush()).decode()

        if self.options.unlock_method == MissionUnlockMethod.option_missions:
            mission_costs = list(range(self.options.mission_count))
        else:
            mission_costs = [
                get_mission_rank_required(self, i + 1)
                    for i in range(self.options.mission_count)
            ]

        options_to_show = [
            "difficulty_knowledge", "difficulty_execution", "boof_shenanigans",
            "medal_select", "gifts", "sidequests", "unlock_method", "goal",
            "death_link"]

        if self.options.goal == Goal.option_3bosses:
            options_to_show.append("bosses_goal_cap")

        return {
            "level_order": encoded_levels,
            "early_levels": self.early_levels,
            "mission_costs": mission_costs,
            "options": self.options.as_dict(*options_to_show)
        }

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
