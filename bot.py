import random
import math

from battlecode25.stubs import *

# This is an example bot written by the developers!
# Use this to help write your own code, or run it against your bot to see how well you can do!


# Globals
turn_count = 0
directions = [
    Direction.NORTH,
    Direction.NORTHEAST,
    Direction.EAST,
    Direction.SOUTHEAST,
    Direction.SOUTH,
    Direction.SOUTHWEST,
    Direction.WEST,
    Direction.NORTHWEST,
]

def max(i1: int, i2: int):
    if i1 > i2:
        return i1
    else:
        return i2

def turn():
    """
    MUST be defined for robot to run
    This function will be called at the beginning of every turn and should contain the bulk of your robot commands
    """
    global turn_count
    turn_count += 1

    if get_type() == UnitType.SOLDIER:
        run_soldier()
    elif get_type() == UnitType.MOPPER:
        run_mopper()
    elif get_type() == UnitType.SPLASHER:
        run_splasher()
    elif get_type().is_tower_type():
        run_tower()
    else:
        pass  # Other robot types?


def run_tower():
    if turn_count % 100 == 50 and get_round_num() < 500 and get_type() == UnitType.LEVEL_ONE_MONEY_TOWER:
        disintegrate()
        log(f"Disintegrate tower at ({get_location().x}, {get_location().y})")

    # Pick a direction to build in.
    dir = directions[random.randint(0, len(directions) - 1)]
    next_loc = get_location().add(dir)

    # Pick a random robot type to build.
    robot_type = random.randint(0, max(15 - get_num_towers(), 7))
    if 0 <= robot_type <= 3 and can_build_robot(UnitType.SOLDIER, next_loc):
        build_robot(UnitType.SOLDIER, next_loc)
        log("BUILT A SOLDIER")
    if robot_type == 4 and get_round_num() > 500 and can_build_robot(UnitType.MOPPER, next_loc):
        build_robot(UnitType.MOPPER, next_loc)
        log("BUILT A MOPPER")
    if 4 < robot_type <= 7 and get_round_num() > 500 and can_build_robot(UnitType.SPLASHER, next_loc):
        build_robot(UnitType.SPLASHER, next_loc)
        log("BUILT A SPLASHER")

    # Read incoming messages
    messages = read_messages()
    for m in messages:
        log(f"Tower received message: '#{m.get_sender_id()}: {m.get_bytes()}'")

    # TODO: can we attack other bots?


def run_soldier():
    # Sense information about all visible nearby tiles.
    nearby_tiles = sense_nearby_map_infos()

    # Search for a nearby ruin to complete.
    cur_ruin = None
    min_dist = -1
    for tile in nearby_tiles:
        if not tile.has_ruin():
            continue
        dist = get_location().distance_squared_to(tile.get_map_location())
        if cur_ruin == None or min_dist > dist:
            cur_ruin = tile
            min_dist = dist

    if cur_ruin is not None:
        target_loc = cur_ruin.get_map_location()
        # log(f"Detect ruin at: ({target_loc.x}, {target_loc.y})")
        dir = get_location().direction_to(target_loc)
        if can_move(dir):
            move(dir)

        # Mark the pattern we need to draw to build a tower here if we haven't already.
        should_mark = cur_ruin.get_map_location().subtract(dir)
        if sense_map_info(should_mark).get_mark() == PaintType.EMPTY and can_mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
            mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
            log("Trying to build a tower at " + str(target_loc))

        # Fill in any spots in the pattern with the appropriate paint.
        for pattern_tile in sense_nearby_map_infos(target_loc):
            if pattern_tile.get_mark() != pattern_tile.get_paint() and pattern_tile.get_mark() != PaintType.EMPTY:
                use_secondary = pattern_tile.get_mark() == PaintType.ALLY_SECONDARY
                if can_attack(pattern_tile.get_map_location()):
                    attack(pattern_tile.get_map_location(), use_secondary)

        # Complete the ruin if we can.
        if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
            complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
            set_timeline_marker("Tower built", 0, 255, 0)
            log("Built a tower at " + str(target_loc) + "!")

    # Move and attack randomly if no objective.
    avail_dir = [None] * 8
    idx = 0
    for dir in directions:
        next_loc = get_location().add(dir)
        if can_move(dir) and not sense_map_info(next_loc).get_paint().is_ally():
            avail_dir[idx] = dir
            idx += 1
    if idx > 0:
        dir = avail_dir[random.randint(0, idx - 1)]
        move(dir)
    else:
        dir = directions[random.randint(0, len(directions) - 1)]
        if can_move(dir):
            move(dir)


    # Try to paint beneath us as we walk to avoid paint penalties.
    # Avoiding wasting paint by re-painting our own tiles.
    current_tile = sense_map_info(get_location())
    if not current_tile.get_paint().is_ally() and can_attack(get_location()):
        attack(get_location())


