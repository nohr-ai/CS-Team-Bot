import requests
from cachetools import TTLCache, cached


@cached(cache=TTLCache(maxsize=1, ttl=86400))
def get_active_duty():
    """
    Uses countrestrike.fandom.com to get the current active duty map pool.
    A tiny bit of html parsing here.
    Active duty maps are listed bellow "Current Map Pool" header and "Map Pool History" header.
    All are hrefs to additional pages, so we can extract the map name from the href.
    """
    page = requests.get(
        "https://counterstrike.fandom.com/wiki/Category:Active_Duty_Group"
    ).text
    lines = page.splitlines()
    ad = []
    for idx, line in enumerate(lines):
        if "Current Map" in line:
            for line in lines[idx:]:
                if "Map Pool History" in line:
                    return ad
                if 'href="/wiki/' in line:
                    ad.append(line.split('"')[1].removeprefix("/wiki/"))
    # In case counterstrike.fandom changes the page layout
    #  \_O_/
    return ad


if __name__ == "__main__":
    pass
