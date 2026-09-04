from collections.abc import Iterable
from typing import NamedTuple

from BaseClasses import Item, ItemClassification

from .locations import neon_white_level_name_internal


class NWItem(Item):
    game: str = "Neon White"
    prog_id = 400
    card_id = 500
    level_id = 600
    misc_id = 800

    card_classification = ItemClassification.progression | ItemClassification.useful

class NWItemData(NamedTuple):
    category: str
    id: int
    classification: ItemClassification

def get_items_from_category(category: str) -> Iterable[str]:
    for name, item in nw_items.items():
        if item.category == category:
            yield name

nw_items: dict[str, NWItemData] = {
    "Katana":               NWItemData("Card", NWItem.card_id +  1, NWItem.card_classification),
    "Book of Life":         NWItemData("Card", NWItem.card_id +  2, NWItem.card_classification),
    "Purify - Fire":        NWItemData("Card", NWItem.card_id +  3, NWItem.card_classification),
    "Purify - Discard":     NWItemData("Card", NWItem.card_id +  4, NWItem.card_classification),
    "Elevate - Fire":       NWItemData("Card", NWItem.card_id +  5, NWItem.card_classification),
    "Elevate - Discard":    NWItemData("Card", NWItem.card_id +  6, NWItem.card_classification),
    "Godspeed - Fire":      NWItemData("Card", NWItem.card_id +  7, NWItem.card_classification),
    "Godspeed - Discard":   NWItemData("Card", NWItem.card_id +  8, NWItem.card_classification),
    "Stomp - Fire":         NWItemData("Card", NWItem.card_id +  9, NWItem.card_classification),
    "Stomp - Discard":      NWItemData("Card", NWItem.card_id + 10, NWItem.card_classification),
    "Fireball - Fire":      NWItemData("Card", NWItem.card_id + 11, NWItem.card_classification),
    "Fireball - Discard":   NWItemData("Card", NWItem.card_id + 12, NWItem.card_classification),
    "Dominion - Fire":      NWItemData("Card", NWItem.card_id + 13, NWItem.card_classification),
    "Dominion - Discard":   NWItemData("Card", NWItem.card_id + 14, NWItem.card_classification),

    "Neon Rank":            NWItemData("Progression", NWItem.prog_id + 0,
        ItemClassification.progression_skip_balancing),
    "Mission Unlock":       NWItemData("Progression", NWItem.prog_id + 1,
        ItemClassification.progression),

    "Heavenly Delight Ticket": NWItemData("Filler", NWItem.misc_id + 0,
        ItemClassification.filler)
} | {
    f"{level}": NWItemData("Level", NWItem.level_id + i, ItemClassification.progression)
        for i, level in enumerate(neon_white_level_name_internal.keys())
}

item_categories = [
    "Progression",
    "Card",
    "Filler",
    "Level"
]

nw_item_groups = { cat: set(get_items_from_category(cat)) for cat in item_categories }
