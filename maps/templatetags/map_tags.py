from django import template

register = template.Library()


@register.filter
def securityClass(value):

    if value is None:
        return ""

    sec = round(value, 1)

    if sec > 0.95:
        return "securityOne"
    if sec > 0.85:
        return "pointNine"
    if sec > 0.75:
        return "pointEight"
    if sec > 0.65:
        return "pointSeven"
    if sec > 0.55:
        return "pointSix"
    if sec > 0.45:
        return "pointFive"
    if sec > 0.35:
        return "pointFour"
    if sec > 0.25:
        return "pointThree"
    if sec > 0.15:
        return "pointTwo"
    if sec > 0.05:
        return "pointOne"

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

    if remaining_minutes > 0:
        return "%dm %ds" % (remaining_minutes, remaining_seconds)

    if remaining_seconds > 0:
        return "%ds" % (remaining_seconds)

    return "-"
