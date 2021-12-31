import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from maps.forms import PathForm, WaypointForm
from maps.services import compute_travel_path

from static_dump.models import MapRegion, MapSolarSystem, Station


class WaypointValidationException(Exception):
    pass


def shortest_path(request):
    path = None
    path_time = None
    path_error = None
    path_length = None

    waypoint_list = request.session.get("waypoint_list", [])

    if len(request.GET) > 0:
        path_form = PathForm(request.GET)

        if path_form.is_valid():
            path_form.cleaned_data["waypoint_list"] = waypoint_list

            # path is a list of dictionaries - each dict is a waypoint, containing the time to travel that leg, and the path inside
            path, path_length, path_time, path_error = compute_travel_path(
                path_form.cleaned_data
            )

            # store the search data in the session for the next request
            request.session["shortest_path_form_data"] = request.GET

    else:
        # if the session has stored data, load it
        shortest_path_initial = request.session.get("shortest_path_form_data", {})
        path_form = PathForm(initial=shortest_path_initial)

    # to make it easier to display the destination types, zip them up here
    origin_types = zip(
        path_form["origin_type"],
        [path_form["origin_system"], path_form["origin_station"]],
    )

    # to make it easier to display the destination types, zip them up here
    destination_types = zip(
        path_form["destination_type"],
        [
            {"field": path_form["destination_system"]},
            {"field": path_form["destination_station"]},
            {"field": path_form["destination_region"]},
        ],
    )

    return render_to_response(
        "maps/shortest_path.html",
        {
            "path_form": path_form,
            "destination_types": destination_types,
            "origin_types": origin_types,
            "waypoint_list": waypoint_list,
            "path": path,
            "path_length": path_length,
            "path_time": path_time,
            "path_error": path_error,
        },
        context_instance=RequestContext(request),
    )


@ensure_csrf_cookie
def manage_waypoints(request):

    waypoint_list = request.session.get("waypoint_list", [])

    waypoint_form = WaypointForm()

    # to make it easier to display the destination types, zip them up here
    destination_types = zip(
        waypoint_form["destination_type"],
        [
            waypoint_form["destination_system"],
            waypoint_form["destination_station"],
            waypoint_form["destination_region"],
        ],
    )

    context_inst = RequestContext(request)

    # render the waypoint form first. we're doing it this way to keep it consistent with the ajax method that will send and updated version of the form
    waypoint_form_str = render_to_string(
        "include/waypoint_form.html",
        {"form": waypoint_form, "destination_types": destination_types},
        context_instance=context_inst,
    )

    return render_to_response(
        "maps/manage_waypoints.html",
        {"waypoint_list": waypoint_list, "waypoint_form_str": waypoint_form_str},
        context_instance=context_inst,
    )


def add_waypoint(request):

    waypoint_form = WaypointForm(request.GET)
    if waypoint_form.is_valid():

        response_data = {}
        response_data["type"] = waypoint_form.cleaned_data["destination_type"]

        if response_data["type"] == "destination_system":

            system = MapSolarSystem.objects.values("id", "name", "security_level").get(
                name=waypoint_form.cleaned_data["destination_system"]
            )

            response_data["id"] = system["id"]
            response_data["name"] = system["name"]
            response_data["security"] = system["security_level"]

        elif response_data["type"] == "destination_station":

            station = Station.objects.values(
                "id", "name", "solar_system__security_level"
            ).get(name=waypoint_form.cleaned_data["destination_station"])

            response_data["id"] = station["id"]
            response_data["name"] = station["name"]
            response_data["security"] = station["solar_system__security_level"]

        elif response_data["type"] == "destination_region":

            region = MapRegion.objects.values("id", "name").get(
                name=waypoint_form.cleaned_data["destination_region"]
            )

            response_data["id"] = region["id"]
            response_data["name"] = region["name"]
            response_data["security"] = None

        # render the waypoint entry template
        context_inst = RequestContext(request)
        response_text = render_to_string(
            "include/waypoint_entry.html",
            {"point": response_data, "num": -1},
            context_instance=context_inst,
        )

        result = {"success": True, "response": response_text}
        return HttpResponse(json.dumps(result))
    else:

        # to make it easier to display the destination types, zip them up here
        destination_types = zip(
            waypoint_form["destination_type"],
            [
                waypoint_form["destination_system"],
                waypoint_form["destination_station"],
                waypoint_form["destination_region"],
            ],
        )

        # render the waypoint form in order to display any errors and return it
        context_inst = RequestContext(request)
        response_text = render_to_string(
            "include/waypoint_form.html",
            {"form": waypoint_form, "destination_types": destination_types},
            context_instance=context_inst,
        )

        result = {"success": False, "response": response_text}
        return HttpResponse(json.dumps(result))


def save_waypoints(request):

    if request.method == "POST" and "waypoints" in request.POST:

        try:
            waypoint_list = json.loads(request.POST["waypoints"])

            # gather sets of region, system, and station ids just to verify that they're all valid
            region_set = set()
            system_set = set()
            station_set = set()

            for item in waypoint_list:
                object_id = int(item["id"])
                if item["type"] == "destination_region":
                    region_set.add(object_id)
                elif item["type"] == "destination_system":
                    system_set.add(object_id)
                elif item["type"] == "destination_station":
                    station_set.add(object_id)
                else:
                    raise WaypointValidationException()

            system_dict = MapSolarSystem.objects.in_bulk(system_set)
            station_dict = Station.objects.select_related("system").in_bulk(station_set)
            region_dict = MapRegion.objects.in_bulk(region_set)

            # if any of the waypoints were not found, raise an error
            if (
                len(system_dict) < len(system_set)
                or len(system_dict) < len(system_set)
                or len(system_dict) < len(system_set)
            ):
                raise WaypointValidationException()

            saved_waypoints = []

            # go through the list of waypoints and use the dictionaries to clean and store the data
            for item in waypoint_list:
                object_id = int(item["id"])
                if item["type"] == "destination_region":
                    region = region_dict[object_id]
                    saved_waypoints.append(
                        {
                            "type": "destination_region",
                            "id": region.id,
                            "name": region.name,
                            "security": None,
                        }
                    )

                elif item["type"] == "destination_system":
                    system = system_dict[object_id]
                    saved_waypoints.append(
                        {
                            "type": "destination_system",
                            "id": system.id,
                            "name": system.name,
                            "security": system.security_level,
                        }
                    )

                else:
                    station = station_dict[object_id]
                    saved_waypoints.append(
                        {
                            "type": "destination_station",
                            "id": station.id,
                            "name": station.name,
                            "security": station.solar_system.security_level,
                        }
                    )

            request.session["waypoint_list"] = saved_waypoints

            result_url = reverse("maps.shortest_path")
            return HttpResponse(json.dumps({"success": True, "response": result_url}))

        except WaypointValidationException:
            return HttpResponse(json.dumps({"success": False, "response": ""}))
    else:
        raise Http404()
