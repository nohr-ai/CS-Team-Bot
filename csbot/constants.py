"""
Ranks changed dramatically with the release of CS2.
Ranks are now any integer >= 0.
The titles are just rough estimate of equivalent rank in csgo.
"""

ranks = {
    0: "Silver I",
    2800: "Silver II",
    3800: "Silver III",
    4200: "Silver IV",
    4700: "Silver Elite",
    4999: "Silver Elite Master",
    5600: "Gold Nova I",
    6500: "Gold Nova II",
    7400: "Gold Nova III",
    8400: "Gold Nova Master",
    9400: "Master Guardian I",
    10000: "Master Guardian II",
    10900: "Master Guardian Elite",
    12000: "DMG",
    13100: "Legendary Eagle",
    14200: "Legendary Eagle Master",
    15500: "Supreme Master First Class",
    18000: "Global Elite",
}

# Default team size for competitive cs2 is 5
team_size = 5
# Set limit for amount of times rolling for an optimal team
team_roll_limit = 100
