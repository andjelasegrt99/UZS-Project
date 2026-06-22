def hm(hour, minute):
    return hour * 60 + minute


def make_trip(tid, s_station, e_station, start, end):
    return {
        'id': tid,
        'start_station': s_station,
        'end_station': e_station,
        'start': start,
        'end': end,
        'duration': end - start
    }


def _format_minutes(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def describe_instance(instance):
    trips = instance['trips']
    stations = sorted({
        trip['start_station'] for trip in trips
    } | {
        trip['end_station'] for trip in trips
    })
    first_start = min(trip['start'] for trip in trips)
    last_end = max(trip['end'] for trip in trips)
    average_duration = sum(trip['duration'] for trip in trips) / len(trips)

    return {
        'num_trips': len(trips),
        'num_stations': len(stations),
        'stations': stations,
        'time_span': f"{_format_minutes(first_start)}-{_format_minutes(last_end)}",
        'average_trip_duration': average_duration,
    }


def small_instance():
    trips = [
        make_trip('T1', 'A', 'B', hm(8, 0), hm(9, 0)),
        make_trip('T2', 'B', 'C', hm(9, 20), hm(10, 10)),
        make_trip('T3', 'C', 'D', hm(10, 30), hm(11, 30)),
        make_trip('T4', 'B', 'A', hm(9, 50), hm(10, 40)),
        make_trip('T5', 'A', 'C', hm(11, 0), hm(12, 0)),
        make_trip('T6', 'C', 'B', hm(12, 30), hm(13, 15)),
    ]
    return {'trips': trips}


def medium_instance():
    stations = [
        'Beograd Centar',
        'Novi Beograd',
        'Zemun',
        'Batajnica',
        'Nova Pazova',
        'Stara Pazova',
        'Indjija',
        'Sremski Karlovci',
        'Petrovaradin',
        'Novi Sad',
    ]

    trips = [
        make_trip('M1', stations[0], stations[1], hm(6, 0), hm(6, 14)),
        make_trip('M2', stations[1], stations[2], hm(6, 32), hm(6, 44)),
        make_trip('M3', stations[2], stations[3], hm(7, 0), hm(7, 14)),
        make_trip('M4', stations[3], stations[4], hm(7, 32), hm(7, 46)),
        make_trip('M5', stations[4], stations[5], hm(8, 2), hm(8, 14)),
        make_trip('M6', stations[5], stations[6], hm(8, 32), hm(8, 47)),
        make_trip('M7', stations[6], stations[7], hm(9, 5), hm(9, 19)),
        make_trip('M8', stations[7], stations[8], hm(9, 36), hm(9, 47)),
        make_trip('M9', stations[8], stations[9], hm(10, 5), hm(10, 17)),

        make_trip('M10', stations[9], stations[8], hm(6, 20), hm(6, 32)),
        make_trip('M11', stations[8], stations[7], hm(6, 50), hm(7, 1)),
        make_trip('M12', stations[7], stations[6], hm(7, 18), hm(7, 32)),
        make_trip('M13', stations[6], stations[5], hm(7, 50), hm(8, 5)),
        make_trip('M14', stations[5], stations[4], hm(8, 21), hm(8, 33)),
        make_trip('M15', stations[4], stations[3], hm(8, 50), hm(9, 4)),
        make_trip('M16', stations[3], stations[2], hm(9, 22), hm(9, 36)),
        make_trip('M17', stations[2], stations[1], hm(9, 52), hm(10, 4)),
        make_trip('M18', stations[1], stations[0], hm(10, 20), hm(10, 35)),

        make_trip('M19', stations[0], stations[2], hm(11, 0), hm(11, 28)),
        make_trip('M20', stations[2], stations[3], hm(11, 43), hm(11, 57)),
        make_trip('M21', stations[3], stations[5], hm(12, 20), hm(12, 45)),
        make_trip('M22', stations[5], stations[9], hm(13, 5), hm(13, 50)),
        make_trip('M23', stations[9], stations[5], hm(11, 10), hm(11, 55)),
        make_trip('M24', stations[5], stations[3], hm(12, 12), hm(12, 37)),
        make_trip('M25', stations[3], stations[1], hm(12, 45), hm(13, 10)),
        make_trip('M26', stations[1], stations[0], hm(13, 28), hm(13, 43)),

        make_trip('M27', stations[0], stations[1], hm(16, 0), hm(16, 14)),
        make_trip('M28', stations[1], stations[3], hm(16, 32), hm(16, 55)),
        make_trip('M29', stations[3], stations[6], hm(17, 20), hm(17, 55)),
        make_trip('M30', stations[6], stations[9], hm(18, 15), hm(19, 0)),

        make_trip('M31', stations[9], stations[6], hm(16, 10), hm(16, 55)),
        make_trip('M32', stations[6], stations[3], hm(17, 12), hm(17, 47)),
        make_trip('M33', stations[3], stations[1], hm(18, 5), hm(18, 28)),
        make_trip('M34', stations[1], stations[0], hm(18, 45), hm(18, 59)),
    ]

    return {'trips': trips}


def _validate_medium_instance(instance):
    description = describe_instance(instance)
    if description['num_stations'] != 10:
        raise ValueError(
            f"Srednja instanca mora imati tacno 10 stanica, a ima {description['num_stations']}."
        )
    if description['num_trips'] < 25:
        raise ValueError(
            f"Srednja instanca mora imati najmanje 25 voznji, a ima {description['num_trips']}."
        )


def get_instances():
    instances = {'small': small_instance(), 'medium': medium_instance()}
    _validate_medium_instance(instances['medium'])
    return instances
