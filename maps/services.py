from static_dump.models import MapSolarSystem, MapRegion, Station, GraphNode

from static_dump import dump_manager
from math_utils import travel_time
from math_utils import search

one_au = 150000000000
gate_manager = dump_manager.GateWarpManager()


def get_origin_states(data_dict):

    origin_type = data_dict["origin_type"]

    if origin_type == "origin_system":
        return set(
            GraphNode.objects.filter(
                system__name=data_dict["origin_system"]
            ).values_list("id", flat=True)
        )

    elif origin_type == "origin_station":
        return {
            Station.objects.values_list("id", flat=True).get(
                name=data_dict["origin_station"]
            )
        }

    else:
        raise ValueError("Invalid origin type")


def get_destination_states(data_dict):
    destination_type = data_dict["destination_type"]

    if destination_type == "destination_system":
        return set(
            GraphNode.objects.filter(
                system__name=data_dict["destination_system"]
            ).values_list("id", flat=True)
        )

    elif destination_type == "destination_station":
        return {
            Station.objects.values_list("id", flat=True).get(
                name=data_dict["destination_station"]
            )
        }

    elif destination_type == "destination_region":
        return set(
            GraphNode.objects.filter(
                system__region__name=data_dict["destination_region"]
            ).values_list("id", flat=True)
        )

    else:
        raise ValueError("Invalid destination type")


def get_avoided_systems(data_dict):
    avoided_systems = set(data_dict["avoid_systems"])
    avoided_regions = data_dict["avoid_regions"]

    return avoided_systems | set(
        MapSolarSystem.objects.filter(region_id__in=avoided_regions).values_list(
            "id", flat=True
        )
    )


def compute_travel_path(data_dict):

    total_path = []

    origin_states = get_origin_states(data_dict)

    if data_dict["use_midpoints"] and len(data_dict["waypoint_list"]) > 0:

        result_path = []

        # the user has selected multiple waypoints, so we need to travel down the list
        for destination in data_dict["waypoint_list"]:
            waypoint_dict = {"destination_type": destination["type"]}

            # the get_destination_states method is expecting a dictionary key with the same name as the value of destination_type
            waypoint_dict[destination["type"]] = destination["name"]

            destination_states = get_destination_states(waypoint_dict)

            waypoint_list, waypoint_time, waypoint_error = compute_waypoint_path(
                origin_states, destination_states, data_dict
            )

            if len(waypoint_list) == 0:
                break

            # determine the name of the waypoint for display purposes
            if destination["type"] == "destination_region":
                type_name = "Region"
            elif destination["type"] == "destination_station":
                type_name = "Station"
            elif destination["type"] == "destination_system":
                type_name = "System"

            waypoint_dict = {
                "type": type_name,
                "name": destination["name"],
                "jumps": len(waypoint_list),
                "error": waypoint_error,
                "time": waypoint_time,
                "path": waypoint_list,
            }

            total_path.append(waypoint_dict)

            # the next cycle should start where this cycle stopped
            origin_states = set([waypoint_list[-1]["state_id"]])

    # compute the path from the most recent waypoint to the destination
    destination_states = get_destination_states(data_dict)
    waypoint_list, waypoint_time, waypoint_error = compute_waypoint_path(
        origin_states, destination_states, data_dict
    )

    # determine the name of the waypoint for display purposes
    if data_dict["destination_type"] == "destination_region":
        type_name = "Region"
        destination_name = data_dict["destination_region"]
    elif data_dict["destination_type"] == "destination_station":
        type_name = "Station"
        destination_name = data_dict["destination_station"]
    elif data_dict["destination_type"] == "destination_system":
        type_name = "System"
        destination_name = data_dict["destination_system"]

    waypoint_dict = {
        "type": type_name,
        "name": destination_name,
        "jumps": len(waypoint_list),
        "error": waypoint_error,
        "time": waypoint_time,
        "path": waypoint_list,
    }
    total_path.append(waypoint_dict)

    # compute stats for the final resulting path
    total_length = sum(p["jumps"] for p in total_path)
    if data_dict["compute_travel_time"]:
        total_error = sum(p["error"] for p in total_path if p["error"] is not None)
        total_time = sum(p["time"] for p in total_path if p["time"] is not None)
    else:
        total_error = None
        total_time = None

    return total_path, total_length, total_time, total_error


