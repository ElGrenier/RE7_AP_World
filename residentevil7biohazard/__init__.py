import re
import typing

from typing import Dict, Any, TextIO
from Utils import visualize_regions

from BaseClasses import ItemClassification, Item, Location, Region, CollectionState
from worlds.AutoWorld import World
from ..generic.Rules import set_rule
from Fill import fill_restrictive

from .Data import Data
from .Options import RE7Options
from .Exceptions import RE7ROptionError


Data.load_data()


def no_advancement_items(item):
    return not item.advancement

def chain_item_rule(location, new_rule): ### Permit stacking of rules instead of overwritting it
    old_rule = location.item_rule or (lambda item: True)
    location.item_rule = lambda item: old_rule(item) and new_rule(item)

def handle_coin_randomization(self, option, location, original_item):
    if option == 0:
        location.place_locked_item(self.create_item(original_item))
    elif option == 1:
        chain_item_rule(location, no_advancement_items)



class RE7Location(Location):
    def stack_names(*area_names):
        return " - ".join(area_names)
    
    def stack_names_not_victory(*area_names):
        if area_names[-1] == "Victory": return area_names[-1]

        return RE7Location.stack_names(*area_names)

    def is_item_forbidden(item, location_data, current_item_rule):
        return current_item_rule(item) and ('forbid_item' not in location_data or item.name not in location_data['forbid_item'])


