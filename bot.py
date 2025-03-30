import random
import math

from battlecode25.stubs import *

# This is an example bot written by the developers!
# Use this to help write your own code, or run it against your bot to see how well you can do!


# Globals
margin = 3
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
ruins_bitmask = [0 for _ in range(get_map_height())]
walls_bitmask = [0 for _ in range(get_map_height())]
spawn_turns = [
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    UnitType.SOLDIER,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    UnitType.SPLASHER,
    UnitType.SPLASHER,
    UnitType.SPLASHER,
    UnitType.MOPPER,
]
target = [
    MapLocation(margin, margin),
    MapLocation(get_map_width() - 1 - margin, get_map_height() - 1 - margin),
    MapLocation(margin, get_map_height() - 1 - margin),
    MapLocation(get_map_width() - 1 - margin, margin),
    MapLocation(margin, int(get_map_height() / 2)),
    MapLocation(int(get_map_width() / 2), margin),
    MapLocation(get_map_width() - 1 - margin, int(get_map_height() / 2)),
    MapLocation(int(get_map_width() / 2), get_map_height() - 1 - margin),
    MapLocation(int(get_map_width() / 2), int(get_map_height() / 2)),
]


def turn():
    """
    MUST be defined for robot to run
    This function will be called at the beginning of every turn and should contain the bulk of your robot commands
    """
    global turn_count
    turn_count += 1

    robo_type = get_type()
    if robo_type == UnitType.SOLDIER:
        run_soldier()
    elif robo_type == UnitType.MOPPER:
        run_mopper()
    elif robo_type == UnitType.SPLASHER:
        run_splasher()
    elif robo_type.is_tower_type():
        run_tower()


# bitmask handling


def mark_ruin(ruin_loc: MapLocation):
    ruins_bitmask[ruin_loc.x] = ruins_bitmask[ruin_loc.x] ^ (1 << ruin_loc.y)


def mark_wall(wall_loc: MapLocation):
    wall_loc[wall_loc.x] = wall_loc[wall_loc.x] ^ (1 << wall_loc.y)


# running towers


def run_tower():
    robot_spawn_point = give_random_location()
    robot_type = spawn_turns[turn_count % len(spawn_turns)]
    if can_build_robot(robot_type, robot_spawn_point):
        build_robot(robot_type, robot_spawn_point)
        log(f"Build {robot_type} at ({robot_spawn_point.x}, {robot_spawn_point.y})")
    if turn_count > 50 and get_type() == UnitType.LEVEL_ONE_MONEY_TOWER:
        disintegrate()


# running robots


def run_soldier():
    nearby_tiles = sense_nearby_map_infos(get_location())

    cur_ruin = None
    non_ally_tiles = [None] * len(nearby_tiles)
    
    num_non_ally_tiles = 0
    for tile in nearby_tiles:
        if not tile.get_paint().is_ally():
            non_ally_tiles[num_non_ally_tiles] = tile
            num_non_ally_tiles = num_non_ally_tiles + 1
    
        if tile.has_ruin() and not check_tower(tile):
            cur_ruin = tile

    if cur_ruin != None:
        target_loc = cur_ruin.get_map_location()
        dir = directions[
            (directions.index(get_location().direction_to(target_loc)) + 1)
            % len(directions)
        ]
        if can_move(dir):
            move(dir)

        ruins_pattern_type = check_ruins_mark(cur_ruin.get_map_location())
        if ruins_pattern_type == None:
            ruins_pattern_type = UnitType.LEVEL_ONE_MONEY_TOWER
            if random.randint(0, 1) == 0 and get_round_num() > 200:
                ruins_pattern_type = UnitType.LEVEL_ONE_PAINT_TOWER
            mark_tower(cur_ruin.get_map_location(), ruins_pattern_type)
        else:
            complete_pattern(cur_ruin.get_map_location(), ruins_pattern_type)
        paint_pattern(cur_ruin.get_map_location(), ruins_pattern_type)

    non_ally_tile = non_ally_tiles[random.randint(0, len(non_ally_tiles) - 1)]
    if non_ally_tile is not None:
        target_loc = non_ally_tile.get_map_location()
        dir = get_location().direction_to(target_loc)
        if can_move(dir):
            move(dir)
        if can_attack(non_ally_tile.get_map_location()):
            attack(non_ally_tile.get_map_location())

    # Move and attack randomly if no objective.
    run_bug0()

    return


