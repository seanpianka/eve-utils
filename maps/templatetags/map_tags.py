from django import template

register = template.Library()


@register.filter
def securityClass(value):

    if value is None:
        return ""
    else:
        sec = round(value, 1)

        if sec > 0.95:
            return "securityOne"
        elif sec > 0.85:
            return "pointNine"
        elif sec > 0.75:
            return "pointEight"
        elif sec > 0.65:
            return "pointSeven"
        elif sec > 0.55:
            return "pointSix"
        elif sec > 0.45:
            return "pointFive"
        elif sec > 0.35:
            return "pointFour"
        elif sec > 0.25:
            return "pointThree"
        elif sec > 0.15:
            return "pointTwo"
        elif sec > 0.05:
            return "pointOne"
        else:
            return "securityZero"


@register.filter
def format_seconds(value):

    if value is None:
        return None

    seconds = int(round(value, 1))
    minutes = seconds / 60
    remaining_seconds = seconds % 60

    hours = minutes / 60
    remaining_minutes = minutes % 60

    if hours > 0:
        return "%dh %dm %ds" % (hours, remaining_minutes, remaining_seconds)
    else:
        if remaining_minutes > 0:
            return "%dm %ds" % (remaining_minutes, remaining_seconds)
        else:
            if remaining_seconds > 0:
                return "%ds" % (remaining_seconds)
            else:
                return "-"