def run_mopper():
    
    # Sense information about all visible nearby tiles.
    nearby_tiles = sense_nearby_map_infos()

    cur_ruin = None
    min_dist = -1
    for tile in nearby_tiles:
        if not tile.has_ruin():
            continue
        dist = get_location().distance_squared_to(tile.get_map_location())
        if cur_ruin == None or min_dist > dist:
            cur_ruin = tile
            min_dist = dist

    if cur_ruin is not None:
        target_loc = cur_ruin.get_map_location()
        # log(f"Detect ruin at: ({target_loc.x}, {target_loc.y})")
        dir = get_location().direction_to(target_loc)
        if can_move(dir):
            move(dir)

        # Mark the pattern we need to draw to build a tower here if we haven't already.
        should_mark = cur_ruin.get_map_location().subtract(dir)
        if sense_map_info(should_mark).get_mark() == PaintType.EMPTY and can_mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
            mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
            log("Trying to build a tower at " + str(target_loc))
        
        # Complete the ruin if we can.
        if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
            complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
            set_timeline_marker("Tower built", 0, 255, 0)
            log("Built a tower at " + str(target_loc) + "!")
    
    # Move and attack randomly.
    avail_dir = [None] * 8
    idx = 0
    for dir in directions:
        next_loc = get_location().add(dir)
        if can_move(dir) and not sense_map_info(next_loc).get_paint().is_ally():
            avail_dir[idx] = dir
            idx += 1
    if idx > 0:
        dir = avail_dir[random.randint(0, idx - 1)]
        next_loc = get_location().add(dir)
        if can_move(dir):
            move(dir)
        if can_mop_swing(dir):
            mop_swing(dir)
            # log("Mop Swing! Booyah!")
        elif can_attack(next_loc) and not sense_map_info(next_loc).get_paint().is_ally():
            attack(next_loc)
    else:
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = get_location().add(dir)
        if can_move(dir):
            move(dir)
        if can_mop_swing(dir):
            mop_swing(dir)
            # log("Mop Swing! Booyah!")
        elif can_attack(next_loc) and not sense_map_info(next_loc).get_paint().is_ally():
            attack(next_loc)

    # We can also move our code into different methods or classes to better organize it!
    # update_enemy_robots()

def run_splasher():
    # Sense information about all visible nearby tiles.
    nearby_tiles = sense_nearby_map_infos()

    # Search for a nearby ruin to complete.
    cur_ruin = None
    min_dist = -1
    for tile in nearby_tiles:
        if not tile.has_ruin():
            continue
        dist = get_location().distance_squared_to(tile.get_map_location())
        if cur_ruin == None or min_dist > dist:
            cur_ruin = tile
            min_dist = dist

    if cur_ruin is not None:
        target_loc = cur_ruin.get_map_location()
        # log(f"Detect ruin at: ({target_loc.x}, {target_loc.y})")
        dir = get_location().direction_to(target_loc)
        if can_move(dir):
            move(dir)

        # Mark the pattern we need to draw to build a tower here if we haven't already.
        should_mark = cur_ruin.get_map_location().subtract(dir)
        if sense_map_info(should_mark).get_mark() == PaintType.EMPTY and can_mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
            mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
            log("Trying to build a money tower at " + str(target_loc))

        # Fill in any spots in the pattern with the appropriate paint.
        for pattern_tile in sense_nearby_map_infos(target_loc, 8):
            if pattern_tile.get_mark().is_enemy():
                if can_attack(pattern_tile.get_map_location()):
                    attack(pattern_tile.get_map_location())

        # Complete the ruin if we can.
        if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
            complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
            set_timeline_marker("Tower built", 0, 255, 0)
            log("Built a tower at " + str(target_loc) + "!")

    # Move and attack randomly if no objective.
    avail_dir = [None] * 8
    idx = 0
    for dir in directions:
        next_loc = get_location().add(dir)
        if can_move(dir) and not sense_map_info(next_loc).get_paint().is_ally():
            avail_dir[idx] = dir
            idx += 1
    if idx > 0:
        dir = avail_dir[random.randint(0, idx - 1)]
        move(dir)
    else:
        dir = directions[random.randint(0, len(directions) - 1)]
        if can_move(dir):
            move(dir)

    # Try to paint beneath us as we walk to avoid paint penalties.
    # Avoiding wasting paint by re-painting our own tiles.
    current_tile = sense_map_info(get_location())
    if not current_tile.get_paint().is_ally() and can_attack(get_location()):
        attack(get_location(), 0)

def update_enemy_robots():
    # Sensing methods can be passed in a radius of -1 to automatically 
    # use the largest possible value.
    enemy_robots = sense_nearby_robots(team=get_team().opponent())
    if len(enemy_robots) == 0:
        return

    set_indicator_string("There are nearby enemy robots! Scary!")

    # Save an array of locations with enemy robots in them for possible future use.
    enemy_locations = [None] * len(enemy_robots)
    for i in range(len(enemy_robots)):
        enemy_locations[i] = enemy_robots[i].get_location()

    # Occasionally try to tell nearby allies how many enemy robots we see.
    ally_robots = sense_nearby_robots(team=get_team())
    if get_round_num() % 20 == 0:
        for ally in ally_robots:
            if can_send_message(ally.location):
                send_message(ally.location, len(enemy_robots))