def run_mopper():
    nearby_tiles = sense_nearby_map_infos()

    enemy_tiles = [None] * len(nearby_tiles)
    num_enemy_tiles = 0
    for tile in nearby_tiles:
        if tile.get_paint().is_enemy():
            enemy_tiles[num_enemy_tiles] = tile
            num_enemy_tiles = num_enemy_tiles + 1

    enemy_tile = enemy_tiles[random.randint(0, len(enemy_tiles) - 1)]
    if enemy_tile is not None:
        target_loc = enemy_tile.get_map_location()
        dir = get_location().direction_to(target_loc)
        if can_move(dir):
            move(dir)
        if can_attack(enemy_tile.get_map_location()):
            attack(enemy_tile.get_map_location())

    run_bug0()
    return


def run_splasher():
    nearby_tiles = sense_nearby_map_infos()
    non_ally_tiles = [None] * len(nearby_tiles)
    num_non_ally_tiles = 0
    for tile in nearby_tiles:
        if not tile.get_paint().is_ally():
            non_ally_tiles[num_non_ally_tiles] = tile
            num_non_ally_tiles = num_non_ally_tiles + 1

    non_ally_tile = non_ally_tiles[random.randint(0, len(non_ally_tiles) - 1)]

    if non_ally_tile is not None:
        target_loc = non_ally_tile.get_map_location()
        dir = get_location().direction_to(target_loc)
        if can_move(dir):
            move(dir)
        if can_attack(non_ally_tile.get_map_location()):
            attack(non_ally_tile.get_map_location())

    run_bug0()
    return


# miscellaneous


def give_random_location() -> MapLocation:
    dir = directions[random.randint(0, len(directions) - 1)]
    next_loc = get_location().add(dir)
    return next_loc


def check_tower(ruins: MapInfo) -> bool:
    return ruins.has_ruin() and can_sense_robot_at_location(ruins.get_map_location())


def check_ruins_mark(ruins_loc: MapLocation) -> UnitType:
    # check paint tower mark
    next_loc_N = ruins_loc.add(directions[0])
    next_loc_S = ruins_loc.add(directions[4])
    if check_pattern_mark(
        1, 2, next_loc_N, UnitType.LEVEL_ONE_PAINT_TOWER
    ) or check_pattern_mark(3, 2, next_loc_S, UnitType.LEVEL_ONE_PAINT_TOWER):
        return UnitType.LEVEL_ONE_PAINT_TOWER

    # check money tower mark
    next_loc_NE = ruins_loc.add(directions[1])
    next_loc_SW = ruins_loc.add(directions[5])
    if check_pattern_mark(
        1, 3, next_loc_NE, UnitType.LEVEL_ONE_MONEY_TOWER
    ) or check_pattern_mark(3, 1, next_loc_SW, UnitType.LEVEL_ONE_MONEY_TOWER):
        return UnitType.LEVEL_ONE_MONEY_TOWER

    # check defense tower mark
    next_loc_E = ruins_loc.add(directions[2])
    next_loc_W = ruins_loc.add(directions[6])
    if check_pattern_mark(
        2, 3, next_loc_E, UnitType.LEVEL_ONE_DEFENSE_TOWER
    ) or check_pattern_mark(2, 1, next_loc_W, UnitType.LEVEL_ONE_DEFENSE_TOWER):
        return UnitType.LEVEL_ONE_DEFENSE_TOWER

    return None


def check_pattern_mark(
    row_pos: int,
    col_pos: int,
    global_pos: MapLocation,
    TowerType: UnitType,
):
    if not can_sense_location(global_pos):
        return False
    tile_info = sense_map_info(global_pos)
    return (
        tile_info.get_mark() != PaintType.EMPTY
        and (tile_info.get_mark() == PaintType.ALLY_SECONDARY)
        == get_tower_pattern(TowerType)[row_pos][col_pos]
    )


