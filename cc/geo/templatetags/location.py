from django import template

register = template.Library()

@register.simple_tag
def relative_location(loc, user_loc):
    "Returns a short useful description of `loc` for someone at `user_loc`."
    # In same city if city names are identical and points are within 40km:
    # Just give neighborhood.
    if (loc.city.lower() == user_loc.city.lower() and
        loc.point.distance(user_loc.point) < 40000):
        loc_str = loc.neighborhood
    else:  # Different city.
        locs = []
        if loc.city:
            locs.append(loc.city)
        if loc.state != user_loc.state or loc.country != user_loc.country:
            if loc.state:
                locs.append(loc.state)
        if loc.country != user_loc.country:
            locs.append(loc.country)  # Country can't be blank.
        loc_str = ', '.join(locs)
    return loc_str
