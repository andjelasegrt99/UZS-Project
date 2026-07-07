# Uvoz PuLP biblioteke za linearno programiranje
import pulp

# Uvoz biblioteke za merenje vremena izvršavanja
import time

# Uvoz funkcije count koja pravi brojač (0,1,2,3...)
from itertools import count


# Proverava da li dve vožnje mogu biti u istoj dužnosti
def are_compatible(t1, t2, min_transfer):

    # Moraju da se završavaju i počinju na istoj stanici
    # i mora postojati dovoljno vremena za presedanje
    return (
        t1['end_station'] == t2['start_station']
    ) and (
        t2['start'] - t1['end'] >= min_transfer
    )


# Generiše sve moguće dužnosti
def generate_duties(
    trips,
    max_duty_duration,
    min_transfer,
    max_sequence_len=None
):

    # Sortiranje vožnji po vremenu polaska, dolaska i ID-u
    sorted_trips = sorted(
        trips,
        key=lambda trip: (
            trip['start'],
            trip['end'],
            trip['id']
        )
    )

    # Rečnik: ID vožnje -> cela vožnja
    trip_by_id = {
        trip['id']: trip
        for trip in sorted_trips
    }

    # Rečnik: ID vožnje -> njen redni broj
    trip_index = {
        trip['id']: idx
        for idx, trip in enumerate(sorted_trips)
    }

    # Za svaku vožnju pravi praznu listu mogućih naslednika
    successors = {
        trip['id']: []
        for trip in sorted_trips
    }

    # Traženje svih kompatibilnih narednih vožnji
    for i, trip in enumerate(sorted_trips):

        # Posmatraju se samo vožnje koje dolaze posle nje
        for candidate in sorted_trips[i + 1:]:

            # Ako bi dužnost bila predugačka prekida se pretraga
            if candidate['start'] - trip['start'] > max_duty_duration:
                break

            # Ako su vožnje kompatibilne dodaje se naslednik
            if are_compatible(trip, candidate, min_transfer):
                successors[trip['id']].append(candidate['id'])

    # Lista svih mogućih dužnosti
    duties = []

    # Generator jedinstvenih ID-eva
    duty_id_gen = count()

    # Skup već obrađenih sekvenci
    seen_sequences = set()

    # Rekurzivna DFS funkcija
    def dfs(path_ids, first_start, last_trip_id):

        # Poslednja vožnja u trenutnoj sekvenci
        last_trip = trip_by_id[last_trip_id]

        # Trajanje cele dužnosti
        duration = last_trip['end'] - first_start

        # Ako je predugačka prekida se
        if duration > max_duty_duration:
            return

        # Trenutna sekvenca vožnji
        sequence = tuple(path_ids)

        # Ako nije već generisana
        if sequence not in seen_sequences:

            # Pamti se da je obrađena
            seen_sequences.add(sequence)

            # Dodaje se nova dužnost
            duties.append({

                # Automatski ID (d0,d1,d2...)
                'id': f'd{next(duty_id_gen)}',

                # Lista vožnji
                'trips': list(path_ids),

                # Ukupno trajanje
                'duration': duration
            })

        # Ako postoji ograničenje broja vožnji u dužnosti
        if (
            max_sequence_len is not None
            and len(path_ids) >= max_sequence_len
        ):
            return

        # Obilaze se svi mogući naslednici
        for next_trip_id in successors[last_trip_id]:

            next_trip = trip_by_id[next_trip_id]

            # Sprečava vraćanje unazad
            if trip_index[next_trip_id] <= trip_index[last_trip_id]:
                continue

            # Novo trajanje ako se doda sledeća vožnja
            new_duration = next_trip['end'] - first_start

            # Ako prelazi dozvoljeno preskače se
            if new_duration > max_duty_duration:
                continue

            # Rekurzivni nastavak pretrage
            dfs(
                path_ids + (next_trip_id,),
                first_start,
                next_trip_id
            )

    # DFS se pokreće iz svake vožnje
    for trip in sorted_trips:

        # Samostalna vožnja mora biti dozvoljene dužine
        if (
            trip['end'] - trip['start']
        ) <= max_duty_duration:

            dfs(
                (trip['id'],),
                trip['start'],
                trip['id']
            )

    # Vraća sve pronađene dužnosti
    return duties


# Formiranje i rešavanje optimizacionog modela
def build_and_solve(

    instance,

    # Maksimalno trajanje dužnosti (8 sati)
    max_duty_duration=8 * 60,

    # Minimalno vreme presedanja
    min_transfer=15,

    # Fiksni trošak jedne dužnosti
    fixed_cost=50.0,

    # Koeficijent promenljivog troška
    alpha=0.5,

    # Maksimalan broj vožnji u jednoj dužnosti
    max_sequence_len=None,
):

    # Sve vožnje iz instance
    trips = instance['trips']

    # Generisanje svih mogućih dužnosti
    duties = generate_duties(

        trips,

        max_duty_duration,

        min_transfer,

        max_sequence_len=max_sequence_len,
    )

    # Računanje troška svake dužnosti
    for d in duties:

        d['cost'] = (
            fixed_cost +
            alpha * d['duration']
        )

    # Za svaku vožnju lista dužnosti koje je pokrivaju
    covers = {
        t['id']: []
        for t in trips
    }

    # Popunjavanje liste pokrivanja
    for d in duties:

        for tid in d['trips']:

            covers[tid].append(d['id'])

    # Provera da li postoji vožnja koju nijedna dužnost ne pokriva
    infeasible = [

        tid

        for tid, ds in covers.items()

        if len(ds) == 0
    ]

    # Ako postoji takva vožnja model nije izvodljiv
    if infeasible:

        print(
            "Model nije izvodljiv: sledeće vožnje nisu pokrivene nijednom dužnošću:",
            infeasible
        )

        return None, duties, trips, None, 0.0

    # Kreiranje LP problema minimizacije
    prob = pulp.LpProblem(

        'RailwayCrewScheduling',

        pulp.LpMinimize
    )

    # Binarne promenljive (0 ili 1)
    x = {

        d['id']:

        pulp.LpVariable(

            f"x_{d['id']}",

            cat='Binary'

        )

        for d in duties
    }

    # Funkcija cilja - minimizacija ukupnog troška
    prob += pulp.lpSum(

        d['cost'] * x[d['id']]

        for d in duties
    )

    # Svaka vožnja mora biti pokrivena tačno jednom dužnošću
    for t in trips:

        prob += (

            pulp.lpSum(

                x[d]

                for d in covers[t['id']]

            )

            == 1,

            f"cover_{t['id']}"
        )

    # CBC solver
    solver = pulp.PULP_CBC_CMD(msg=False)

    # Početak merenja vremena
    start = time.time()

    # Rešavanje modela
    prob.solve(solver)

    # Ukupno vreme rešavanja
    solve_time = time.time() - start

    # Vraća model, dužnosti, vožnje, promenljive i vreme rešavanja
    return prob, duties, trips, x, solve_time