def inside_pattern_range(row_pos: int, col_pos: int, width: int = 5, height: int = 5):
    return 0 <= row_pos and row_pos < width and 0 <= col_pos and col_pos < height


def paint_pattern(ruins_loc: MapLocation, tower_type: UnitType):
    pattern = get_tower_pattern(tower_type)
    nearby_ruins_tiles = sense_nearby_map_infos(ruins_loc, 8)

    for pattern_tile in nearby_ruins_tiles:
        if pattern_tile.has_ruin():
            continue
        target_loc = pattern_tile.get_map_location()
        row_pos = target_loc.x - ruins_loc.x + 2
        col_pos = target_loc.y - ruins_loc.y + 2
        if not can_attack(pattern_tile.get_map_location()):
            continue

        if not inside_pattern_range(row_pos, col_pos):
            if not pattern_tile.get_paint().is_ally():
                attack(get_location())
            continue

        if (
            pattern_tile.get_paint() == PaintType.EMPTY
            or (pattern_tile.get_paint() == PaintType.ALLY_SECONDARY)
            != pattern[row_pos][col_pos]
        ):
            attack(pattern_tile.get_map_location(), pattern[row_pos][col_pos])


def mark_tower(ruins_loc: MapLocation, tower_type: UnitType):
    pattern = get_tower_pattern(tower_type)

    if tower_type == UnitType.LEVEL_ONE_PAINT_TOWER:
        next_loc_N = ruins_loc.add(directions[0])
        next_loc_S = ruins_loc.add(directions[4])
        if can_mark(next_loc_N):
            mark(next_loc_N, pattern[1][2])
            # log(f"Mark {tower_type} at ({ruins_loc.x}, {ruins_loc.y})")
        if can_mark(next_loc_S):
            mark(next_loc_S, pattern[3][2])
            # log(f"Mark {tower_type} at ({ruins_loc.x}, {ruins_loc.y})")

    if tower_type == UnitType.LEVEL_ONE_MONEY_TOWER:
        next_loc_NE = ruins_loc.add(directions[1])
        next_loc_SW = ruins_loc.add(directions[5])
        if can_mark(next_loc_NE):
            mark(next_loc_NE, pattern[1][3])
            # log(f"Mark {tower_type} at ({ruins_loc.x}, {ruins_loc.y})")
        if can_mark(next_loc_SW):
            mark(next_loc_SW, pattern[3][1])
            # log(f"Mark {tower_type} at ({ruins_loc.x}, {ruins_loc.y})")

    if tower_type == UnitType.LEVEL_ONE_DEFENSE_TOWER:
        next_loc_E = ruins_loc.add(directions[2])
        next_loc_W = ruins_loc.add(directions[6])
        if can_mark(next_loc_E):
            mark(next_loc_E, pattern[2][3])
            # log(f"Mark {tower_type} at ({ruins_loc.x}, {ruins_loc.y})")
        if can_mark(next_loc_W):
            mark(next_loc_W, pattern[2][1])
            # log(f"Mark {tower_type} at ({ruins_loc.x}, {ruins_loc.y})")

    return


def complete_pattern(ruin_loc: MapLocation, tower_type: UnitType):
    if can_complete_tower_pattern(tower_type, ruin_loc):
        complete_tower_pattern(tower_type, ruin_loc)
        set_timeline_marker("Tower built", 0, 255, 0)
        log("Built a tower at " + str(ruin_loc) + "!")


def run_bug0():
    current_pos = get_location()

    # Choose target based on bot ID (i think this is also random)
    id = get_id()
    dir = current_pos.direction_to(target[(id + turn_count // 40) % len(target)])

    # Movement
    if can_move(dir):
        move(dir)
    elif dir != Direction.CENTER:
        idx = directions.index(dir)
        for i in range(0, 8):
            if can_move(directions[int(i + idx) % 8]):
                move(directions[int(i + idx) % 8])
                break

    current_pos = get_location()
    # Paint current tile
    if not sense_map_info(current_pos).get_paint().is_ally() and can_attack(
        current_pos
    ):
        attack(current_pos)
