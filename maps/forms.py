from django import forms

from static_dump.forms import (
    SystemNameField,
    RegionNameField,
    MultiSystemNameField,
    MultiRegionNameField,
    StationNameField,
)

security_choices = [
    (1.0, "None"),
    (0.9, "0.9"),
    (0.8, "0.8"),
    (0.7, "0.7"),
    (0.6, "0.6"),
    (0.5, "0.5"),
    (0.4, "0.4"),
    (0.3, "0.3"),
    (0.2, "0.2"),
    (0.1, "0.1"),
    (0.0, "0.0"),
]

origin_type_choices = [("origin_system", "System"), ("origin_station", "Station")]

destination_type_choices = [
    ("destination_system", "System"),
    ("destination_station", "Station"),
    ("destination_region", "Region"),
]

waypoint_type_choices = [
    ("destination_system", "System"),
    ("destination_station", "Station"),
    ("destination_region", "Region"),
]

# a form where some fields are conditionally required
class ConditionalForm(forms.Form):
    def validate_required_field(
        self, cleaned_data, field_name, message="This field is required"
    ):

        if (field_name not in self._errors) and (
            cleaned_data.get(field_name, None) is None
        ):
            self._errors[field_name] = self.error_class(["This field is required"])
            cleaned_data.pop(field_name, None)


class PathForm(ConditionalForm):
    origin_type = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=origin_type_choices,
        initial="origin_system",
        label="Origin",
    )

    origin_system = SystemNameField(required=False)
    origin_station = StationNameField(required=False)

    destination_type = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=destination_type_choices,
        initial="destination_system",
        label="Destination",
    )

    destination_system = SystemNameField(required=False)
    destination_station = StationNameField(required=False)
    destination_region = RegionNameField(required=False)

    use_midpoints = forms.BooleanField(required=False)
    optimize_midpoints = forms.BooleanField(required=False)

    avoid_lowsec = forms.BooleanField(required=False)
    maximum_security = forms.ChoiceField(
        choices=security_choices, label="Avoid Security >"
    )
    avoid_systems = MultiSystemNameField(required=False, widget=forms.Textarea)
    avoid_regions = MultiRegionNameField(required=False, widget=forms.Textarea)

    compute_travel_time = forms.BooleanField(required=False)
    autopilot = forms.BooleanField(required=False)
    align_time = forms.FloatField(required=False, min_value=0.01, max_value=500)
    warp_speed = forms.FloatField(required=False, min_value=0.01, max_value=500)
    ship_speed = forms.FloatField(required=False, min_value=0.01, max_value=5000)

    def __init__(self, *args, **kwargs):
        super(PathForm, self).__init__(*args, **kwargs)

    def clean_maximum_security(self):

        value = self.cleaned_data["maximum_security"]
        if value == "None" or value is None or len(value) == 0:
            return None
        else:
            return float(value)

    def clean(self):
        cleaned_data = super(PathForm, self).clean()

        if "origin_type" in cleaned_data:
            field_name = cleaned_data["origin_type"]
            self.validate_required_field(cleaned_data, field_name)

        if "destination_type" in cleaned_data:
            dest_type = cleaned_data["destination_type"]
            if dest_type == "destination_waypoints":
                if len(self.waypoint_list) == 0:
                    self._errors["destination_type"] = self.error_class(
                        ["At least one waypoint is required."]
                    )
                    del cleaned_data["destination_type"]
            else:
                self.validate_required_field(cleaned_data, dest_type)

        if cleaned_data.get("compute_travel_time", False):
            self.validate_required_field(cleaned_data, "align_time")
            self.validate_required_field(cleaned_data, "warp_speed")
            self.validate_required_field(cleaned_data, "ship_speed")

        return cleaned_data


class WaypointForm(ConditionalForm):
    destination_type = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=waypoint_type_choices,
        initial="destination_system",
        label="Destination",
    )

    destination_system = SystemNameField(required=False)
    destination_station = StationNameField(required=False)
    destination_region = RegionNameField(required=False)

    def clean(self):
        cleaned_data = super(WaypointForm, self).clean()

        if "destination_type" in cleaned_data:
            field_name = cleaned_data["destination_type"]
            self.validate_required_field(cleaned_data, field_name)

        return cleaned_data
