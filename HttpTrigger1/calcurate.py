def nearest_garbage(locations, cur_location):
    min_dis = 100000000
    for location in locations:
        latitude = location[3] - cur_location[0]
        longitude = location[4] - cur_location[1]
        distance = latitude*latitude + longitude*longitude
        if min_dis > distance:
            min_dis = distance
            nearest_location = location

    return nearest_location