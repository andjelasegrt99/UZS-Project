import pulp
import time
from itertools import count


def are_compatible(t1, t2, min_transfer):
    return (t1['end_station'] == t2['start_station']) and (t2['start'] - t1['end'] >= min_transfer)


def generate_duties(trips, max_duty_duration, min_transfer, max_sequence_len=None):
    sorted_trips = sorted(trips, key=lambda trip: (trip['start'], trip['end'], trip['id']))
    trip_by_id = {trip['id']: trip for trip in sorted_trips}
    trip_index = {trip['id']: idx for idx, trip in enumerate(sorted_trips)}
    successors = {trip['id']: [] for trip in sorted_trips}

    for i, trip in enumerate(sorted_trips):
        for candidate in sorted_trips[i + 1:]:
            if candidate['start'] - trip['start'] > max_duty_duration:
                break
            if are_compatible(trip, candidate, min_transfer):
                successors[trip['id']].append(candidate['id'])

    duties = []
    duty_id_gen = count()
    seen_sequences = set()

    def dfs(path_ids, first_start, last_trip_id):
        last_trip = trip_by_id[last_trip_id]
        duration = last_trip['end'] - first_start
        if duration > max_duty_duration:
            return

        sequence = tuple(path_ids)
        if sequence not in seen_sequences:
            seen_sequences.add(sequence)
            duties.append({
                'id': f'd{next(duty_id_gen)}',
                'trips': list(path_ids),
                'duration': duration
            })

        if max_sequence_len is not None and len(path_ids) >= max_sequence_len:
            return

        for next_trip_id in successors[last_trip_id]:
            next_trip = trip_by_id[next_trip_id]
            if trip_index[next_trip_id] <= trip_index[last_trip_id]:
                continue
            new_duration = next_trip['end'] - first_start
            if new_duration > max_duty_duration:
                continue
            dfs(path_ids + (next_trip_id,), first_start, next_trip_id)

    for trip in sorted_trips:
        if (trip['end'] - trip['start']) <= max_duty_duration:
            dfs((trip['id'],), trip['start'], trip['id'])

    return duties


def build_and_solve(
    instance,
    max_duty_duration=8*60,
    min_transfer=15,
    fixed_cost=50.0,
    alpha=0.5,
    max_sequence_len=None,
):
    trips = instance['trips']

    duties = generate_duties(
        trips,
        max_duty_duration,
        min_transfer,
        max_sequence_len=max_sequence_len,
    )

    for d in duties:
        d['cost'] = fixed_cost + alpha * d['duration']

    covers = {t['id']: [] for t in trips}
    for d in duties:
        for tid in d['trips']:
            covers[tid].append(d['id'])

    infeasible = [tid for tid, ds in covers.items() if len(ds) == 0]
    if infeasible:
        print("Model nije izvodljiv: sledeće vožnje nisu pokrivene nijednom dužnošću:", infeasible)
        return None, duties, trips, None, 0.0

    prob = pulp.LpProblem('RailwayCrewScheduling', pulp.LpMinimize)

    x = {d['id']: pulp.LpVariable(f"x_{d['id']}", cat='Binary') for d in duties}

    prob += pulp.lpSum([d['cost'] * x[d['id']] for d in duties])

    for t in trips:
        prob += pulp.lpSum([x[d] for d in covers[t['id']]]) == 1, f"cover_{t['id']}"

    solver = pulp.PULP_CBC_CMD(msg=False)
    start = time.time()
    prob.solve(solver)
    solve_time = time.time() - start

    return prob, duties, trips, x, solve_time
