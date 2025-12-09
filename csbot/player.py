import constants
import random

from csgo import get_active_duty
from helperfunctions import euclidean_distance, DiscordString
from mapdict import MapDict


class Player:
    """
    Main object for Counter-Strike players

    :param id: The unique identifier for the player
    :param name: The name of the player
    :param display_name: The display name of the player
    :param rank: The rank of the player
    :param title: The title of the player
    :param matches: The number of matches the player has played
    :param maps: The map preferences of the player
    :param igl: Whether the player is the in-game leader

    """

    def __init__(self, id, name, display_name):
        self.id = id
        self.display_name = display_name
        self.steam_id = None
        self.liga_id = None
        self.name = name
        self.rank = 0
        self.title = constants.ranks[self.rank]
        self.matches = 0
        self.maps = MapDict().from_list(get_active_duty())
        self.igl = False

    def set_igl(self, val: bool):
        self.igl = val

    def set_rank(self, rank: int):
        """
        Set the rank of the player and update the title
        """
        if rank < 0:
            rank = 0
        self.rank = rank
        title = None
        for r in sorted(constants.ranks.keys(), key=int):
            if r <= int(rank):
                title = constants.ranks[r]
            else:
                break
        self.title = title

    def rank_map(self, map, rank):
        if rank < 0:
            rank = 0
        if rank > len(self.maps) - 1:
            rank = len(self.maps) - 1
        self.maps[map] = rank

    def get_map_ranking(self) -> str:
        ranking = ""
        for map, value in self.maps.items():
            ranking += f"{map}: {value}\n"
        return ranking

    def map_order(self) -> DiscordString:
        order = DiscordString("| ")
        for map in self.maps.to_list_sorted():
            order += f"{map} | "
        return order.to_code_inline()

    def get_info(self):
        s = f"{self.name} is rank {self.rank} and has map order: "
        s += self.map_order()
        return s

    def update_maps(self, maps: list):
        self.maps.update_from_list(maps)

    def rank_compatability(self, player) -> float:
        return euclidean_distance(self.rank, player.rank)

    def map_compatability(self, player) -> float:
        diff = 0
        for map in get_active_duty():
            diff += euclidean_distance(self.maps[map], player.maps[map])
        return diff

    def generate_random(id=random.randint(0, 0xFFFFFFFF)):
        player = Player(id, str(id))
        player.rank = random.randint(1, 18)
        player.maps = {}
        map_pool = random.sample(get_active_duty(), k=len(get_active_duty()))
        for i, map in enumerate(map_pool):
            player.maps[map] = i

        return player


### TESTS


def test_player_init():
    """
    Test player initialization
    """
    import uuid

    expected_id = int(uuid.uuid4())
    expected_name = "test"
    expected_display_name = "test_display_name"
    expected_rank = 0
    expected_title = constants.ranks[0]
    expected_matches = 0
    expected_maps = MapDict().from_list(get_active_duty())
    expected_igl = False
    player = Player(expected_id, expected_name, expected_display_name)
    assert player.id == expected_id, "Player id should be the same as the input id"
    assert isinstance(player.name, str), "Name should be a string"
    assert (
        player.name == expected_name
    ), "Player name should be the same as the input name"
    assert isinstance(player.display_name, str), "Display name should be a string"
    assert (
        player.display_name == expected_display_name
    ), "Player display name should be the same as the input display name"
    assert isinstance(player.rank, int), "Rank should be an integer"
    assert player.rank == expected_rank, "Player rank should default to 0"
    assert isinstance(player.title, str), "Title should be a string"
    assert player.title == expected_title, "Player title should default to Silver I"
    assert isinstance(player.matches, int), "Matches should be an integer"
    assert player.matches == expected_matches, "Player matches should default to 0"
    assert isinstance(player.maps, MapDict), "Maps should be a MapDict object"
    assert player.maps == expected_maps, "Player maps should default to the active duty"
    assert isinstance(player.igl, bool), "IGL should be a boolean"
    assert player.igl == expected_igl, "Player IGL should default to False"


