import json

from django.http import HttpResponse

from static_dump.models import MapSolarSystem, MapRegion, Station


def system_name_autocomplete(request):

    if "query" in request.GET:
        search_text = request.GET["query"]
        search_results = list(
            MapSolarSystem.objects.filter(name__startswith=search_text)
            .order_by("name")
            .values_list("name", flat=True)
        )
    else:
        search_text = ""
        search_results = []

    response_text = json.dumps(
        {"query": search_text, "suggestions": search_results}, separators=(",", ":")
    )

    return HttpResponse(response_text)


def station_name_autocomplete(request):

    if "query" in request.GET:
        search_text = request.GET["query"]
        search_results = list(
            Station.objects.filter(name__startswith=search_text)
            .order_by("name")
            .values_list("name", flat=True)
        )
    else:
        search_text = ""
        search_results = []

    response_text = json.dumps(
        {"query": search_text, "suggestions": search_results}, separators=(",", ":")
    )

    return HttpResponse(response_text)


def region_name_autocomplete(request):

    if "query" in request.GET:
        search_text = request.GET["query"]
        search_results = list(
            MapRegion.objects.filter(name__startswith=search_text)
            .order_by("name")
            .values_list("name", flat=True)
        )
    else:
        search_text = ""
        search_results = []

    response_text = json.dumps(
        {"query": search_text, "suggestions": search_results}, separators=(",", ":")
    )

    return HttpResponse(response_text)