class ResidentEvil7(World):
    """
    'Welcome to the Family Son.' - The Dad, probably
    """
    game: str = "Resident Evil 7"

    data_version = 2
    required_client_version = (0, 4, 4)
    apworld_release_version = "0.3.4" # defined to show in spoiler log

    item_id_to_name = { item['id']: item['name'] for item in Data.item_table }
    item_name_to_id = { item['name']: item['id'] for item in Data.item_table }
    item_name_to_item = { item['name']: item for item in Data.item_table }
    location_id_to_name = { loc['id']: RE7Location.stack_names(loc['region'], loc['name']) for loc in Data.location_table }
    location_name_to_id = { RE7Location.stack_names(loc['region'], loc['name']): loc['id'] for loc in Data.location_table }
    location_name_to_location = { RE7Location.stack_names(loc['region'], loc['name']): loc for loc in Data.location_table }
    source_locations = {} # this is used to seed the initial item pool from original items, and is indexed by player as lname:loc locations

    # de-dupe the item names for the item group name
    item_name_groups = { key: set(values) for key, values in Data.item_name_groups.items() }

    # keep track of the weapon randomizer settings for use in various steps and in slot data
    # disabling for now because it's ruining generations
    # replacement_weapons = {}
    # replacement_ammo = {}

    options_dataclass = RE7Options
    options: RE7Options

    def generate_early(self): # check weapon randomization before locations and items are processed, so we can swap non-randomized items as well
        # start with the normal locations per player for pool, then overwrite with weapon rando if needed
        self.source_locations[self.player] = self._get_locations() # id:loc combo
        self.source_locations[self.player] = { 
            RE7Location.stack_names(l['region'], l['name']): { **l, 'id': i } 
                for i, l in self.source_locations[self.player].items() 
        } # turn it into name:loc instead

    def create_regions(self): # and create locations
        scenario_locations = { l['id']: l for _, l in self.source_locations[self.player].items() }
        scenario_regions = self._get_region_table()

        regions = [
            Region(region['name'], self.player, self.multiworld) 
                for region in scenario_regions
        ]
        
        for region in regions:
            region.locations = [
                RE7Location(self.player, RE7Location.stack_names_not_victory(region.name, location['name']), location['id'], region) 
                    for _, location in scenario_locations.items() if location['region'] == region.name
            ]
            region_data = [scenario_region for scenario_region in scenario_regions if scenario_region['name'] == region.name][0]
            
            for location in region.locations:
                location_data = scenario_locations[location.address]
                
                # if location has an item that should be forced there, place that. for cases where the item to place differs from the original.
                if 'force_item' in location_data and location_data['force_item']:
                    location.place_locked_item(self.create_item(location_data['force_item']))
                # if location is marked not rando'd, place its original item. 
                # if/elif here allows force_item + randomized=0, since a forced item is technically not randomized, but don't need to trigger both.
                elif 'randomized' in location_data and location_data['randomized'] == 0:
                    location.place_locked_item(self.create_item(location_data["original_item"]))
                # if the coins are not randomized

                elif location_data.get("original_item") == "Antique Coin": # Manage Antique coins randomization
                    handle_coin_randomization(self,self.options.randomize_coins, location, "Antique Coin")

                elif self.options.start_at_chapter_2 and region_data["zone_id"] == 1: # Check if "start_at_chapter_2 option is activated"
                    location.place_locked_item(self.create_item(location_data["original_item"]))

                elif region_data["zone_id"] == 4 and "original_item" in location_data: # Manage Coins Cage Randomization
                    handle_coin_randomization(self, self.options.randomize_coins_cages, location, location_data["original_item"])


                if 'forbid_item' in location_data and location_data['forbid_item']:
                    current_item_rule = location.item_rule or None

                    if not current_item_rule:
                        current_item_rule = lambda x: True

                    location.item_rule = lambda item, loc_data=location_data, cur_rule=current_item_rule: RE7Location.is_item_forbidden(item, loc_data, cur_rule)

                # now, set rules for the location access
                if "condition" in location_data and "items" in location_data["condition"]:
                    set_rule(location, lambda state, loc=location, loc_data=location_data: self._has_items(state, loc_data["condition"].get("items", [])))

            self.multiworld.regions.append(region)
                
        for connect in self._get_region_connection_table():
            # skip connecting on a one-sided connection because this should not be reachable backwards (and should be reachable otherwise)
            if 'limitation' in connect and connect['limitation'] in ['ONE_SIDED_DOOR']:
                continue

            from_name = connect['from'] if 'Menu' not in connect['from'] else 'Menu'
            to_name = connect['to'] if 'Menu' not in connect['to'] else 'Menu'

            region_from = self.multiworld.get_region(from_name, self.player)
            region_to = self.multiworld.get_region(to_name, self.player)
            ent = region_from.connect(region_to)

            if "condition" in connect and "items" in connect["condition"]:
                set_rule(ent, lambda state, en=ent, conn=connect: self._has_items(state, conn["condition"].get("items", [])))

        # Uncomment the below to see a connection of the regions (and their locations).
        # visualize_regions(self.multiworld.get_region("Menu", self.player), "region_uml")

        # Place victory and set the completion condition for having victory
        self.multiworld.get_location("Victory", self.player) \
            .place_locked_item(self.create_item("Victory"))

        self.multiworld.completion_condition[self.player] = lambda state: self._has_items(state, ['Victory'])

    def create_items(self):
        scenario_locations = self.source_locations[self.player]

        pool = [
            self.create_item(item['name'] if item else None) for item in [
                self.item_name_to_item[location['original_item']] if location.get('original_item') else None
                    for _, location in scenario_locations.items()
            ]
        ]

        pool = [item for item in pool if item is not None] # some of the locations might not have an original item, so might not create an item for the pool

        # remove any already-placed source items from the pool (forced / vanilla-locked locations)
        #
        # Important: filled_location.item is a new Item object, so object identity does not
        # match the item object that was created for the pool. Also, force_item locations
        # still consume their original source item slot from the pool.
        for filled_location in self.multiworld.get_filled_locations(self.player):
            if filled_location.player != self.player:
                continue

            location_data = scenario_locations.get(filled_location.name)
            if not location_data and filled_location.address is not None:
                location_data = next(
                    (loc for loc in scenario_locations.values() if loc.get('id') == filled_location.address),
                    None
                )

            source_item_name = None
            if location_data:
                source_item_name = location_data.get('original_item')
            elif filled_location.item:
                source_item_name = filled_location.item.name

            if source_item_name:
                self._remove_one_pool_item_by_name(pool, source_item_name)

        # check the starting hip pouches option and add as precollected, removing from pool and replacing with junk
        # starting_hip_pouches = int(self.options.starting_hip_pouches)

        # if starting_hip_pouches > 0:
        #     hip_pouches = [item for item in pool if item.name == 'Hip Pouch'] # 6 total in every campaign, I think

        #     # if the hip pouches option exceeds the number of hip pouches in the pool, reduce it to the number in the pool
        #     if starting_hip_pouches > len(hip_pouches):
        #         starting_hip_pouches = len(hip_pouches)
        #         self.options.starting_hip_pouches.value = len(hip_pouches)

        #     for x in range(starting_hip_pouches):
        #         self.multiworld.push_precollected(hip_pouches[x]) # starting inv
        #         pool.remove(hip_pouches[x])

        # check the starting ink ribbons option and add as precollected, removing from pool and replacing with junk
        # starting_tape = int(self.options.starting_tape)

        # if self._format_option_text(self.options.difficulty) == 'Hardcore' and starting_tape > 0:
        #     ink_ribbons = [item for item in pool if item.name == 'Ink Ribbon'] # 12+ total in every campaign, I think

        #     # if the ink ribbons option exceeds the number of ink ribbons in the pool, reduce it to the number in the pool
        #     if starting_tape > len(ink_ribbons):
        #         starting_tape = len(ink_ribbons)
        #         self.options.starting_tape.value = len(ink_ribbons)

        #     for x in range(starting_tape):
        #         self.multiworld.push_precollected(ink_ribbons[x]) # starting inv
        #         pool.remove(ink_ribbons[x])

        # check the bonus start option and add some heal items and ammo packs as precollected / starting items
        if self._format_option_text(self.options.bonus_start) == 'True':
            count_spray = 3
            count_ammo = 4

            for x in range(count_spray): self.multiworld.push_precollected(self.create_item('First Aid Med'))

            for x in range(count_ammo): self.multiworld.push_precollected(self.create_item('Handgun Ammo'))

        # do all the "no X" options here so we have more empty spots to use for traps, if needed
        if self._format_option_text(self.options.no_first_aid_med) == 'True':
            pool = self._replace_pool_item_with(pool, 'First Aid Med', 'Ethan\'s Hand')

        if self._format_option_text(self.options.no_herb) == 'True':
            pool = self._replace_pool_item_with(pool, 'Herb', 'Ethan\'s Hand')

        if self._format_option_text(self.options.no_gunpowder) == 'True':
            pool = self._replace_pool_item_with(pool, 'Gunpowder', 'Ethan\'s Leg')
        
        # if self._format_option_text(self.options.no_gunpowder) == 'True':
        #     replaceables = set(item.name for item in pool if 'Gunpowder' in item.name)
        #     less_useful_items = set(
        #         item.name for item in pool 
        #             if 'Boards' in item.name or 'Cassette' in item.name or ('Film' in item.name and 'Hiding Place' not in item.name) or item.name == 'Blue Herb'
        #     )

            # for from_item in replaceables:
            #     to_item = self.random.choice(list(less_useful_items))
            #     pool = self._replace_pool_item_with(pool, from_item, to_item)

        # figure out which traps are enabled, then swap them in for low-priority items
        # do this before the "oops all X" options so we can make use of extra Handgun Ammo spots before they get replaced out
        # traps = []

        # if self._format_option_text(self.options.add_damage_traps) == 'True':
        #     for x in range(int(self.options.damage_trap_count)):
        #         traps.append(self.create_item("Damage Trap"))

        # if len(traps) > 0:
        #     # use these spots for replacement first, since they're entirely non-essential
        #     available_spots = [
        #         item for item in pool 
        #             if 'Boards' in item.name or 'Cassette' in item.name or ('Film' in item.name and 'Hiding Place' not in item.name)
        #     ]
        #     self.random.shuffle(available_spots)

        #     # use these spots for replacement next, since they're lower priority but we don't want to use as many of them
        #     # for gunpowder, only target the small / normal gunpowders
        #     extra_spots = [
        #         item for item in pool 
        #             if 'Handgun Ammo' in item.name or item.name == 'Gunpowder'
        #     ]
        #     self.random.shuffle(extra_spots)
               
        #     for spot in available_spots:
        #         if len(traps) == 0: break

        #         trap_to_place = traps.pop()
        #         pool.remove(spot)
        #         pool.append(trap_to_place)
                
        #     for spot in extra_spots:
        #         if len(traps) == 0: break

        #         trap_to_place = traps.pop()
        #         pool.remove(spot)
        #         pool.append(trap_to_place)

        # add extras for Clock Tower items or Medallions, if configured
        # doing this before "oops all X" to make use of extra Handgun Ammo spots, too
        # if self._format_option_text(self.options.extra_clock_tower_items) == 'True':
        #     replaceables = [item for item in pool if 'Boards' in item.name or item.name == 'Handgun Ammo' or item.name == 'Large-Caliber Handgun Ammo']
            
        #     for x in range(3):
        #         pool.remove(replaceables[x])

        #     pool.append(self.create_item('Mechanic Jack Handle'))
        #     pool.append(self.create_item('Small Gear'))
        #     pool.append(self.create_item('Large Gear'))

        # if self._format_option_text(self.options.extra_medallions) == 'True':
        #     replaceables = [item for item in pool if 'Boards' in item.name or item.name == 'Handgun Ammo' or item.name == 'Large-Caliber Handgun Ammo']
            
        #     for x in range(2):
        #         pool.remove(replaceables[x])

        #     pool.append(self.create_item('Lion Medallion'))
        #     pool.append(self.create_item('Unicorn Medallion'))

        #     # The A scenarios have Maiden forced to the Bolt Cutters vanilla location, which is guaranteed to be accessible.
        #     # B scenarios have it randomized, so add a second randomized Maiden.
        #     if self._get_scenario().lower() == 'b':
        #         pool.remove(replaceables[2]) # remove the 3rd item to make room for a 3rd medallion
        #         pool.append(self.create_item('Maiden Medallion'))

        # if self._format_option_text(self.options.early_medallions) == 'True':
        #     medallions = {i.name: len([i2 for i2 in pool if i2.name == i.name]) for i in pool if i.name in ['Lion Medallion', 'Unicorn Medallion', 'Maiden Medallion']}

        #     for item_name, item_qty in medallions.items():
        #         if item_qty > 0:
        #             self.multiworld.early_items[self.player][item_name] = item_qty
   

        # check the "Oops! All ____" option. From the option description:
        #     Enabling this swaps weapons, weapon ammo, subweapons, crafting supplies,
        #     and upgrades to the selected weapon. Progression / key / gating items are
        #     intentionally left alone, matching the safer RE3-style behavior.
        oops_all_flag = self._get_oops_all_options_flag()
        if oops_all_flag:
            oops_items_map = {
                0x01: 'Chain Saw',
                0x02: 'M19 Handgun',
                0x04: 'Grenade Launcher',
                0x08: 'Knife'
            }

            if oops_all_flag not in oops_items_map:
                raise RE7ROptionError("Cannot apply multiple 'Oops All' options. Please fix your yaml")

            oops_replace_types = {'Weapon', 'Ammo', 'Subweapon', 'Consumable', 'Upgrade'}
            items_to_replace = [
                item for item in self.item_name_to_item.values()
                if item.get('type') in oops_replace_types
                and not item.get('progression', False)
            ]

            for from_item in items_to_replace:
                pool = self._replace_pool_item_with(pool, from_item['name'], oops_items_map[oops_all_flag])


        # if the number of unfilled locations exceeds the count of the pool, fill the remainder of the pool with extra maybe helpful items
        missing_item_count = len(self.multiworld.get_unfilled_locations(self.player)) - len(pool)

        if missing_item_count > 0:
            for x in range(missing_item_count):
                pool.append(self.create_item('Herb'))

        # Make any items that result in a really quick BK either early or local items, so the BK time is reduced
        early_items = {}       

        for item_name, item_qty in early_items.items():
            if item_qty > 0:
                self.multiworld.early_items[self.player][item_name] = item_qty

        local_items = {}       
        #local_items["Fuse - Main Hall"] = len([i for i in pool if i.name == "Fuse - Main Hall"])

        for item_name, item_qty in local_items.items():
            if item_qty > 0:
                self.options.local_items.value.add(item_name)

        # Match the pool to the currently unfilled location count.
        # This mirrors the RE3 safety trim and prevents option combinations from
        # leaving extra filler/useful items in the pool.
        extra_items = len(pool) - len(self.multiworld.get_unfilled_locations(self.player))

        for _ in range(extra_items):
            eligible_items = [
                item for item in pool
                if item.classification in (ItemClassification.filler, ItemClassification.useful)
            ]

            if not eligible_items:
                break

            pool.remove(eligible_items[0])

        self.multiworld.itempool += pool
            
    # def pre_fill(self):
    #     # Item plando runs after create_items. If plando fills RE7 locations, the
    #     # original item for each plando-filled location is still sitting in the pool.
    #     # Trim non-progression items here so fill sees the same number of items as
    #     # unfilled locations.
    #     player_pool = [item for item in self.multiworld.itempool if item.player == self.player]
    #     extra_items = len(player_pool) - len(self.multiworld.get_unfilled_locations(self.player))

    #     for _ in range(extra_items):
    #         eligible_items = [
    #             item for item in self.multiworld.itempool
    #             if item.player == self.player
    #             and item.classification in (ItemClassification.filler, ItemClassification.useful)
    #         ]

    #         if not eligible_items:
    #             break

    #         self.multiworld.itempool.remove(eligible_items[0])

    def _remove_one_pool_item_by_name(self, pool, item_name: str) -> bool:
        for item in list(pool):
            if item.name == item_name:
                pool.remove(item)
                return True

        return False

    def create_item(self, item_name: str) -> Item:
        if not item_name: return

        item = self.item_name_to_item[item_name]

        if item.get('progression', False):
            classification = ItemClassification.progression
        elif item.get('type', None) not in ['Lore']:
            classification = ItemClassification.useful
        else: # it's Lore
            classification = ItemClassification.filler

        new_item = Item(item['name'], classification, item['id'], player=self.player)
        return new_item

    def get_filler_item_name(self) -> str:
        return "Hands"

    def fill_slot_data(self) -> Dict[str, Any]:
        slot_data = {
            "apworld_version": self.apworld_release_version,
            "difficulty": self._get_difficulty(),
            "unlocked_typewriters": self._format_option_text(self.options.unlocked_typewriters).split(", "),
            "ammo_pack_modifier": self._format_option_text(self.options.ammo_pack_modifier),
            "death_link": self._format_option_text(self.options.death_link) == 'Yes' # why is this yes? lol Edit : NO IDEA
        }

        return slot_data
    
    def write_spoiler_header(self, spoiler_handle: TextIO):
        spoiler_handle.write(f"RE7_AP_World version: {self.apworld_release_version}\n")

    def _has_items(self, state: CollectionState, item_names: list) -> bool:
        # if there are no item requirements, this location is open, they "have the items needed"
        if len(item_names) == 0:
            return True

        # if the requirements are a single set of items, make it a list of a single set of items to support looping for multiple sets (below)
        if len(item_names) > 0 and type(item_names[0]) is not list:
            item_names = [item_names]

        for set_of_requirements in item_names:
            # if it requires all unique items, just do a state has all
            if len(set(set_of_requirements)) == len(set_of_requirements):
                if state.has_all(set_of_requirements, self.player):
                    return True
            # else, it requires some duplicates, so let's group them up and do some has w/ counts
            else:
                item_counts = {
                    item_name: len([i for i in set_of_requirements if i == item_name]) for item_name in set_of_requirements # e.g., { Spare Key: 2 }
                }
                missing_an_item = False

                for item_name, count in item_counts.items():
                    if not state.has(item_name, self.player, count):
                        missing_an_item = True

                if missing_an_item:
                    continue # didn't meet these requirements, so skip to the next set, if any
                
                # if we made it here, state has all the items and the quantities needed, return True
                return True

        # if we made it here, state didn't have enough to return True, so return False
        return False

    def _format_option_text(self, option) -> str:
        return re.sub(r'\w+\(', '', str(option)).rstrip(')')
    
    def _get_locations(self) -> dict:
        valid_region_names = {region['name'] for region in self._get_region_table()}
        locations_pool = {
            loc['id']: loc for _, loc in self.location_name_to_location.items()
            if loc.get('region') in valid_region_names
        }

        # if the player chose hardcore, take out any matching standard difficulty locations
        if self._format_option_text(self.options.difficulty) == 'Hardcore':
            for hardcore_loc in [loc for loc in locations_pool.values() if loc['difficulty'] == 'hardcore']:
                check_loc_region = re.sub(r'H\)$', ')', hardcore_loc['region']) # take the Hardcore off the region name
                check_loc_name = hardcore_loc['name']

                # if there's a standard location with matching name and region, it's obsoleted in hardcore, remove it
                standard_locs = [id for id, loc in locations_pool.items() if loc['region'] == check_loc_region and loc['name'] == check_loc_name and loc['difficulty'] != 'hardcore']

                if len(standard_locs) > 0:
                    del locations_pool[standard_locs[0]]

        # Hardcore locations temporarily disabled until Madhouse support is implemented
        locations_pool = {
            id: loc for id, loc in locations_pool.items() if loc['difficulty'] != 'hardcore'
        }

        # now that we've factored in hardcore swaps, remove any hardcore locations that were just there for removing unused standard ones
        locations_pool = { id: loc for id, loc in locations_pool.items() if 'remove' not in loc }
        
        return locations_pool

    def _get_region_table(self) -> list:
        return [
            region for region in Data.region_table 
        ]
    
    def _get_region_connection_table(self) -> list:
        return [
            conn for conn in Data.region_connections_table
        ]
    
    def _get_difficulty(self) -> str:
        return self._format_option_text(self.options.difficulty).lower()
    
    def _replace_pool_item_with(self, pool, from_item_name, to_item_name) -> list:
        items_to_remove = [item for item in pool if item.name == from_item_name]
        count_of_new_items = len(items_to_remove)

        for item in items_to_remove:
            pool.remove(item)

        for x in range(count_of_new_items):
            pool.append(self.create_item(to_item_name))

        return pool

    def _get_oops_all_options_flag(self) -> int:
        flag = 0
        if self._format_option_text(self.options.oops_all_chainsaw) == 'True':
            flag |= 0x01
        if self._format_option_text(self.options.oops_all_handgun) == 'True':
            flag |= 0x02
        if self._format_option_text(self.options.oops_all_grenade_launcher) == 'True':
            flag |= 0x04
        if self._format_option_text(self.options.oops_all_knives) == 'True':
            flag |= 0x08
        return flag
       
    # def _output_items_and_locations_as_text(self):
    #     my_locations = [
    #         {
    #             'id': loc.address,
    #             'name': loc.name,
    #             'original_item': self.location_name_to_location[loc.name]['original_item'] if loc.name != "Victory" else "(Game Complete)"
    #         } for loc in self.multiworld.get_locations() if loc.player == self.player
    #     ]

    #     my_locations = set([
    #         "{} | {} | {}".format(loc['id'], loc['name'], loc['original_item'])
    #         for loc in my_locations
    #     ])
        
    #     my_items = [
    #         {
    #             'id': item.code,
    #             'name': item.name
    #         } for item in self.multiworld.get_items() if item.player == self.player
    #     ]

    #     my_items = set([
    #         "{} | {}".format(item['id'], item['name'])
    #         for item in my_items
    #     ])

    #     print("\n".join(sorted(my_locations)))
    #     print("\n".join(sorted(my_items)))

    #     raise BaseException("Done with debug output.")