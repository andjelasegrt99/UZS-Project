import csv
import os
import pulp

# Uvoz eksternih funkcija za deskripciju instanci i proveru kompatibilnosti dve vožnje
from data_instances import describe_instance
from model import are_compatible


def format_minutes_as_hhmm(total_minutes):
    """Pretvara ukupan broj minuta (npr. 540) u čitljiv HH:MM format (npr. 09:00)."""
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _trip_lookup(trips):
    """Pravi rečnik (mapu) gde je ključ ID vožnje, a vrednost ceo objekat vožnje radi brže pretrage."""
    return {trip['id']: trip for trip in trips}


def get_selected_duties(duties, x_vars):
    """
    Iz liste svih kandidatskih dužnosti izdvaja samo one koje je solver izabrao.
    Proverava da li je vrednost binarne promenljive x veća ili jednaka 0.5.
    """
    if x_vars is None:
        return []
    return [duty for duty in duties if x_vars[duty['id']].value() >= 0.5]


def build_selected_duty_rows(instance_name, selected_duties, trips):
    """
    Priprema podatke o izabranim dužnostima za tabelarni prikaz i CSV izvoz.
    Povezuje dužnosti sa njihovim pripadajućim vožnjama da izvuče stanice, početak i kraj.
    """
    trip_map = _trip_lookup(trips)
    rows = []
    for duty in selected_duties:
        # Dohvatanje svih vožnji koje čine trenutnu dužnost
        duty_trips = [trip_map[trip_id] for trip_id in duty['trips']]
        first_trip = duty_trips[0]
        last_trip = duty_trips[-1]
        
        # Kreiranje strukturiranog rečnika sa svim detaljima dužnosti
        rows.append({
            'instance_name': instance_name,
            'duty_id': duty['id'],
            'trip_sequence': ' -> '.join(duty['trips']),  # Vizuelni prikaz sekvence vožnji
            'first_start_station': first_trip['start_station'],
            'last_end_station': last_trip['end_station'],
            'duty_start': format_minutes_as_hhmm(first_trip['start']),
            'duty_end': format_minutes_as_hhmm(last_trip['end']),
            'duty_duration_minutes': duty['duration'],
            'duty_duration_hhmm': format_minutes_as_hhmm(duty['duration']),
            'number_of_trips': len(duty['trips']),
            'duty_cost': duty['cost'],
        })
    return rows


def verify_solution_integrity(selected_duties, trips, min_transfer, max_duty_duration):
    """
    Ključna validacija rešenja. Proverava:
    1. Da li su vožnje unutar smene hronološki poređane.
    2. Da li su uzastopne vožnje kompatibilne (vreme transfera).
    3. Da li dužina smene prelazi maksimum.
    4. Da li je svaka vožnja iz rasporeda pokrivena tačno jednom (Set Partitioning pravilo).
    """
    trip_map = _trip_lookup(trips)
    cover_count = {trip['id']: 0 for trip in trips}  # Brojač koliko puta je svaka vožnja pokrivena
    issues = []  # Lista za beleženje grešaka

    for duty in selected_duties:
        duty_trip_ids = duty['trips']
        duty_trips = [trip_map[trip_id] for trip_id in duty_trip_ids]

        # 1. Provera hronologije vožnji unutar dužnosti
        starts = [trip['start'] for trip in duty_trips]
        if starts != sorted(starts):
            issues.append(f"Duznost {duty['id']} nema hronoloski poredjane voznje.")

        # 2. Provera kompatibilnosti uzastopnih vožnji
        for first, second in zip(duty_trips, duty_trips[1:]):
            if not are_compatible(first, second, min_transfer):
                issues.append(
                    f"Duznost {duty['id']} ima nekompatibilnu vezu {first['id']} -> {second['id']}."
                )

        # 3. Provera maksimalnog trajanja dužnosti i konzistentnosti podataka
        actual_duration = duty_trips[-1]['end'] - duty_trips[0]['start']
        if actual_duration > max_duty_duration:
            issues.append(
                f"Duznost {duty['id']} premasuje max_duty_duration: {actual_duration} > {max_duty_duration}."
            )
        if duty['duration'] != actual_duration:
            issues.append(
                f"Duznost {duty['id']} ima nekonzistentno trajanje {duty['duration']} umesto {actual_duration}."
            )

        # Evidencija pokrivenosti vožnji
        for trip_id in duty_trip_ids:
            cover_count[trip_id] += 1

    # 4. Provera da li ima neispravno pokrivenih vožnji (nepokrivene ili duplirane vožnje)
    bad_cover = {trip_id: count for trip_id, count in cover_count.items() if count != 1}
    for trip_id, count in bad_cover.items():
        issues.append(f"Voznja {trip_id} ima pokrivenost {count} umesto 1.")

    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'cover_count': cover_count,
    }


