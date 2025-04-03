import random

from battlecode25.stubs import *

# This is an example bot written by the developers!
# Use this to help write your own code, or run it against your bot to see how well you can do!


# Globals
margin_x = get_location().x
margin_y = get_location().y
mid_x = (get_map_width() // 2) - 1
mid_y = (get_map_height() // 2) - 1
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
targets = [
    [
        MapLocation(0, 0),
        MapLocation(get_map_width() - 1, get_map_height() - 1),
        MapLocation(0, get_map_height() - 1),
        MapLocation(get_map_width() - 1, 0),
    ],
    [
        MapLocation(get_map_width() - 1 - margin_x, get_map_height() - 1 - margin_y),
        MapLocation(get_map_width() - 1 - margin_x, margin_y),
        MapLocation(margin_x, get_map_height() - 1 - margin_y),
        MapLocation(margin_x, margin_y),
        MapLocation(0, 0),
        MapLocation(get_map_width() - 1, get_map_height() - 1),
        MapLocation(0, get_map_height() - 1),
        MapLocation(get_map_width() - 1, 0),
    ],
]
prev_pos = [MapLocation(-1, -1)] * 5
prev_target = MapLocation(0, 0)
obstacle_start_dist = 0
is_tracing = False
tracing_dir = None
min_dist = 10000
min_dist_loc = None
turn_count = 0
target_idx = get_id() % len(targets[get_type() != UnitType.Soldier])


class FastSet:
    def __init__(self):
        self.values = set()

    def encode_loc(self, x, y):
        return (x << 6) | y

    def decode_loc(self, encoded):
        value = encoded[0]
        return (value >> 6, value & 0x3F)

    def add(self, x, y):
        encoded = self.encode_loc(x, y)
        if encoded not in self.values:
            self.values.add(encoded)
            return True
        return False

    def contains(self, x, y):
        return self.encode_loc(x, y) in self.values

    def remove(self, x, y):
        encoded = self.encode_loc(x, y)
        self.discard(encoded)

    def getLoc(self):
        return [self.decode_loc(bytes([b])) for b in self.values]


ruinLocations = FastSet()
friendly_tower_locations = FastSet()
enemyTowerLocations = FastSet()
flickerTowerLocations = FastSet()
impossible_srp_locations = FastSet()


def init():
    random.shuffle(spawn_turns)


def turn():
    random.seed(get_id() * get_time_left())
    """
    MUST be defined for robot to run
    This function will be called at the beginning of every turn and should contain the bulk of your robot commands
    """
    global turn_count
    global target_idx
    turn_count += 1
    robo_type = get_type()

    if robo_type.is_robot_type() and turn_count == 0:
        init()

    if robo_type.is_robot_type() and (
        turn_count % 50 == 49
        or get_location().distance_squared_to(
            targets[get_type() != UnitType.Soldier][target_idx]
        )
        < 8
    ):
        target_idx += 1
        target_idx = target_idx % len(targets[get_type() != UnitType.Soldier])

    if robo_type == UnitType.SOLDIER:
        run_soldier()
    elif robo_type == UnitType.MOPPER:
        run_mopper()
    elif robo_type == UnitType.SPLASHER:
        run_splasher()
    elif robo_type.is_tower_type():
        run_tower(robo_type)


# running towers


def run_tower(tower_type: UnitType):
    spawn_robots()
    attack_robots()
    if tower_type == UnitType.LEVEL_ONE_MONEY_TOWER:
        run_lvl_1_money_tower()
    if is_paint_tower(tower_type):
        run_paint_tower()
    if is_defense_tower(tower_type):
        run_defense_tower()


def run_lvl_1_money_tower():
    if (
        (turn_count > 50)
        and get_chips() > 2500
        and not check_enemy_paint_in_ruins_pattern(get_location())
    ):
        disintegrate()


def run_paint_tower():
    if get_chips() > 10000 and can_upgrade_tower(get_location()):
        upgrade_tower(get_location())


def run_defense_tower():
    if (
        (turn_count > 50)
        and get_chips() > 2500
        and not check_enemy_paint_in_ruins_pattern(get_location())
    ):
        disintegrate()


def spawn_robots():
    robot_spawn_point = give_random_location()
    robot_type = spawn_turns[turn_count % len(spawn_turns)]
    if robot_type == UnitType.MOPPER:
        if random.randint(0, 2) != 0:
            robot_type = UnitType.SPLASHER
    if can_build_robot(robot_type, robot_spawn_point):
        build_robot(robot_type, robot_spawn_point)
        log(f"Built {robot_type} at {robot_spawn_point}")


def attack_robots():
    robots_nearby = sense_nearby_robots(get_location(), 9)
    num_enemy_robot = 0
    enemy_splasher = None
    enemy_mopper = None

    for robot in robots_nearby:
        if robot.get_team() == get_team():
            continue
        num_enemy_robot += 1
        if robot.get_type() == UnitType.SPLASHER:
            enemy_splasher = robot
        if robot.get_type() == UnitType.MOPPER:
            enemy_mopper = robot

    if num_enemy_robot > 1 and can_attack(None):
        attack(None)

    if enemy_splasher != None and can_attack(enemy_splasher.get_location()):
        attack(enemy_splasher.get_location())
    elif enemy_mopper != None and can_attack(enemy_mopper.get_location()):
        attack(enemy_mopper.get_location())


# running robots


def run_soldier():
    nearby_tiles = sense_nearby_map_infos(get_location())

    cur_ruin = None
    empty_tiles = [None] * len(nearby_tiles)

    num_empty_tiles = 0
    for tile in nearby_tiles:
        if tile.get_paint() == PaintType.EMPTY:
            empty_tiles[num_empty_tiles] = tile
            num_empty_tiles = num_empty_tiles + 1

        if (
            tile.has_ruin()
            and not check_tower(tile)
            and not check_enemy_paint_in_ruins_pattern(tile.get_map_location())
            and num_of_soldier_within_pattern(tile.get_map_location()) < 4
        ):
            cur_ruin = tile

    if cur_ruin != None:
        target_loc = cur_ruin.get_map_location()
        dir = directions[
            (directions.index(get_location().direction_to(target_loc)) + 2)
            % len(directions)
        ]
        run_bug1(target_loc.add(dir))

        ruins_pattern_type = check_ruins_mark(cur_ruin.get_map_location())
        if ruins_pattern_type == None:
            ruins_pattern_type = UnitType.LEVEL_ONE_MONEY_TOWER
            if random.randint(0, 1) == 0 and get_num_towers() > 3:
                ruins_pattern_type = UnitType.LEVEL_ONE_PAINT_TOWER
            if random.randint(0, 4) == 0 and get_num_towers() > 5:
                ruins_pattern_type = UnitType.LEVEL_ONE_DEFENSE_TOWER
            mark_tower(cur_ruin.get_map_location(), ruins_pattern_type)
        else:
            complete_pattern(cur_ruin.get_map_location(), ruins_pattern_type)
        paint_pattern(cur_ruin.get_map_location(), ruins_pattern_type)

    empty_tile = empty_tiles[random.randint(0, len(empty_tiles) - 1)]
    if empty_tile is not None:
        target_loc = empty_tile.get_map_location()
        run_bug0(target_loc)
        if can_attack(empty_tile.get_map_location()):
            attack(empty_tile.get_map_location())

    # Move and attack randomly if no objective.
    if get_round_num() > 300:
        buld_srp()
    run_bug0(targets[get_type() != UnitType.Soldier][target_idx])
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
        if can_attack(enemy_tile.get_map_location()):
            attack(enemy_tile.get_map_location())

    run_bug2(targets[get_type() != UnitType.Soldier][target_idx])
    # mopper_mop()
    return


def mopper_mop():
    
    enemy_bots = [[None] * 3 for i in range(0, 3)]
    nearby_robots = sense_nearby_robots(radius_squared=2)
    for robot in nearby_robots:
        x = robot.get_location().x - get_location().x + 1
        y = robot.get_location().y - get_location().y + 1
        enemy_bots[x][y] = robot
    best_do_mop_swing = False
    best_mop_dir = None
    best_mop_heur = None
    for dir in directions:
        if not can_attack(get_location().add(dir)):
            continue

        nearby_tiles = sense_nearby_map_infos(get_location().add(dir), 8)
        num_ruins_nearby = 0
        for tile in nearby_tiles:
            if tile.has_ruin():
                num_ruins_nearby += 1

        mop_heur = 25 + 100 if num_ruins_nearby > 0 else 0
        valid_dir = [dir]
        do_mop_swing = False

        if is_cardinal_dir(dir) and can_mop_swing(dir):
            valid_dir = [dir.rotate_left(), dir, dir.rotate_right()]

        for dir_p in valid_dir:
            x = dir_p.get_dx() + 1
            y = dir_p.get_dy() + 1

            if enemy_bots[x][y] != None:
                mop_heur += 75
                if enemy_bots[x][y].get_paint_amount() < 10:
                    mop_heur += 100

                if dir_p != dir:
                    do_mop_swing = True

        if best_mop_heur == None or mop_heur > best_mop_heur:
            best_mop_heur = mop_heur
            best_mop_dir = dir
            best_do_mop_swing = do_mop_swing

    log(f"Best heuristic for mopper is {best_mop_dir}")
    if best_mop_heur != None:
        if best_do_mop_swing and can_mop_swing(best_mop_dir):
            mop_swing(best_mop_dir)
            log(f"{get_type()} mop swing in the {best_mop_dir} directions")
            set_timeline_marker("Mopper mop swing", 0, 0, 255)
        elif can_attack(get_location().add(dir)):
            attack(get_location().add(dir))
            log(f"{get_type()} attack at {get_location().add(dir)}")
            set_timeline_marker("Mopper attacked", 255, 0, 255)


def run_splasher():
    nearby_tiles = sense_nearby_map_infos()
    non_ally_tiles = [None] * len(nearby_tiles)
    num_non_ally_tiles = 0
    for tile in nearby_tiles:
        if not tile.get_paint().is_ally() and tile.is_passable():
            non_ally_tiles[num_non_ally_tiles] = tile
            num_non_ally_tiles = num_non_ally_tiles + 1

    non_ally_tile = non_ally_tiles[random.randint(0, len(non_ally_tiles) - 1)]

    if non_ally_tile is not None:
        if can_attack(non_ally_tile.get_map_location()):
            attack(non_ally_tile.get_map_location())

    run_bug2(targets[get_type() != UnitType.Soldier][target_idx])
    # splasher_attack()
    return


def splasher_attack():
    splash_heur = [[0] * 7 for _ in range(0, 7)]
    nearby_tiles = sense_nearby_map_infos(radius_squared=18)
    for tile in nearby_tiles:
        x = tile.get_map_location().x - get_location().x + 3
        y = tile.get_map_location().y - get_location().y + 3
        if not inside_range(x, y, 7, 7):
            continue
        if tile.get_paint().is_ally() or tile.is_wall():
            splash_heur[x][y] = -2
        elif tile.get_paint() == PaintType.EMPTY:
            splash_heur[x][y] = 1
        else:
            splash_heur[x][y] = 10
    best_attack_loc = MapLocation(-1, -1)
    best_attack_heur = None
    for x in range(1, len(splash_heur) - 1):
        for y in range(1, len(splash_heur[0]) - 1):
            if not can_attack(MapLocation(x, y)):
                continue
            sum_heur = 0
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    sum_heur += splash_heur[x + dx][y + dy]
            if best_attack_heur == None or best_attack_heur < sum_heur:
                best_attack_loc = MapLocation(x, y)
                best_attack_heur = sum_heur

    if best_attack_loc != MapLocation(-1, -1) and can_attack(best_attack_loc):
        attack(best_attack_loc)
        log(f"{get_type()} attack at {best_attack_loc}")
        set_timeline_marker("Splasher attacked", 255, 0, 0)
    return


# miscellaneous


def inside_range(row_pos: int, col_pos: int, width: int = 5, height: int = 5) -> bool:
    return 0 <= row_pos and row_pos < width and 0 <= col_pos and col_pos < height


def max(a: int, b: int) -> int:
    if a > b:
        return a
    return b


def is_cardinal_dir(dir: Direction):
    return (
        dir == Direction.NORTH
        or dir == Direction.SOUTH
        or dir == Direction.EAST
        or dir == Direction.WEST
    )


def is_paint_tower(tower_type: UnitType) -> bool:
    return (
        tower_type == UnitType.LEVEL_ONE_PAINT_TOWER
        or tower_type == UnitType.LEVEL_TWO_PAINT_TOWER
        or tower_type == UnitType.LEVEL_THREE_PAINT_TOWER
    )


def is_defense_tower(tower_type: UnitType) -> bool:
    return (
        tower_type == UnitType.LEVEL_ONE_DEFENSE_TOWER
        or tower_type == UnitType.LEVEL_TWO_DEFENSE_TOWER
        or tower_type == UnitType.LEVEL_THREE_DEFENSE_TOWER
    )


def is_money_tower(tower_type: UnitType) -> bool:
    return (
        tower_type == UnitType.LEVEL_ONE_MONEY_TOWER
        or tower_type == UnitType.LEVEL_TWO_MONEY_TOWER
        or tower_type == UnitType.LEVEL_THREE_MONEY_TOWER
    )


def check_tower(ruins: MapInfo) -> bool:
    return ruins.has_ruin() and can_sense_robot_at_location(ruins.get_map_location())


def check_in_the_right_path(next_loc: MapLocation) -> bool:
    dir1 = get_location().direction_to(next_loc)
    dir2 = get_location().direction_to(
        targets[get_type() != UnitType.Soldier][target_idx]
    )
    if dir1 == Direction.CENTER or dir2 == Direction.CENTER:
        return True
    idx1 = directions.index(dir1)
    idx2 = directions.index(dir2)
    return abs(idx1 - idx2) <= 3 or abs(idx1 - idx2) >= 6


def give_random_location() -> MapLocation:
    dir = directions[random.randint(0, len(directions) - 1)]
    next_loc = get_location().add(dir)
    return next_loc


# Mark and paint ruins


def check_enemy_paint_in_ruins_pattern(ruin_loc: MapLocation) -> bool:
    nearby_ruins_tiles = sense_nearby_map_infos(ruin_loc)

    for pattern_tile in nearby_ruins_tiles:
        if pattern_tile.has_ruin():
            continue
        target_loc = pattern_tile.get_map_location()
        row_pos = target_loc.x - ruin_loc.x + 2
        col_pos = target_loc.y - ruin_loc.y + 2

        if inside_range(row_pos, col_pos):
            if pattern_tile.get_paint().is_enemy():
                return True

    return False


def check_ruins_mark(ruin_loc: MapLocation) -> UnitType:
    # check paint tower mark
    next_loc_N = ruin_loc.add(directions[0])
    next_loc_S = ruin_loc.add(directions[4])
    if check_pattern_mark(
        1, 2, next_loc_N, UnitType.LEVEL_ONE_PAINT_TOWER
    ) or check_pattern_mark(3, 2, next_loc_S, UnitType.LEVEL_ONE_PAINT_TOWER):
        return UnitType.LEVEL_ONE_PAINT_TOWER

    # check money tower mark
    next_loc_NE = ruin_loc.add(directions[1])
    next_loc_SW = ruin_loc.add(directions[5])
    next_loc_NW = ruin_loc.add(directions[7])
    next_loc_SE = ruin_loc.add(directions[3])
    if (
        check_pattern_mark(1, 3, next_loc_NE, UnitType.LEVEL_ONE_MONEY_TOWER)
        or check_pattern_mark(3, 1, next_loc_SW, UnitType.LEVEL_ONE_MONEY_TOWER)
        or check_pattern_mark(1, 1, next_loc_NW, UnitType.LEVEL_ONE_MONEY_TOWER)
        or check_pattern_mark(3, 3, next_loc_SE, UnitType.LEVEL_ONE_MONEY_TOWER)
    ):
        return UnitType.LEVEL_ONE_MONEY_TOWER

    # check defense tower mark
    next_loc_E = ruin_loc.add(directions[2])
    next_loc_W = ruin_loc.add(directions[6])
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
) -> bool:
    if not can_sense_location(global_pos):
        return False
    tile_info = sense_map_info(global_pos)
    return (
        tile_info.get_mark() != PaintType.EMPTY
        and (tile_info.get_mark() == PaintType.ALLY_SECONDARY)
        == get_tower_pattern(TowerType)[row_pos][col_pos]
    )


def paint_pattern(ruin_loc: MapLocation, tower_type: UnitType):
    pattern = get_tower_pattern(tower_type)
    nearby_ruins_tiles = sense_nearby_map_infos(ruin_loc, 8)

    for pattern_tile in nearby_ruins_tiles:
        if pattern_tile.has_ruin():
            continue
        target_loc = pattern_tile.get_map_location()
        row_pos = target_loc.x - ruin_loc.x + 2
        col_pos = target_loc.y - ruin_loc.y + 2
        if not can_attack(pattern_tile.get_map_location()):
            continue

        if not inside_range(row_pos, col_pos):
            if not pattern_tile.get_paint().is_ally():
                attack(get_location())
            continue

        if (
            pattern_tile.get_paint() == PaintType.EMPTY
            or (pattern_tile.get_paint() == PaintType.ALLY_SECONDARY)
            != pattern[row_pos][col_pos]
        ):
            attack(pattern_tile.get_map_location(), pattern[row_pos][col_pos])


def mark_tower(ruin_loc: MapLocation, tower_type: UnitType):
    pattern = get_tower_pattern(tower_type)

    if tower_type == UnitType.LEVEL_ONE_PAINT_TOWER:
        next_loc_N = ruin_loc.add(directions[0])
        next_loc_S = ruin_loc.add(directions[4])
        if can_mark(next_loc_N):
            mark(next_loc_N, pattern[1][2])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")
        if can_mark(next_loc_S):
            mark(next_loc_S, pattern[3][2])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")

    if tower_type == UnitType.LEVEL_ONE_MONEY_TOWER:
        next_loc_NE = ruin_loc.add(directions[1])
        next_loc_SW = ruin_loc.add(directions[5])
        next_loc_NW = ruin_loc.add(directions[7])
        next_loc_SE = ruin_loc.add(directions[3])
        if can_mark(next_loc_NE):
            mark(next_loc_NE, pattern[1][3])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")
        if can_mark(next_loc_SW):
            mark(next_loc_SW, pattern[3][1])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")
        if can_mark(next_loc_NW):
            mark(next_loc_NW, pattern[1][1])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")
        if can_mark(next_loc_SE):
            mark(next_loc_SE, pattern[3][3])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")

    if tower_type == UnitType.LEVEL_ONE_DEFENSE_TOWER:
        next_loc_E = ruin_loc.add(directions[2])
        next_loc_W = ruin_loc.add(directions[6])
        if can_mark(next_loc_E):
            mark(next_loc_E, pattern[2][3])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")
        if can_mark(next_loc_W):
            mark(next_loc_W, pattern[2][1])
            # log(f"Mark {tower_type} at ({ruin_loc.x}, {ruin_loc.y})")

    return


def complete_pattern(ruin_loc: MapLocation, tower_type: UnitType):
    if can_complete_tower_pattern(tower_type, ruin_loc):
        complete_tower_pattern(tower_type, ruin_loc)
        set_timeline_marker("Tower built", 0, 255, 0)
        log(f"Built a {tower_type} at {ruin_loc}")


def num_of_soldier_within_pattern(ruin_loc: MapLocation) -> int:
    num_of_soldier = 0
    nearby_ally_robots = sense_nearby_robots(ruin_loc, 8, get_team())
    for ally_robot in nearby_ally_robots:
        if ally_robot.get_type() == UnitType.SOLDIER:
            num_of_soldier += 1
    return num_of_soldier


# pathfinding


def moving_micro(dir: Direction, target: MapLocation) -> int:
    next_loc = get_location().add(dir)
    score = -prev_pos.count(next_loc)
    target_dir = get_location().direction_to(target)
    if target_dir == dir:
        score += 20
    if dir == target_dir.rotate_left() or dir == target_dir.rotate_right():
        score += 15
    mopper_penalty = 2 if get_type() == UnitType.MOPPER else 1
    if sense_map_info(next_loc).get_paint() == PaintType.EMPTY:
        score -= 10 * mopper_penalty
    if sense_map_info(next_loc).get_paint().is_enemy():
        score -= 5 * mopper_penalty
    nearby_robots = sense_nearby_robots()
    num_ally_robot = 0
    num_enemy_tower = 0
    enemy_mopper_presence = 0
    for robot in nearby_robots:
        if (
            robot.get_team() == get_team()
            and robot.get_location().is_within_distance_squared(next_loc, 2)
        ):
            num_ally_robot += 1
        if (
            robot.get_team() != get_team()
            and robot.get_type().is_tower_type()
            and robot.get_location().is_within_distance_squared(
                next_loc, 16 if is_defense_tower(robot.get_type()) else 9
            )
        ):
            num_enemy_tower += 1
        if (
            robot.get_team() != get_team()
            and robot.get_type() == UnitType.MOPPER
            and robot.get_location().is_within_distance_squared(next_loc, 2)
        ):
            enemy_mopper_presence = 1
    score -= num_ally_robot * 5 + num_enemy_tower * 20 + enemy_mopper_presence * 20
    return score


def choose_best_dir(target_loc: MapLocation) -> Direction:
    best_dir = Direction.CENTER
    best_mircro = 0
    for dir in directions:
        if not can_move(dir):
            continue
        micro = moving_micro(dir, target_loc)
        if best_dir == Direction.CENTER or best_mircro < micro:
            best_dir = dir
            best_mircro = micro

    return best_dir


def run_bug0(target: MapLocation):
    # Choose target based on bot ID (i think this is also random)
    # dir = choose_best_dir(target)
    dir = get_location().direction_to(target)

    # Movement
    if can_move(dir):
        move(dir)
    elif dir != Direction.CENTER:
        idx = directions.index(dir)
        for i in range(0, 8):
            if can_move(directions[(i + idx) % len(directions)]):
                move(directions[(i + idx) % len(directions)])
                break

    if not sense_map_info(get_location()).get_paint().is_ally() and can_attack(
        get_location()
    ):
        attack(get_location())


def run_bug1(target: MapLocation):
    global is_tracing
    global tracing_dir
    global min_dist_loc
    global min_dist
    global target_idx

    # dir = choose_best_dir(dir)
    dir = get_location().direction_to(target)

    if dir == Direction.CENTER:
        target_idx += 1
        target_idx = target_idx % len(targets[get_type() != UnitType.Soldier])
        return

    # scuffed bug1
    if not is_tracing:
        if can_move(dir):
            move(dir)
        else:
            is_tracing = True
            tracing_dir = dir
    else:
        if get_location().x == min_dist_loc.x and get_location().y == min_dist_loc.y:
            is_tracing = False
            tracing_dir = None
            min_dist = 10000
            min_dist_loc = None
        else:
            curDist = get_location().distance_squared_to(target)
            if curDist < min_dist:
                min_dist = curDist
                min_dist_loc = get_location()

            if can_move(tracing_dir):
                move(tracing_dir)
                w = directions.index(tracing_dir)
                w = (w + 2) % len(directions)
                tracing_dir = directions[w]
            else:
                w = directions.index(tracing_dir)
                for i in range(0, 8):
                    w -= 1
                    w += 8
                    w = w % len(directions)
                    if can_move(directions[w]):
                        move(directions[w])
                        tracing_dir = directions[(w + 2) % len(directions)]
                        break

    if not sense_map_info(get_location()).get_paint().is_ally() and can_attack(
        get_location()
    ):
        attack(get_location())


# Draw horizontal lines
def draw_line_H(x0, y0, x1, y1):
    a = []
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0

    dir = -1 if dy < 0 else 1
    dy *= dir

    if dx != 0:
        y = y0
        D = 2 * dy - dx
        for i in range(dx + 1):
            a.append((x0 + i, y))
            if D >= 0:
                y += dir
                D = D - 2 * dx
            D = D + 2 * dy
    else:
        for i in range(dy + 1):
            a.append((x0, y0 + i))
    return a


# Draw vertical lines
def draw_line_V(x0, y0, x1, y1):
    a = []
    if y0 > y1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0

    dir = -1 if dx < 0 else 1
    dx *= dir

    if dy != 0:
        x = x0
        D = 2 * dx - dy
        for i in range(dy + 1):
            a.append((x, y0 + i))
            if D >= 0:
                x += dir
                D = D - 2 * dy
            D = D + 2 * dx
    else:
        for i in range(dx + 1):
            a.append((x0 + i, y0))
    return a


# Main func for draw lines
def draw_line(x0, y0, x1, y1):
    if abs(x1 - x0) > abs(y1 - y0):
        return draw_line_H(x0, y0, x1, y1)
    else:
        return draw_line_V(x0, y0, x1, y1)


def run_bug2(target: MapLocation):
    global is_tracing
    global tracing_dir
    global obstacle_start_dist
    global prev_target
    global target_idx

    prev_target = get_location()
    # dir = choose_best_dir(target)
    dir = get_location().direction_to(target)
    if dir == Direction.CENTER:
        target_idx += 1
        target_idx = target_idx % len(targets[get_type() != UnitType.Soldier])
        return

    # scuffed bug2

    line = []
    if target != prev_target:
        prev_target = target
        line = draw_line(get_location().x, get_location().y, target.x, target.y)

    if not is_tracing:
        if can_move(dir):
            move(dir)
        else:
            is_tracing = True
            obstacle_start_dist = get_location().distance_squared_to(target)
            tracing_dir = dir
    else:
        if (
            int(get_location().x),
            int(get_location().y),
        ) in line and get_location().distance_squared_to(target) < obstacle_start_dist:
            is_tracing = False
        else:
            if can_move(tracing_dir):
                move(tracing_dir)
                w = directions.index(tracing_dir)
                w = (w + 2) % 8
                tracing_dir = directions[w]
            else:
                w = directions.index(tracing_dir)
                for i in range(0, 8):
                    w -= 1
                    w += 8
                    w = w % 8
                    if can_move(directions[w]):
                        move(directions[w])
                        tracing_dir = directions[(w + 2) % 8]
                        break


# build srp
buld_srp_location = get_location()


def paint_srp(center: MapLocation):
    pattern = get_resource_pattern()

    for pattern_tile in sense_nearby_map_infos(center, 8):
        target_loc = pattern_tile.get_map_location()
        row_pos = target_loc.x - center.x + 2
        col_pos = target_loc.y - center.y + 2
        if not can_attack(pattern_tile.get_map_location()):
            continue

        if not inside_range(row_pos, col_pos):
            if not pattern_tile.get_paint().is_ally():
                attack(get_location())
            continue

        if (
            pattern_tile.get_paint() == PaintType.EMPTY
            or (pattern_tile.get_paint() == PaintType.ALLY_SECONDARY)
            != pattern[row_pos][col_pos]
        ):
            attack(pattern_tile.get_map_location(), pattern[row_pos][col_pos])


def is_valid_srp_location(loc: MapLocation):
    if ((loc.x <= mid_x) != (get_location().x <= mid_x)) or (
        (loc.y <= mid_y) != (get_location().y <= mid_y)
    ):
        return False
    if abs(loc.x - mid_x) < 2 or abs(loc.y - mid_y) < 2:
        return False
    return (
        can_sense_location(loc)
        and not impossible_srp_locations.contains(loc.x, loc.y)
        and not sense_map_info(loc).is_resource_pattern_center()
    )


def getcloset_srp_loc(raw_ruin_locs):
    loc = get_location()
    x = None
    y = None

    if loc.x <= mid_x:
        x = (loc.x + 2) % 4
    else:
        x = (loc.x - get_map_width() - 1) % 4

    if loc.y <= mid_y:
        y = (loc.y + 2) % 4
    else:
        y = (loc.y - get_map_height() - 1) % 4

    if x < 0:
        x += 4
    if y < 0:
        y += 4

    offsets = [
        (0, 0),
        (0, 4),
        (4, 0),
        (4, 4),
        (-4, 0),
        (0, -4),
        (-4, -4),
        (-4, 4),
        (4, -4),
    ]
    possible_srp_locations = [
        (
            MapLocation(loc.x + dx - x, loc.y + dy - y)
            if is_valid_srp_location(MapLocation(loc.x + dx - x, loc.y + dy - y))
            else None
        )
        for dx, dy in offsets
    ]

    for ruin in raw_ruin_locs:
        for possible_loc in possible_srp_locations:
            if (
                possible_loc is not None
                and abs(ruin.x - possible_loc.x) <= 5
                and abs(ruin.y - possible_loc.y <= 5)
            ):
                impossible_srp_locations.add(possible_loc.x, possible_loc.y)
                possible_loc = None
                break

    min_srp_dist = 20
    closet_srp_loc = None
    for possible_loc in possible_srp_locations:
        if possible_loc is not None:
            dist = get_location().distance_squared_to(possible_loc)
            if dist < min_srp_dist:
                min_srp_dist = dist
                closet_srp_loc = possible_loc

    return closet_srp_loc


def buld_srp():
    # if get_num_towers() < 6 or get_round_num() < 150:
    # switch to default mode + return
    #   return
    # if not building srp or not running default: return

    ruin_locs = [MapLocation(x, y) for x, y in ruinLocations.getLoc()]
    raw_ruins = FastSet()

    for ruin in ruin_locs:
        # if ruin not taken or flickering tower
        if not friendly_tower_locations.contains(ruin.x, ruin.y):
            raw_ruins.add(ruin.x, ruin.y)
        if flickerTowerLocations.contains(ruin.x, ruin.y):
            raw_ruins.add(ruin.x, ruin.y)

    raw_ruin_locs = [MapLocation(x, y) for x, y in raw_ruins.getLoc()]

    if len(raw_ruin_locs) != 0:
        # if in building srp mode
        for raw_ruin in raw_ruin_locs:
            if abs(raw_ruin.x - buld_srp_location.x) <= 5 and abs(
                raw_ruin.y - buld_srp_location.y <= 5
            ):
                impossible_srp_locations.add(buld_srp_location.x, buld_srp_location.y)
                # switch to default + return

    # if in mode default
    closet_srp_loc = getcloset_srp_loc(raw_ruin_locs)
    if closet_srp_loc is not None:
        # switch to mode building srp + no paint counter
        buld_srp_location = closet_srp_loc
    else:
        return

    # set_timeline_marker("Build SRP", 0, 0, 255)
    # log("Trying to build SRP at " + str(buld_srp_location) + "!")

    if can_sense_location(buld_srp_location):
        if sense_map_info(buld_srp_location).is_resource_pattern_center():
            impossible_srp_locations.add(buld_srp_location.x, buld_srp_location.y)
            return

    if get_location().distance_squared_to(buld_srp_location) <= 2:
        if not can_mark_resource_pattern(buld_srp_location):
            impossible_srp_locations.add(buld_srp_location.x, buld_srp_location.y)
            return

    num_enemy_paint = 0
    num_soldiers_building = 0

    for info in sense_nearby_map_infos(buld_srp_location, 8):
        if info.get_paint().is_enemy():
            num_enemy_paint += 1
        if info.is_wall():
            impossible_srp_locations.add(buld_srp_location.x, buld_srp_location.y)
            return

    for ally in sense_nearby_robots(buld_srp_location, 8, get_team()):
        if (
            ally.get_type() == UnitType.SOLDIER
            and ally.get_location().distance_squared_to(buld_srp_location) <= 1
        ):
            num_soldiers_building += 1
        if ally.get_type() == UnitType.MOPPER and get_round_num() >= 100:
            num_enemy_paint -= 3

    if num_enemy_paint > 0 or (
        num_soldiers_building >= 2
        and get_location().distance_squared_to(buld_srp_location) > 1
    ):
        impossible_srp_locations.add(buld_srp_location.x, buld_srp_location.y)
        return

    # pattern = get_resource_pattern()
    # nearby_tiles = sense_nearby_map_infos(buld_srp_location, 8)

    # if can_mark_resource_pattern(buld_srp_location):
    #     mark_resource_pattern(buld_srp_location)

    # for pattern_tile in sense_nearby_map_infos(buld_srp_location, 8):
    #     if pattern_tile.get_mark() != pattern_tile.get_paint() and pattern_tile.get_mark() != PaintType.EMPTY:
    #         use_secondary = pattern_tile.get_mark() == PaintType.ALLY_SECONDARY
    #         if can_attack(pattern_tile.get_map_location()):
    #             attack(pattern_tile.get_map_location(), use_secondary)

    if (
        get_location().distance_squared_to(buld_srp_location) <= 2
        and is_action_ready()
        and can_complete_resource_pattern(buld_srp_location)
    ):
        complete_resource_pattern(buld_srp_location)
        impossible_srp_locations.add(buld_srp_location.x, buld_srp_location.y)
    else:
        paint_srp(buld_srp_location)
