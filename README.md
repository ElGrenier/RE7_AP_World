# RE7 Archipelago World
An Archipelago (AP) randomizer world for Resident Evil 7 Biohazard. Designed for use with the RE7 Archipelago client repository linked below.

## How to generate and play an RE7 randomized world
Follow the visual setup guide here: 

https://elgrenier.github.io/RE7_AP_SetupGuide/

## How is the  data structured?
All of the data lives in the `data` folder. The structure of the data is:

- [Locations file](#locations-file)
- [Locations (Hardcore) file](#locations-hardcore-file)
- [Regions file](#regions-file)
- [Region Connections file](#region-connections-file)
- [Typewriter List file](#typewriter-list-file)
- [Item List file](#item-list-file)
- [Region Zones file](#region-zones-file)

---
#### Item Type
There are multiple item types to choose from:

- Key = These are high-priority gating items that unlock major progression
- Gating = These are low-priority gating items that unlock only a few locations
- Consumable = These are non-progression but likely useful items that are consumed on use
- Recovery = These are the same as Consumable, but further categorized as healing items
- Weapon = These are weapons that consume ammunition (so the Combat Knife is not included)
- Subweapon = These are weapons that do not consume ammunition, and many of these are throwable
- Ammo = These are all the ammo types for use with the Weapon item type
- Upgrade = These are all the weapon upgrades for use with the Weapon item type, it is also used for player upgrade (like Steroid or Stabilizer)
- Lore = These are all non-progression, non-useful items that are classified as filler

##### Decimal
The decimal field is a decimal (base 10) representation of the item's in-game hex code. This is how the randomizer client translates a named item to an in-game item.

##### Count
The count field represents the quantity you receive each time the item is received, NOT the number of this item. In most cases, the count will be 1. For Weapons, the count is the starting ammo count for that weapon when received. For Ammo, the count is the amount of ammo received when you receive that "pack" of ammo.

##### Progression
If an item is marked as progression, it unlocks one or more locations. Typically, this will only be the case for the item types Key and Gating.

---

#### Region Zones file
Regions represent rooms, so zones represent groups of rooms, like RPD.

---

### Locations file
This is the most important part of the randomizer world. The locations and original items defined here directly impact what is randomized into the world, and the item object information is used by the randomizer client to track those location checks.

Some important fields to note:

##### Name and Region
These are combined with the location name. The region name must match a region name in the Regions file.

##### Original Item
This is the item that is found at the location when playing through the vanilla game. When the apworld is generated, this item is added to the item pool for randomization.

##### Condition
This allows conditional logic for whether a location should be accessible. For instance, ...

##### Item Object, Parent Object, and Folder Path
These three fields uniquely identify every location in the game. They are derived from game object names and field values from the game's code. Using these values, the randomizer client can identify the right named location to track.

To find these values, you can use [REF_Inspect](https://github.com/FuzzyGamesOn/REF_Inspect) and interact with the locations normally.

##### Force Item
This is an optional field and only included on some item entries. In some cases, we want to force a specific item to be placed at a specific location, so we use this option and provide the name of the item to place.

##### Randomized
This is an optional field and only included on some item entries. In some cases, we want the location to keep its vanilla item, so we use this option. This option defaults to 1 (randomized), and 0 means not randomized.

##### ID and Victory
There must be exactly one Victory location (i.e., location that finishes the randomizer), and it is the only location that uses these fields. All location IDs are dynamically assigned unless provided, but Victory forces a non-dynamic ID. The Victory field is set to true to indicate that the location is the Victory location.

---

#### Locations (Hardcore) file
This file is optional, but needed for Hardcore difficulty supports. The only difference between Hardcore difficulty and other difficulties is the placement of ... , both in locations that are used by other difficulties and in new locations.

This file only contains locations that are changed/added for Hardcore, and is loaded after the normal locations file. If a location in the Hardcore file has the same region name and location name as a location in the normal file, the location in the normal file will be overwritten when playing Hardcore difficulty. If the location in the Hardcore file has a region + location name that doesn't match an existing location, it will be added as a new location when playing Hardcore difficulty.

---

#### Regions file
This file lists all of the rooms (regions) in the game and what zone (area) they belong to. This file must always start with the Menu region.

---

#### Region Connections file
This file dictates how the randomizer connects each room (region) together. Currently, these connections must follow their vanilla connection and item requirements.

Some important fields to note:

##### From and To
Each of these must be set to a region name from the regions file. These define a forward connection *from* the From region *to* the To region. 

**Note: Since you can travel back along any connection you've previously traveled forward over, don't define two-way connections between regions. This will likely break logic because the logic will sometimes use the reverse connection to avoid the vanilla connection mentioned above.**

##### Condition
Similar to the Condition field in the regions file, this allows you to specify item requirements to traverse a region connection. This is the most common place to use the Condition field, for things like door keys, etc.

You will also notice that some major region connections (like going to ... ) include more items that are actually required to enter the connection. This forces the logic to provide the extra items before considering this connection to be in logic. (e.g., ... )

##### Limitation
This is an optional field, and is currently only used to define a region connection as a one-sided connection (with the value "ONE_SIDED_DOOR"). This is commonly used for doors with latches or bolt cutter doors that you have to activate from one side to allow traversing.

**Note: One-sided connections are currently excluded from the randomizer because they may end up in logic on the reverse path, which can be unreachable. Similar issue as noted above with From and To. However, we want these defined in case we change this behavior later.**

---

#### Typewriter List file
This file defines all of the typewriter locations. This is used for creating typewriter teleports in the randomizer client.

Some important fields to note:

##### Location ID, Map ID, and Item Object
These fields all uniquely identify a typewriter by field values and game object names from the game's code.

To find these values, you can use [REF_Inspect](https://github.com/FuzzyGamesOn/REF_Inspect) and interact with the typewriters normally.

##### Player Position
This field specifies the x/y/z (Vector3) location that the player should be teleported to when using the typewriter. Typically, you'd want this to be fairly close to the typewriter, or at least nearby in the same room.

To find a usable value for this, you can use [REF_Inspect](https://github.com/FuzzyGamesOn/REF_Inspect) and interact with the typewriters normally.