def _write_csv(path, fieldnames, rows):
    """Pomoćna funkcija koja kreira direktorijum (ako ne postoji) i upisuje podatke u CSV fajl."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_selected_duties_csv(instance_name, rows):
    """Izvozi detaljne podatke o izabranim dužnostima u CSV fajl."""
    path = os.path.join('outputs', f'{instance_name}_selected_duties.csv')
    fieldnames = [
        'instance_name', 'duty_id', 'trip_sequence', 'first_start_station',
        'last_end_station', 'duty_start', 'duty_end', 'duty_duration_minutes',
        'duty_duration_hhmm', 'number_of_trips', 'duty_cost',
    ]
    _write_csv(path, fieldnames, rows)
    return path


def export_summary_results_csv(summary_rows):
    """Izvozi zbirne (sumarne) rezultate optimizacije za sve testirane instance."""
    path = os.path.join('outputs', 'summary_results.csv')
    fieldnames = [
        'instance_name', 'number_of_trips', 'number_of_stations',
        'number_of_candidate_duties', 'number_of_selected_duties',
        'objective_value', 'solver_status', 'solve_time_seconds',
        'coverage_verified',
    ]
    _write_csv(path, fieldnames, summary_rows)
    return path


def _print_selected_duties_table(rows):
    """Formatira i ispisuje tabelu izabranih dužnosti u konzoli sa dinamičkim širinama kolona."""
    print("Izabrane duznosti:")
    if not rows:
        print("  Nema izabranih duznosti.")
        return

    headers = [
        'duty_id', 'trip_sequence', 'duty_start', 'duty_end',
        'duty_duration_hhmm', 'number_of_trips', 'duty_cost',
    ]
    
    printable_rows = []
    for row in rows:
        printable_rows.append({
            'duty_id': row['duty_id'],
            'trip_sequence': row['trip_sequence'],
            'duty_start': row['duty_start'],
            'duty_end': row['duty_end'],
            'duty_duration_hhmm': row['duty_duration_hhmm'],
            'number_of_trips': str(row['number_of_trips']),
            'duty_cost': f"{row['duty_cost']:.2f}",
        })

    # Proračun maksimalne širine za svaku kolonu radi lepog poravnanja text-a
    widths = {
        header: max(len(header), max(len(entry[header]) for entry in printable_rows))
        for header in headers
    }
    
    header_line = " | ".join(header.ljust(widths[header]) for header in headers)
    separator = "-+-".join("-" * widths[header] for header in headers)
    
    print(header_line)
    print(separator)
    for entry in printable_rows:
        print(" | ".join(entry[header].ljust(widths[header]) for header in headers))


def display_results(instance_name, instance, prob, duties, trips, x_vars, solve_time, params):
    """
    Glavna funkcija za obradu i prikaz rezultata nakon završetka optimizacije.
    Objedinjuje ekstrakciju, verifikaciju, ispis na ekranu i pripremu podataka za čuvanje.
    """
    # Slučaj kada solver uopšte nije uspeo da pronađe dopustivo rešenje
    if prob is None:
        print("Nema rešenja (model nije izvodljiv).")
        return {
            'selected_duty_rows': [],
            'summary_row': {
                'instance_name': instance_name,
                'number_of_trips': len(trips),
                'number_of_stations': describe_instance(instance)['num_stations'],
                'number_of_candidate_duties': len(duties),
                'number_of_selected_duties': 0,
                'objective_value': None,
                'solver_status': 'Not Solved',
                'solve_time_seconds': solve_time,
                'coverage_verified': False,
            },
            'integrity': {'is_valid': False, 'issues': ['Model nije izvodljiv.'], 'cover_count': {}},
        }

    # Dohvatanje statusa solvera (npr. Optimal, Infeasible) i vrednosti funkcije cilja
    status = pulp.LpStatus[prob.status]
    obj = pulp.value(prob.objective)
    
    # Obrada izabranih rešenja
    selected_duties = get_selected_duties(duties, x_vars)
    selected_rows = build_selected_duty_rows(instance_name, selected_duties, trips)
    
    # Pokretanje provere integriteta rešenja
    integrity = verify_solution_integrity(
        selected_duties,
        trips,
        min_transfer=params['min_transfer'],
        max_duty_duration=params['max_duty_duration'],
    )

    # Ispis osnovnih performansi optimizacije u konzolu
    print(f"Status solvera: {status}")
    print(f"Vrednost cilja: {obj}")
    print(f"Vreme rešavanja (s): {solve_time:.3f}")
    print(f"Broj kandidatskih dužnosti: {len(duties)}")
    print(f"Broj izabranih dužnosti: {len(selected_duties)}")
    
    # Prikaz tabele
    _print_selected_duties_table(selected_rows)

    # Ispis ishoda verifikacije rešenja
    if integrity['is_valid']:
        print("Provera rešenja: uspešna. Sve vožnje su pokrivene tačno jednom.")
    else:
        print("Provera rešenja: NEUSPEŠNA.")
        for issue in integrity['issues']:
            print(f"  - {issue}")

    # Pakovanje sumarnih rezultata za povratnu vrednost (i kasniji izvoz u zajednički CSV)
    instance_description = describe_instance(instance)
    summary_row = {
        'instance_name': instance_name,
        'number_of_trips': instance_description['num_trips'],
        'number_of_stations': instance_description['num_stations'],
        'number_of_candidate_duties': len(duties),
        'number_of_selected_duties': len(selected_duties),
        'objective_value': obj,
        'solver_status': status,
        'solve_time_seconds': solve_time,
        'coverage_verified': integrity['is_valid'],
    }

    return {
        'selected_duty_rows': selected_rows,
        'summary_row': summary_row,
        'integrity': integrity,
    }
