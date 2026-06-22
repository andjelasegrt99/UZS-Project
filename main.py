import os

from model import build_and_solve
from data_instances import get_instances, describe_instance
from results import (
    display_results,
    export_selected_duties_csv,
    export_summary_results_csv,
)
import sensitivity


def run_instance(name, instance, params):
    print(f"\n--- Rešavanje instance: {name} ---")
    description = describe_instance(instance)
    print(
        "Opis instance: "
        f"broj vožnji = {description['num_trips']}, "
        f"broj stanica = {description['num_stations']}, "
        f"vremenski raspon = {description['time_span']}, "
        f"prosečno trajanje vožnje = {description['average_trip_duration']:.1f} min"
    )
    print(f"Stanice: {', '.join(description['stations'])}")
    prob, duties, trips, x_vars, solve_time = build_and_solve(instance, **params)
    report = display_results(name, instance, prob, duties, trips, x_vars, solve_time, params)
    selected_path = export_selected_duties_csv(name, report['selected_duty_rows'])
    print(f"Sačuvan CSV izabranih dužnosti: {os.path.abspath(selected_path)}")
    return report['summary_row']


def main():
    instances = get_instances()
    os.makedirs('outputs', exist_ok=True)
    params = {"max_duty_duration": 8 * 60,
              "min_transfer": 15,
              "fixed_cost": 50.0,
              "alpha": 0.5}
    summary_rows = []

    summary_rows.append(run_instance("small", instances["small"], params))

    summary_rows.append(run_instance("medium", instances["medium"], params))

    summary_path = export_summary_results_csv(summary_rows)
    print(f"\nSačuvan zbirni CSV rezultata: {os.path.abspath(summary_path)}")

    print("\n--- Pokretanje analize osetljivosti ---")
    sensitivity.run_sensitivity(instances["medium"], base_params=params)


if __name__ == "__main__":
    main()