def compute_waypoint_path(origin_states, destination_states, data_dict):

    avoid_lowsec = data_dict["avoid_lowsec"]
    maximum_security = data_dict["maximum_security"]
    avoided_systems = get_avoided_systems(data_dict)

    if data_dict["compute_travel_time"]:
        # the provided warp speed is in au/s, we need to convert it to m/s
        warp_speed = one_au * data_dict["warp_speed"]
        ship_speed = data_dict["ship_speed"]
        align_time = data_dict["align_time"]
    else:
        warp_speed = one_au * 3
        ship_speed = 150
        align_time = 5

    duration_func = get_travel_duration_func(
        align_time, ship_speed, warp_speed, data_dict["autopilot"]
    )

    # compute the shortest path. do not compute it if the destination systems are a subset of the avoided systems
    if destination_states < avoided_systems:
        return []

    def goal_func(state_id):
        return state_id in destination_states

    # create a function to return the valid neighbors of a given state
    def neighbor_func(state_id):
        new_states = gate_manager.get_neighbors(state_id)

        result = list()
        for state_id, distance in new_states:
            system_id, system_security = gate_manager.get_node(state_id)

            if system_id not in avoided_systems:
                system_security = round(system_security, 1) - 0.01

                if distance is None:
                    cost = 10  # 10 seconds to jump from one system to another

                else:
                    cost = duration_func(distance)

                if maximum_security is not None and system_security > maximum_security:
                    cost *= 1000
                elif system_security < 0.45 and avoid_lowsec:
                    cost *= 1000

                result.append((state_id, cost))

        return result

    path = search.uniform_cost_search(origin_states, goal_func, neighbor_func)
    path = gate_manager.trace_path(path)

    if data_dict["compute_travel_time"]:
        error = compute_travel_error(data_dict, path)

        for p in path:
            if p["distance"]:
                p["travel_time"] = duration_func(p["distance"])
            else:
                p["travel_time"] = 0

        path_time = sum(p["travel_time"] for p in path)

    else:
        error = None
        path_time = None

    return path, path_time, error


# given a list of adjancent systems representing a path, returns a list containing the travel time for each system
def compute_travel_error(data_dict, path):

    base_error = 5
    if data_dict["autopilot"]:
        # the landing point is random within a small sphere of the "theoretical" landing point
        # we're going to do some fudge math to get a rough estimate of the standard deviation,
        # then we assume that all landings will occur within 2 standard deviations, then muliply by the number of landings we have to make in order to estimate the total error
        min_approach = travel_time.compute_approach_time(
            11000, data_dict["ship_speed"], data_dict["align_time"]
        )
        max_approach = travel_time.compute_approach_time(
            14000, data_dict["ship_speed"], data_dict["align_time"]
        )

        standard_dev = (max_approach - min_approach) / 3.45

        base_error += standard_dev * 2

    return base_error * (len(path) - 1)


"""
===============
Utility functions to be used inside of dijkstra's search
===============
"""


# this function returns a function that takes a distance and returns the time taken to travel that distance, given the parameters supplied here
def get_travel_duration_func(align_time, ship_speed, warp_speed, is_autopilot):

    if is_autopilot:
        times = {
            "wait_begin": 9,
            "wait_align": 1,
            "align": align_time,
            "wait_approach": 3,
            "approach": travel_time.compute_approach_time(
                12500, ship_speed, align_time
            ),
        }
    else:
        times = {
            "wait_begin": 4,
            "wait_align": 1,
            "align": align_time,
            "wait_approach": 0,
            "approach": 1,
        }

    non_warp_time = sum(times.values())

    def compute_travel_duration(distance):
        return non_warp_time + travel_time.compute_warp_time(
            distance, ship_speed, warp_speed
        )

    return compute_travel_duration
