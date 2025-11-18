import json
import os
import pkgutil

# blatantly copied from the minecraft ap world because why not (and from the RE2R Ap world too)
def load_data_file(*args) -> dict:
    data_directory = "data"
    fname = os.path.join(data_directory, *args)

    try:
        filedata = json.loads(pkgutil.get_data(__name__, fname).decode())
    except:
        filedata = []

    return filedata

class Data:
    item_table = []
    location_table = []
    region_table = []
    region_connections_table = []

    item_name_groups = {}

    def load_data():
        #hardcore_offset = 400 # put all hardcore-only locations in the last 100 location spots for each scenario
        #scenario_suffix_hardcore = ' ({}{}H)' # makes hardcore location variations unique

        location_start = item_start = 3000000000

        ###
        # Add standard regions
        ###

        new_region_table = load_data_file('regions.json')
        Data.region_table.extend([
            {
                **reg,
                'name': reg['name'] if reg['name'] != 'Menu' else reg['name'], # add the scenario abbreviation so they're unique
            }
            for reg in new_region_table
        ])

        ###
        # Add hardcore regions, if applicable
        ###

        hardcore_locations_table = load_data_file('locations_hardcore.json')
        hardcore_regions = set([loc['region'] for loc in hardcore_locations_table])

        if len(hardcore_regions) > 0:
            Data.region_table.extend([
                {
                    'name': reg, # add the scenario abbreviation so they're unique
                    'zone_id': [regular['zone_id'] for regular in new_region_table if regular['name'] == reg][0]
                }
                for reg in hardcore_regions # instead of using region definitions, we're using the hardcore region additions from the locations themselves
            ])

        ###
        # Add standard region connections
        ###

        added_connections = []
        new_region_connections_table = load_data_file('region_connections.json')

        for conn in new_region_connections_table:
            connection_path = f"{conn['from']} to {conn['to']}"

            if connection_path in added_connections:
                continue

            added_connections.append(connection_path)

            Data.region_connections_table.append(
                {
                    **conn,
                    'from': conn['from'] if conn['from'] != 'Menu' else conn['from'], # add the scenario abbreviation so they're unique
                    'to': conn['to'] if conn['to'] != 'Menu' else conn['to'], # add the scenario abbreviation so they're unique
                }
            )

        ###
        # Add hardcore region connections
        ###

        # not a typo. if we loaded hardcore regions, we need to generate hardcore region connections as well
        # if len(hardcore_regions) > 0:
        #     for conn in new_region_connections_table:
        #         if conn['from'] in hardcore_regions or conn['to'] in hardcore_regions:
        #             # suffix_from = scenario_suffix_hardcore if conn['from'] in hardcore_regions else scenario_suffix
        #             # suffix_to = scenario_suffix_hardcore if conn['to'] in hardcore_regions else scenario_suffix

        #             connection_from_name = conn['from']
        #             connection_to_name = conn['to']
        #             connection_path = f"{connection_from_name} to {connection_to_name}"

        #             if connection_path in added_connections:
        #                 continue

        #             added_connections.append(connection_path)

        #             new_region_connection = {
        #                 **conn,
        #                 'from': connection_from_name, 
        #                 'to': connection_to_name, 
        #             }

        #             Data.region_connections_table.append(new_region_connection)

        ###
        # Add item table for all difficulties
        ###
        
        new_item_table = load_data_file('items.json')
        Data.item_table.extend([
            { 
                **item, 
                'id': item['id'] if item.get('id') else item_start + key
            } 
            for key, item in enumerate(new_item_table)
        ])

        # For the items that have groups, add them to the item group names
        new_items_with_groups = [item for _, item in enumerate(new_item_table) if "groups" in item.keys()]

        for item_with_group in new_items_with_groups:
            item_name = item_with_group["name"]
            group_names = item_with_group["groups"]

            for group_name in group_names:
                if group_name not in Data.item_name_groups.keys():
                    Data.item_name_groups[group_name] = []

                Data.item_name_groups[group_name].append(item_name)

        ###
        # Add standard location table
        ###

        new_location_table = load_data_file('locations.json')
        Data.location_table.extend([
            { 
                **loc, 
                'id': loc['id'] if loc.get('id') else location_start + key,
                'region': loc['region'], # add the scenario abbreviation so they're unique
                'difficulty': None
            }
            for key, loc in enumerate(new_location_table)
        ])

        ###
        # Add hardcore locations
        ###

        hardcore_location_table = load_data_file('locations_hardcore.json')

        if len(hardcore_location_table) > 0:
            Data.location_table.extend([
                { 
                    **loc, 
                    'id': loc['id'] if loc.get('id') else location_start + key,
                    'region': loc['region'] , # add the scenario abbreviation so they're unique
                    'difficulty': 'hardcore'
                }
                for key, loc in enumerate(hardcore_location_table)
            ])