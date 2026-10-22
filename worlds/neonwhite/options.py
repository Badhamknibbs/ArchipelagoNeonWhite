# pyright: reportUnannotatedClassAttribute=false

from dataclasses import dataclass

from Options import (
    Choice,
    DeathLink,
    DefaultOnToggle,
    ItemDict,
    OptionSet,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
    Toggle,
)

from .info import CAF, MEDALS


class KnowledgeDifficulty(Choice):
    """
    How much understanding of the games mechanics is expected to figure out the solution to a given medal/gift/etc.
    Vanilla: *Only* allow cards and strats the basegame shows you.
    Casual: Expects the bare minimum, only tricks that are taught with in-game tutorials to beat the vanilla game.
    Standard: Incorporates hidden but usually intended or otherwise easy to intuit tech/ideas.
    Expert: Further includes some more advanced tech that is often only relevant to speedrunners.
    Master: Encompasses everything else from level-specific tech to extremely niche game quirks or nuances.
    """
    display_name = "Knowledge Difficulty"
    # option_vanilla = 1
    option_casual = 2
    option_standard = 3
    option_expert = 4
    option_master = 5
    default = 3

class ExecutionDifficulty(Choice):
    """
    How hard it is to actually execute a given solution to a given medal/gift/etc, assuming all knowledge.
    Vanilla: *Only* allow cards and strats the basegame shows you.
    Casual: Can be done by a brand-new player with minimal hassle.
    Standard: Consistently doable by a player who has all aces, especially players with dev medals.
    Expert: Doable by a player who has all dev medals and is competent with advanced tech.
    Master: Unreasonably difficult solutions that are inconsistent/overly precise to the vast majority of players.
    """
    display_name = "Execution Difficulty"
    # option_vanilla = 1
    option_casual = 2
    option_standard = 3
    option_expert = 4
    option_master = 5
    default = 3

class BoofShenanigans(Toggle):
    """
    Whether to include things like clips and far off Book of Life usages in the logic.
    === DOES NOT DO ANYTHING ATM ===
    """
    display_name = "Book of Life Shenanigans"

class Gifts(DefaultOnToggle):
    """
    Whether or not to make gifts checks.
    """

class Sidequests(DefaultOnToggle):
    """
    Whether or not to make sidequest completions checks.
    """

class CardTypes(Choice):
    """
    What card abilities should be placed in the multiworld.
    See also Global Cards for fine-tuning the Missions types.
    Global: 1 item for each ability that unlocks the ability for all levels.
    Ingame Missions: An item for each ability that unlocks the ability on a per-mission (vanilla missions) basis.
    Generated Missions: An item for each ability that unlocks the ability on a per-mission (your world's missions) basis.
    """
    display_name = "Card Ability Types"
    option_global = 1
    option_ingame_missions = 2
    option_generated_missions = 3
    default = 2

class GlobalCards(OptionSet):
    """
    When using either of the "Missions" Card Ability Types, which cards to force to be global.
    (e.g. if Katana is here, there is only one Katana item to get it for the entire game)
    """
    display_name = "Global Cards"
    valid_keys = tuple([CAF.solo_to_string(x).casefold() for x in CAF])
    valid_keys_casefold = True
    default = {"Katana", "Book of Life"}

class MissionUnlockMethod(Choice):
    """
    How missions are unlocked to progress through the game.
    Ranks: Fills the pool with Neon Ranks, each mission requiring a number of ranks to unlock. See Rank Requirement.
    Missions: 1 Mission Unlock item is added to the pool per mission, each obtained unlocking the next locked mission.
    Levels: Each level is an item that must be collected
    """
    display_name = "Mission Unlock Method"
    option_ranks = 1
    option_missions = 2
    option_levels = 3
    default = 1

class StartingLevelCount(Range):
    """
    The amount of Levels for you to start with for Levels unlock method.
    This also influences how many fist-only levels are added early into the level pool for other unlock methods.
    """
    display_name = "Starting Level Count"
    range_start = 1
    default = 5
    range_end = 10

