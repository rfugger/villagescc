from django import template

register = template.Library()

@register.simple_tag
def relative_location(loc, user_loc):
    "Returns a short useful description of `loc` for someone at `user_loc`."
    # In same city if city names are identical and points are within 40km.
    if (loc.city.lower() == user_loc.city.lower() and
        loc.point.distance(user_loc.point) < 40000):
        loc_str = loc.neighborhood
    else:  # Different city.
        if loc.country == user_loc.country:
            if loc.state == user_loc.state:
                loc_str = loc.city
            else:
                loc_str = u"%s, %s" % (loc.city, loc.state)
        else:
            loc_str = u"%s, %s, %s" % (loc.city, loc.state, loc.country)
    return loc_str
