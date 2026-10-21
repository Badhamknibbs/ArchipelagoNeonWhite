import itertools
from collections.abc import Iterable
from typing import NamedTuple

from BaseClasses import Item, ItemClassification

from .info import CAF, LEVEL_INFO, MISSION_INFO
from .options import MissionCount


class NWItem(Item):
    game: str = "Neon White"
    prog_id = 400
    card_id = 500
    level_id = 600
    misc_id = 800

    mission_card_id = 10000 # 1MMCC missionmission cardcard
    fission_card_id = 20000 # same as above, but only for the numbered missions (Fake mISSONS)

    card_classification = ItemClassification.progression | ItemClassification.useful
    usefiller_classification = ItemClassification.useful | ItemClassification.deprioritized | ItemClassification.skip_balancing

class NWItemData(NamedTuple):
    category: str
    id: int
    classification: ItemClassification

def get_items_from_category(category: str) -> Iterable[str]:
    for name, item in nw_items.items():
        if item.category == category:
            yield name

nw_items: dict[str, NWItemData] = {
    CAF.solo_to_string(x): NWItemData("Card", NWItem.card_id + x.bit_length(), NWItem.card_classification)
    for x in CAF
} | {
    "Neon Rank":            NWItemData("Progression", NWItem.prog_id + 0,
        ItemClassification.progression_deprioritized_skip_balancing),
    "Mission Unlock":       NWItemData("Progression", NWItem.prog_id + 1,
        ItemClassification.progression),

    # Generic should not be found in the world; it's just a helper item for FillerWeights
    # because im lazy and i don't want to use schema
    "Generic": NWItemData("Filler", NWItem.misc_id + 99,
        ItemClassification.filler),
    "Heavenly Delight Ticket": NWItemData("Filler", NWItem.misc_id + 0,
        ItemClassification.filler),
    "Insight Crystal Dust": NWItemData("Filler", NWItem.misc_id + 1,
        ItemClassification.filler),
    "Garbage": NWItemData("Filler", NWItem.misc_id + 2,
        ItemClassification.filler),
    "Book of Death Page": NWItemData("Filler", NWItem.misc_id + 3,
        ItemClassification.filler),
    "Cloud 9 Minigolf Ball": NWItemData("Filler", NWItem.misc_id + 4,
        ItemClassification.filler),
    "Neon Mask": NWItemData("Filler", NWItem.misc_id + 5,
        ItemClassification.filler),
    "Secret of Heaven": NWItemData("Filler", NWItem.misc_id + 6,
        ItemClassification.filler),

    "Health Card": NWItemData("Filler", NWItem.misc_id + 51,
        NWItem.usefiller_classification),
    "Ammo Card": NWItemData("Filler", NWItem.misc_id + 52,
        NWItem.usefiller_classification)
} | {
    f"{level}": NWItemData("Level", NWItem.level_id + i, ItemClassification.progression)
        for i, level in enumerate(LEVEL_INFO.keys())
} | {
    name: NWItemData("In-game Mission Card", NWItem.mission_card_id + id, NWItem.card_classification)
    for (name, id) in itertools.chain.from_iterable(
        [[(f"{mission.name} - {CAF.solo_to_string(card)}", (i * 100) + card.bit_length())
            for card in mission.cards]
            for i, mission in enumerate(MISSION_INFO.values())
        ]
    )
} | {
    name: NWItemData("Generated Mission Card", NWItem.fission_card_id + id, NWItem.card_classification)
    for (name, id) in itertools.chain.from_iterable(
        [[(f"Mission {i + 1} - {CAF.solo_to_string(card)}", (i * 100) + card.bit_length())
            for card in CAF]
            for i in range(MissionCount.range_end)
        ]
    )
}

# from pprint import pprint
# pprint(nw_items, sort_dicts=False)

item_categories = [
    "Progression",
    "Card",
    "Filler",
    "Level",
    "In-game Mission Card",
    "Generated Mission Card",
]

nw_item_groups = { cat: set(get_items_from_category(cat)) for cat in item_categories }
