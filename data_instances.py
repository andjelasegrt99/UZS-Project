# Funkcija koja pretvara sate i minute u ukupan broj minuta od 00:00
def hm(hour, minute):
    return hour * 60 + minute


# Funkcija koja pravi jedan zapis o vožnji
def make_trip(tid, s_station, e_station, start, end):
    return {
        'id': tid,                           # Identifikator vožnje
        'start_station': s_station,          # Polazna stanica
        'end_station': e_station,            # Odredišna stanica
        'start': start,                      # Vreme polaska (u minutima)
        'end': end,                          # Vreme dolaska (u minutima)
        'duration': end - start              # Trajanje vožnje
    }


# Funkcija koja pretvara ukupan broj minuta u format HH:MM
def _format_minutes(total_minutes):
    hours = total_minutes // 60             # Izračunavanje broja sati
    minutes = total_minutes % 60            # Izračunavanje preostalih minuta

    # Formatiranje u obliku npr. 08:05
    return f"{hours:02d}:{minutes:02d}"


# Funkcija koja opisuje celu instancu
def describe_instance(instance):

    # Uzimaju se sve vožnje
    trips = instance['trips']

    # Pronalaze se sve jedinstvene stanice
    stations = sorted({
        trip['start_station'] for trip in trips
    } | {
        trip['end_station'] for trip in trips
    })

    # Najranije vreme polaska
    first_start = min(trip['start'] for trip in trips)

    # Najkasnije vreme završetka vožnje
    last_end = max(trip['end'] for trip in trips)

    # Prosečno trajanje svih vožnji
    average_duration = sum(
        trip['duration'] for trip in trips
    ) / len(trips)

    # Vraća opis instance
    return {
        'num_trips': len(trips),                         # Broj vožnji
        'num_stations': len(stations),                  # Broj stanica
        'stations': stations,                           # Lista stanica
        'time_span':
            f"{_format_minutes(first_start)}-"
            f"{_format_minutes(last_end)}",             # Vremenski opseg
        'average_trip_duration': average_duration,      # Prosečno trajanje
    }


# Kreiranje male test instance
def small_instance():

    # Lista svih vožnji
    trips = [

        # Vožnja T1 od A do B
        make_trip('T1', 'A', 'B', hm(8, 0), hm(9, 0)),

        # Vožnja T2 od B do C
        make_trip('T2', 'B', 'C', hm(9, 20), hm(10, 10)),

        # Vožnja T3 od C do D
        make_trip('T3', 'C', 'D', hm(10, 30), hm(11, 30)),

        # Vožnja T4 od B do A
        make_trip('T4', 'B', 'A', hm(9, 50), hm(10, 40)),

        # Vožnja T5 od A do C
        make_trip('T5', 'A', 'C', hm(11, 0), hm(12, 0)),

        # Vožnja T6 od C do B
        make_trip('T6', 'C', 'B', hm(12, 30), hm(13, 15)),
    ]

    # Vraća malu instancu
    return {'trips': trips}


# Kreiranje srednje instance
def medium_instance():

    # Lista svih stanica
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

    # Lista svih vožnji
    trips = [

        # Jutarnji smer Beograd -> Novi Sad
        make_trip('M1', stations[0], stations[1], hm(6, 0), hm(6, 14)),
        make_trip('M2', stations[1], stations[2], hm(6, 32), hm(6, 44)),
        make_trip('M3', stations[2], stations[3], hm(7, 0), hm(7, 14)),
        make_trip('M4', stations[3], stations[4], hm(7, 32), hm(7, 46)),
        make_trip('M5', stations[4], stations[5], hm(8, 2), hm(8, 14)),
        make_trip('M6', stations[5], stations[6], hm(8, 32), hm(8, 47)),
        make_trip('M7', stations[6], stations[7], hm(9, 5), hm(9, 19)),
        make_trip('M8', stations[7], stations[8], hm(9, 36), hm(9, 47)),
        make_trip('M9', stations[8], stations[9], hm(10, 5), hm(10, 17)),

        # Povratni smer Novi Sad -> Beograd
        make_trip('M10', stations[9], stations[8], hm(6, 20), hm(6, 32)),
        make_trip('M11', stations[8], stations[7], hm(6, 50), hm(7, 1)),
        make_trip('M12', stations[7], stations[6], hm(7, 18), hm(7, 32)),
        make_trip('M13', stations[6], stations[5], hm(7, 50), hm(8, 5)),
        make_trip('M14', stations[5], stations[4], hm(8, 21), hm(8, 33)),
        make_trip('M15', stations[4], stations[3], hm(8, 50), hm(9, 4)),
        make_trip('M16', stations[3], stations[2], hm(9, 22), hm(9, 36)),
        make_trip('M17', stations[2], stations[1], hm(9, 52), hm(10, 4)),
        make_trip('M18', stations[1], stations[0], hm(10, 20), hm(10, 35)),

        # Direktne vožnje
        make_trip('M19', stations[0], stations[2], hm(11, 0), hm(11, 28)),
        make_trip('M20', stations[2], stations[3], hm(11, 43), hm(11, 57)),
        make_trip('M21', stations[3], stations[5], hm(12, 20), hm(12, 45)),
        make_trip('M22', stations[5], stations[9], hm(13, 5), hm(13, 50)),
        make_trip('M23', stations[9], stations[5], hm(11, 10), hm(11, 55)),
        make_trip('M24', stations[5], stations[3], hm(12, 12), hm(12, 37)),
        make_trip('M25', stations[3], stations[1], hm(12, 45), hm(13, 10)),
        make_trip('M26', stations[1], stations[0], hm(13, 28), hm(13, 43)),

        # Popodnevni polasci
        make_trip('M27', stations[0], stations[1], hm(16, 0), hm(16, 14)),
        make_trip('M28', stations[1], stations[3], hm(16, 32), hm(16, 55)),
        make_trip('M29', stations[3], stations[6], hm(17, 20), hm(17, 55)),
        make_trip('M30', stations[6], stations[9], hm(18, 15), hm(19, 0)),

        # Popodnevni povratci
        make_trip('M31', stations[9], stations[6], hm(16, 10), hm(16, 55)),
        make_trip('M32', stations[6], stations[3], hm(17, 12), hm(17, 47)),
        make_trip('M33', stations[3], stations[1], hm(18, 5), hm(18, 28)),
        make_trip('M34', stations[1], stations[0], hm(18, 45), hm(18, 59)),
    ]

    # Vraća srednju instancu
    return {'trips': trips}


# Proverava da li srednja instanca ispunjava uslove
def _validate_medium_instance(instance):

    # Dobija opis instance
    description = describe_instance(instance)

    # Mora imati tačno 10 stanica
    if description['num_stations'] != 10:
        raise ValueError(
            f"Srednja instanca mora imati tacno 10 stanica, "
            f"a ima {description['num_stations']}."
        )

    # Mora imati najmanje 25 vožnji
    if description['num_trips'] < 25:
        raise ValueError(
            f"Srednja instanca mora imati najmanje 25 voznji, "
            f"a ima {description['num_trips']}."
        )


# Funkcija koja vraća sve dostupne instance
def get_instances():

    # Kreiraju se mala i srednja instanca
    instances = {
        'small': small_instance(),
        'medium': medium_instance()
    }

    # Proverava ispravnost srednje instance
    _validate_medium_instance(instances['medium'])

    # Vraća obe instance
    return instances
