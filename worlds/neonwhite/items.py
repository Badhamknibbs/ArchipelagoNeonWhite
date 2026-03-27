from BaseClasses import Item, ItemClassification
from typing import NamedTuple

class NWItem(Item):
    game: str = "Neon White"

class NWItemData(NamedTuple):
    category: str
    id: int
    classification: ItemClassification

def get_items_from_category(category: str) -> list[str]:
    itemlist = []
    for item in nw_items:
        if nw_items[item].category == category:
            itemlist.append(item)
    return itemlist

nw_items: dict[str, NWItemData] = {
    "Neon Rank":            NWItemData("Progression", 501, ItemClassification.progression_skip_balancing),

    "Katana":               NWItemData("Card", 502, ItemClassification.progression | ItemClassification.useful),
    "Book of Life":         NWItemData("Card", 503, ItemClassification.progression | ItemClassification.useful),
    "Purify - Fire":        NWItemData("Card", 504, ItemClassification.progression | ItemClassification.useful),
    "Purify - Discard":     NWItemData("Card", 505, ItemClassification.progression | ItemClassification.useful),
    "Elevate - Fire":       NWItemData("Card", 506, ItemClassification.progression | ItemClassification.useful),
    "Elevate - Discard":    NWItemData("Card", 507, ItemClassification.progression | ItemClassification.useful),
    "Godspeed - Fire":      NWItemData("Card", 508, ItemClassification.progression | ItemClassification.useful),
    "Godspeed - Discard":   NWItemData("Card", 509, ItemClassification.progression | ItemClassification.useful),
    "Stomp - Fire":         NWItemData("Card", 510, ItemClassification.progression | ItemClassification.useful),
    "Stomp - Discard":      NWItemData("Card", 511, ItemClassification.progression | ItemClassification.useful),
    "Fireball - Fire":      NWItemData("Card", 512, ItemClassification.progression | ItemClassification.useful),
    "Fireball - Discard":   NWItemData("Card", 513, ItemClassification.progression | ItemClassification.useful),
    "Dominion - Fire":      NWItemData("Card", 514, ItemClassification.progression | ItemClassification.useful),
    "Dominion - Discard":   NWItemData("Card", 515, ItemClassification.progression | ItemClassification.useful),

    "Miracle Katana":       NWItemData("Filler", 516, ItemClassification.filler)
}

item_categories = [
    "Progression",
    "Card",
    "Filler"
]

nw_item_groups = { cat: set(get_items_from_category(cat)) for cat in item_categories }