def test_player_set_igl():
    """
    Test setting the IGL status of a player
    """
    player = Player(0, "test", "test_display_name")
    assert player.igl == False, "IGL should default to False"
    player.set_igl(True)
    assert player.igl == True, "IGL should be set to True"
    player.set_igl(False)
    assert player.igl == False, "IGL should be set to False"


def test_player_set_rank():
    """
    Test setting the rank of a player
    """
    player = Player(0, "test", "test_display_name")
    assert player.rank == 0, "Rank should default to 0"
    new_rank = 2800
    player.set_rank(new_rank)
    assert player.rank == new_rank, f"Rank should be set to {new_rank}"
    assert (
        player.title == constants.ranks[new_rank]
    ), f"Title should be set to {constants.ranks[new_rank]}"
    new_rank = 14200
    player.set_rank(new_rank)
    assert player.rank == new_rank, f"Rank should be set to {new_rank}"
    assert (
        player.title == constants.ranks[new_rank]
    ), f"Title should be set to {constants.ranks[new_rank]}"
    max_rank = max(constants.ranks.keys())
    new_rank = max_rank + 1
    player.set_rank(new_rank)
    assert player.rank == new_rank, f"Rank should be set to {new_rank}"
    assert (
        player.title == f"{constants.ranks[max_rank]}"
    ), f"Title should be {constants.ranks[max_rank]}"

    min_rank = min(constants.ranks.keys())
    new_rank = min_rank - 1
    player.set_rank(new_rank)
    assert player.rank == min_rank, f"Rank should be set to {min_rank}"
    assert (
        player.title == constants.ranks[min_rank]
    ), f"Title should be {constants.ranks[min_rank]}"


def test_player_rank_map():
    """
    Test setting the rank of a map for a player
    """
    player = Player(0, "test", "test_display_name")
    map = "Mirage"
    rank = 0
    player.rank_map(map, rank)
    assert player.maps[map] == rank, f"Map rank should be set to {rank}"
    rank = 1
    player.rank_map(map, rank)
    assert player.maps[map] == rank, f"Map rank should be set to {rank}"
    rank = 6
    player.rank_map(map, rank)
    assert player.maps[map] == rank, f"Map rank should be set to {rank}"
    rank = -1
    player.rank_map(map, rank)
    assert player.maps[map] == 0, "Map rank should not be set to a negative value"
    rank = 100
    player.rank_map(map, rank)
    assert (
        player.maps[map] == len(player.maps) - 1
    ), "Map rank should not exceed the number of maps"


def test_player_get_map_ranking():
    """
    Test getting the map rankings of a player
    """
    player = Player(0, "test", "test_display_name")
    expected_ranking = ""
    for r, map in enumerate(get_active_duty()):
        expected_ranking += f"{map}: {r}\n"
    assert (
        player.get_map_ranking() == expected_ranking
    ), f"Map ranking should be initialized in order [0-{len(player.maps)-1}]"


def test_player_map_order():
    """
    Test getting the map order of a player
    """
    player = Player(0, "test", "test_display_name")
    expected_order = DiscordString("| ")
    for map in get_active_duty():
        expected_order += f"{map} | "
    assert (
        player.map_order() == expected_order.to_code_inline()
    ), "Map order should be initialized in order[0-7]"


def test_player_get_info():
    """
    Test getting the info of a player
    """
    player = Player(0, "test", "test_display_name")
    expected_info = (
        f"{player.name} is rank {player.rank} and has map order: {player.map_order()}"
    )
    assert (
        player.get_info() == expected_info
    ), "Player info should be formatted correctly"


def test_player_update_maps():
    """
    Test updating the map preferences of a player
    """
    player = Player(0, "test", "test_display_name")
    maps = ["Mirage", "Inferno", "Anubis", "Overpass", "Ancient", "Nuke", "Vertigo"]
    player.update_maps(maps)
    assert (
        player.maps.to_list_sorted() == maps[::-1]
    ), "Map preferences should be updated"
