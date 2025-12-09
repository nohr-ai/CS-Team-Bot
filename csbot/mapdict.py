from __future__ import annotations
import csgo
import logging
import traceback
from copy import deepcopy


class MapDict(dict):
    def amplify_most_wanted(self):
        """
        Amplify the top 3 most wanted maps by a factor of 16, 8, and 4.
        Map preferences weigh more than ranks for team composition.
        """
        factor = len(self.keys())
        weights = [16 * factor, 8 * factor, 4 * factor]
        nmaps = 3
        top_n = self.top_n_maps(nmaps)
        for i, map in enumerate(top_n):
            self[map] *= weights[i]

    def remove_banned_maps(self, banned_maps):
        logger = logging.getLogger(f"{self.__class__.__name__}")
        for banned_map in banned_maps:
            try:
                del self[banned_map]
            except NameError as e:
                logger.debug(traceback.TracebackException.from_exception(e).format())
                logger.exception(
                    f"Tried banning {banned_map} not found in available maps."
                )

    def remove_picked_maps(self, picked_maps):
        logger = logging.getLogger(f"{self.__class__.__name__}")
        for picked_map in picked_maps:
            try:
                del self[picked_map]
            except NameError as e:
                logger.debug(traceback.TracebackException.from_exception(e).format())
                logger.exception(
                    f"Tried picking {picked_map} not found in available maps."
                )

    def from_list(self, list) -> MapDict:
        for i, map in enumerate(list):
            self[map] = i
        return self

    def to_list(self):
        return list(self)

    def update_from_list(self, list):
        for i, map in enumerate(list):
            self[map] = i

    def to_list_sorted(self, reverse=False) -> list:
        """
        Return a list of maps sorted by their rank.
        """
        return sorted(self, key=self.get, reverse=reverse)

    def top_n_maps(self, n=len(csgo.get_active_duty())):
        """
        Return the top n maps by ranking.

        PARAMETERS
        ----------
        n : int
            The number of maps to return.

        RETURNS
        -------
        list
            The top n maps by ranking.
        """
        return sorted(self, key=self.get, reverse=True)[:n]

    def copy(self) -> MapDict:
        """
        Return a copy of the MapDict.
        """
        return deepcopy(self)