class MedalSelect(OptionSet):
    """
    Which medals to have as checks.
    Format as a comma-separated list of medal names: ["Bronze", "Ace"].
    Medals available are: Bronze, Silver, Gold, Ace, and Dev. Case-insensitive.
    """
    display_name = "Medal Selection"
    valid_keys = tuple([x.casefold() for x in MEDALS])
    valid_keys_casefold = True
    default = {"Bronze", "Ace"}

class TotalRanks(Range):
    """
    How many total Neon Ranks to add to the pool.
    Only applies when Mission Unlock Method is set to Ranks.
    """
    display_name = "Total Neon Ranks"
    range_start = 1
    default = 100
    range_end = 300

class RanksRequiredPercentage(Range):
    """
    Percentage of existing Neon Ranks required to open the last mission.
    The rest of the mission requirements will scale accordingly.
    Only applies when Mission Unlock Method is set to Ranks.
    """
    display_name = "Ranks Required Percentage"
    range_start = 1
    default = 80
    range_end = 100


class MissionCount(Range):
    """
    The amount of Missions for the game to have when ranks or mission unlock method is chosen.
    Spreads levels as evenly as it can, then spreads across the later half with the remainder.
    """
    display_name = "Mission Count"
    range_start = 3
    default = 11
    range_end = 60

class LevelGradient(Range):
    """
    The amount of "variance" in % to have in the random level selection for the ranks/mission unlock methods.
    A lower value means as the levels are selected, you will, on average, need more and more cards.
    A higher value means much more randomness in the selection.
    """
    display_name = "Level Selection Variance"
    range_start = 0
    range_end = 100
    default = 30

class Traps(DefaultOnToggle):
    """
    Whether negative effects on the Neon White world are added to the item pool.
    === DOES NOT DO ANYTHING ATM ===
    """
    display_name = "Traps"

class Goal(Choice):
    """
    What the goal to complete should be.
    3bosses - Beat The Clocktower, The Third Temple, and Absolution with the highest medal selected.
    TrueEnding - Gather all memories and write Green into the Book of Life. (WILL FAIL TO GEN)
    """
    display_name = "Goal"
    option_3bosses = 1
    option_trueending = 2
    default = 1

class FillerWeights(ItemDict):
    """
    How often different types of filler should appear.
    "Generic" means to pick from a list of filler that don't do anything.
    Only filler items (+ Generic) can be listed here.
    """
    display_name = "Filler Weights"
    default = {
        "Generic": 10,
        "Health Card": 1,
        "Ammo Card": 1
    }

class DeathLinkAmnesty(Range):
    """
    How many deaths it takes to send a DeathLink.
    """
    display_name = "Death Link Amnesty"
    range_start = 1
    range_end = 30
    default = 1

class DeathLinkResets(Range):
    """
    How many **level resets** it takes to send a DeathLink.
    Setting to 0 disables sending them on resets.
    """
    display_name = "Level Reset Death Link Amnesty"
    range_start = 0
    range_end = 50
    default = 20


@dataclass
class NeonWhiteOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    difficulty_knowledge: KnowledgeDifficulty
    difficulty_execution: ExecutionDifficulty
    medal_select: MedalSelect
    gifts: Gifts
    sidequests: Sidequests
    unlock_method: MissionUnlockMethod
    card_types: CardTypes
    global_cards: GlobalCards
    total_ranks: TotalRanks
    ranks_required_percent: RanksRequiredPercentage
    mission_count: MissionCount
    level_gradient: LevelGradient
    starting_level_count: StartingLevelCount
    goal: Goal
    filler_weights: FillerWeights
    death_link: DeathLink
    death_link_amn: DeathLinkAmnesty
    death_link_res: DeathLinkResets
    bad_effects: Traps
    boof_shenanigans: BoofShenanigans
