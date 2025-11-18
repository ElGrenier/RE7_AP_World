from dataclasses import dataclass
from Options import (Choice, OptionList, NamedRange, 
    StartInventoryPool,
    PerGameCommonOptions, DeathLinkMixin)

class Difficulty(Choice):
    """Standard: Most people should play on this.
    Hardcore: Good luck, and thanks for testing deaths. Kappa
    Assisted: ... Okay, fine. No judgment here. :)"""
    display_name = "Difficulty to Play On"
    option_standard = 0
    option_hardcore = 1
    option_assisted = 2
    default = 0

class UnlockedTypewriters(OptionList):
    """Specify the exact name of typewriters from the warp buttons in-game, as a YAML array.
    """
    display_name = "Unlocked Typewriters"

# class StartingHipPouches(NamedRange):
#     """The number of hip pouches you want to start the game with, to a max of 6 (or 5 for Hardcore). 
#     Any that you start with are taken out of the item pool and replaced with junk."""
#     default = 0
#     range_start = 0
#     range_end = 6
#     display_name = "Starting Hip Pouches"
#     special_range_names = {
#         "disabled": 0,
#         "half": 3,
#         "all": 6
#     }

class StartingTape(NamedRange):
    """If playing Hardcore, the number of Tape you want to start the game with, to a max of 12.
    Any that you start with are taken out of the item pool and replaced with junk."""
    default = 0
    range_start = 0
    range_end = 12
    display_name = "Starting Tape"
    special_range_names = {
        "disabled": 0,
        "half": 6,
        "all": 12
    }

class BonusStart(Choice):
    """Some players might want to start with a little help in the way of a few extra heal items and packs of ammo.

    False: (Default) Normal, don't start with extra heal items and packs of ammo.
    True: Start with those helper items."""
    display_name = "Bonus Start"
    option_false = 0
    option_true = 1
    default = 0

class StartAtChapter2(Choice):
    """With this, the first chapter is not randomized, so you will start "directly" to chapter 2 (just interact with the door bell at the start to start Chapter 2)

    False: (Default) Normal, you start the game as normal
    True: The first chapter is not randomized."""
    display_name = "Bonus Start"
    option_false = 0
    option_true = 1
    default = 0


class AllowMissableLocations(Choice):
    """Accidentally skipping item locations early can lead to softlocking as certain story triggers make it impossible to backtrack. 
    This option seeks to avoid that by limiting item placements.

    False: (Default) Will place items so they are not permanently missable.
    This severely limits where progression can be to prevent softlocking of any kind. 
    Will also remove progression for others if multiworld.
    
    True: Progression can be placed in locations that can be missed if story progresses too far, you've been warned.

    NOTE - This option only affects *YOUR* game. Your progression can still be in someone else's if they have this option enabled."""
    display_name = "Allow Missable Locations"
    option_false = 0
    option_true = 1
    default = 0

class RandomizeCoins(Choice):
    """This option permit you to choose how you Randomize Antique Coins (but not what is unlocked with it)
    None: (Default) Won't Randomize Antique Coins
    This will make you able to find coins as default, and make that no item will be behind Coinss
    
    No_progression: The coins will be randomized but won't contains Progression items.

    All : The coins will be randomized, and can contains anything.

    NOTE - This option only affects *YOUR* game. Your progression can still be in someone else's if they have this option enabled."""
    display_name = "Randomized Coins"
    option_none = 0
    option_no_progression = 1
    option_all = 2
    default = 0

class RandomizeCoinsCages(Choice):
    """This option permit you to choose how you Randomize Coins Cages (Not Coins see randomize_coins for that)
    None: (Default) Won't Randomize Randomize Coins Cages
    The content of coins cage will be as default
    
    No_progression: The coins cage will be randomized but won't contains Progression items.

    All : The coins cage will be randomized, and can contains anything.

    NOTE - This option only affects *YOUR* game. Your progression can still be in someone else's if they have this option enabled."""
    display_name = "Randomized Coins"
    option_none = 0
    option_no_progression = 1
    option_all = 2
    default = 0


# class ExtraClockTowerItems(Choice):
#     """The gears and jack handle required for Clock Tower can leave players BK for a while. 
#     This option adds an extra set of these items so the odds of BK are lower.

#     False: Normal, only 1 of each gear and the jack handle in the item pool.
#     True: Now, 2 of each gear and 2 jack handles in the item pool."""
#     display_name = "Extra Clock Tower Items"
#     option_false = 0
#     option_true = 1
#     default = 1

# class ExtraMedallions(Choice):
#     """On your first visit to RPD, the medallions are required to leave. 
#     If you spend too long waiting for these on average, this option will add extras of 2 medallions.

#     False: Normal, only 1 of each RPD medallion in the item pool.
#     True: Now, A scenarios will have 2 extra medallions (since Maiden is always at Fire Escape). 
#           B scenarios will have 3 extra medallions since all are randomized."""
#     display_name = "Extra Medallions"
#     option_false = 0
#     option_true = 1
#     default = 1

# class EarlyMedallions(Choice):
#     """If you find yourself in BK a lot waiting on medallions to leave RPD, this option could be for you!

