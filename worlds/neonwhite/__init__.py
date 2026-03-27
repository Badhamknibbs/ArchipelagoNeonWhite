from worlds.AutoWorld import World, WebWorld
from BaseClasses import Tutorial
from .items import NWItem, nw_items, get_items_from_category, nw_item_groups
from .locations import neon_white_get_locations, checks_in_sets_lvl, neon_white_level_name_internal
#from .Locations import PTLocation, pt_locations, pt_location_groups
from .options import NeonWhiteOptions
from .regions import create_regions
from .rules import set_rules, get_required_rank_for_mission
from math import floor
from typing import Any, TextIO
from worlds.LauncherComponents import Component, components, icon_paths, launch as launch_component, Type
nw_base_id = 7307000

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
    options: NeonWhiteOptions
    options_dataclass = NeonWhiteOptions

    item_name_to_id = {name: data.id for name, data in nw_items.items()}

    location_name_to_id = neon_white_get_locations()

    item_name_groups = nw_item_groups
    location_name_groups = checks_in_sets_lvl

    ordered_levels: list[str]   # Post-rando level list, to be split into missions every 11 levels
    neon_rank_increments = 0    # Number of neon rank increments exist in the item pool, determines mission requirement.

    origin_region_name = "Central Heaven"

    web = NeonWhiteWeb()

    def generate_early(self) -> None:
        if not self.player_name.isascii():
            raise Exception("Neon White yaml's slot name has invalid character(s).")

        self.ordered_levels = []

    def create_item(self, name: str) -> NWItem:
        return NWItem(name, nw_items[name].classification, nw_items[name].id, self.player)

    def create_regions(self):
        create_regions(self.player, self.multiworld, self.options)

    def create_items(self):
        neon_white_itempool = []

        locations_to_fill = len(self.multiworld.get_unfilled_locations(self.player))

        # Add soul cards
        for card in get_items_from_category("Card"):
            neon_white_itempool.append(self.create_item(card))
            locations_to_fill = locations_to_fill - 1 # Added an item

        for i in range(locations_to_fill):
            # 1/100 items added for filler will be a miracle katana, the rest will be neon rank increments
            if i + 1 % 100 == 0:
                neon_white_itempool.append(self.create_item("Miracle Katana"))
            else:
                neon_white_itempool.append(self.create_item("Neon Rank"))
                self.neon_rank_increments = self.neon_rank_increments + 1

        self.multiworld.itempool += neon_white_itempool

    def set_rules(self):
        set_rules(self.multiworld, self, self.options, self.neon_rank_increments)
        self.multiworld.completion_condition[self.player] = lambda state: state.can_reach(
            "Absolution Completion", "Location", self.player)

    def get_filler_item_name(self) -> str:
        return "Miracle Katana"

    def fill_slot_data(self):
        return {
            "level_order": {neon_white_level_name_internal(level) for level in self.ordered_levels},
            "rank_increments": int(self.neon_rank_increments),
            "mission_costs": { get_required_rank_for_mission(self.neon_rank_increments, i) for i in range(12) }
        }
