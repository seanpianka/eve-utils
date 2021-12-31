import math
from collections import defaultdict

from static_dump.models import MapSolarSystem, MapRegion, Station, GraphNode, GraphEdge


# this class will query and manage relationships between systems, stored
# by gate warp
class GateWarpManager:

    # map from node_id to system id
    _nodes = dict()

    # map from node id to dict: destination node id as key, distance as value
    _edges = dict()

    # map from system id to system info: name, constellation name, region
    # name, sec status
    _systems = dict()

    # map from station id to station name
    _stations = dict()

    def __init__(self):
        node_query = GraphNode.objects.values_list(
            "id", "system_id", "system__security_level"
        )
        self._nodes = {
            node_id: (system_id, security)
            for (node_id, system_id, security) in node_query
        }

        edge_query = GraphEdge.objects.values_list(
            "origin_id", "destination_id", "distance"
        )
        self._edges = defaultdict(dict)
        for (origin_id, destination_id, distance) in edge_query:
            self._edges[origin_id][destination_id] = distance

        system_query = MapSolarSystem.objects.select_related(
            "constellation", "region"
        ).values_list("id", "name", "constellation__name", "region__name")
        self._systems = {
            system_id: (name, const_name, region_name)
            for (system_id, name, const_name, region_name) in system_query
        }

        station_query = Station.objects.values_list("id", "name")
        self._stations = {station_id: name for (station_id, name) in station_query}

    def get_node(self, node_id):
        return self._nodes[node_id]

    def get_neighbors(self, current_state):
        return list(self._edges[current_state].items())

    def trace_path(self, state_list):

        # do this in two passes - in the first pass, convert from the state
        # list to an intermediate list of states

        # action_list contains 2-tuples, the first item is where you end up after the action
        # the second item is the warp distance to get there
        action_list = []
        if len(state_list) > 0:
            prev_state = state_list[0]

        for current_state in state_list[1:]:
            distance = self._edges[prev_state][current_state]

            # on the first element, we want to add the entry no matter what. on
            # subsequent entries we only want to add some of them
            if len(action_list) == 0:
                action_list.append([current_state, distance])
            else:

                # if distance is None, this is a gate jump. instead of adding this to the list, modify the previous entry's "current state"
                # in effect, we're combining the previous warp and this jump into one
                # action
                if distance is None:
                    action_list[-1][0] = current_state
                else:
                    action_list.append([current_state, distance])

            prev_state = current_state

        # convert the action list into a list of path nodes
        path = []
        for destination_node, distance in (tuple(entry) for entry in action_list):

            system_id, security = self._nodes[destination_node]
            location_name, constellation_name, region_name = self._systems[system_id]

            # if the destination is actually a station, overwrite the location name
            # with the station name
            if destination_node in self._stations:
                location_name = self._stations[destination_node]

            path.append(
                {
                    "location": location_name,
                    "state_id": destination_node,
                    "constellation": constellation_name,
                    "region": region_name,
                    "security_level": security,
                    "distance": distance,
                }
            )

        return path