#     This option will mark your RPD medallions as "early" items, meaning they will show up in the 1st sphere of someone's playthrough.
#     Also, if you combine this early option with the extra option above, at least some of those extra medallions will *also* be in the 1st sphere.

#     False: Normal, you get your medallions when you get them. Could be a while.
#     True: Now, your medallions will likely all show up before you complete RPD 1's location checks."""
#     display_name = "Early Medallions"
#     option_false = 0
#     option_true = 1
#     default = 0


class AmmoPackModifier(Choice):
    """This option, when set, will modify the quantity of ammo in each ammo pack. This can make the game easier or much, much harder.
    The available options are:

    None: You realized that consistency in ammo pack quantities is one of the few true joys in life, and this causes you to not modify them at all.
    Max: Each ammo pack will contain the maximum amount of ammo that the game allows. (i.e., you will never, ever run out of ammo.)
    Double: Each ammo pack will contain twice as much ammo as it normally contains.
    Half: Each ammo pack will contain half as much ammo as it normally contains.
    Only Three: Each ammo pack will have an ammo count of 3.
    Only Two: Each ammo pack will have an ammo count of 2.
    Only One: Each ammo pack will have an ammo count of 1. (Yes, your Handgun Ammo pack will have a single bullet in it.)
    Random By Type: Each ammo type's ammo pack will have a random quantity of ammo, and you will get that same quantity of ammo from every pack for that ammo type.
        (For example, you receive a Shotgun Shells pack that has a random quantity of 7 ammo. All Shotgun Shells packs will have a quantity of 7.)
    Random Always: Each ammo pack will have a random quantity of ammo, and that quantity will be randomized every time.
        (For example, you receive a Shotgun Shells pack that has a random quantity of 7 ammo. Your next Shotgun Shells pack has a quantity of 4, next has 2, etc.)

    NOTE: The options for "Only Three", "Only Two", "Only One", "Random By Type", and "Random Always" are not guaranteed to be reasonably beatable."""
    display_name = "Ammo Pack Modifier"
    option_none = 0
    option_max = 1
    option_double = 2
    option_half = 3
    option_only_three = 4
    option_only_two = 5
    option_only_one = 6
    option_random_by_type = 7
    option_random_always = 8

class OopsAllChainsaw(Choice):
    """Enabling this swaps all weapons, weapon ammo, and subweapons to Chainsaws. 
    (Except progression weapons, of course.)"""
    display_name = "Oops! All Chainsaws"
    option_false = 0
    option_true = 1
    default = 0

class OopsAlHandgun(Choice):
    """Enabling this swaps all weapons, weapon ammo, and subweapons to Handgun. 
    (Except progression weapons, of course.)"""
    display_name = "Oops! All Handgun"
    option_false = 0
    option_true = 1
    default = 0

class OopsAllGrenadeLauncher(Choice):
    """Enabling this swaps all weapons, weapon ammo, and subweapons to GrenadeLauncher. 
    (Except progression weapons, of course.)"""
    display_name = "Oops! All Grenades"
    option_false = 0
    option_true = 1
    default = 0

class OopsAllKnives(Choice):
    """Enabling this swaps all weapons, weapon ammo, and subweapons to Knives. 
    (Except progression weapons, of course.)"""
    display_name = "Oops! All Knives"
    option_false = 0
    option_true = 1
    default = 0


class NoFirstAidMed(Choice):
    """Enabling this swaps all first aid Meds to filler or less useful items. 
    """
    display_name = "No First Aid Spray"
    option_false = 0
    option_true = 1
    default = 0

class NoHerb(Choice):
    """Enabling this swaps all herbs to filler or less useful items. 
    """
    display_name = "No Herbs"
    option_false = 0
    option_true = 1
    default = 0

class NoGunpowder(Choice):
    """Enabling this swaps all gunpowder of all types to filler or less useful items. 
    """
    display_name = "No Gunpowder"
    option_false = 0
    option_true = 1
    default = 0


# making this mixin so we can keep actual game options separate from AP core options that we want enabled
# not sure why this isn't a mixin in core atm, anyways
@dataclass
class StartInventoryFromPoolMixin:
    start_inventory_from_pool: StartInventoryPool

@dataclass
class RE7Options(StartInventoryFromPoolMixin, DeathLinkMixin, PerGameCommonOptions):
    difficulty: Difficulty
    unlocked_typewriters: UnlockedTypewriters
    # starting_hip_pouches: StartingHipPouches
    starting_tape: StartingTape
    bonus_start: BonusStart
    start_at_chapter_2: StartAtChapter2
    randomize_coins: RandomizeCoins
    randomize_coins_cages: RandomizeCoinsCages

    # allow_progression_in_labs: AllowProgressionInLabs
    ammo_pack_modifier: AmmoPackModifier
    oops_all_chainsaw: OopsAllChainsaw
    oops_all_handgun: OopsAlHandgun
    oops_all_grenade_launcher: OopsAllGrenadeLauncher
    oops_all_knives: OopsAllKnives
    no_first_aid_med: NoFirstAidMed
    no_herb: NoHerb
    no_gunpowder: NoGunpowder