import os
import csv
import matplotlib
# Postavljanje 'Agg' backend-a za matplotlib kako bi se grafikoni generisali u pozadini
# i sačuvali kao fajlovi, bez pokušaja otvaranja GUI prozora (korisno za servere/skripte)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pulp
from model import build_and_solve


def _collect_scenario_row(instance, base_params, scenario_type, parameter_value, overrides):
    """
    Pokreće model optimizacije za specifičan scenario i vraća rezultate u vidu rečnika.
    Kopira osnovne parametre, primenjuje izmene (overrides) i poziva solver.
    """
    params = base_params.copy()
    params.update(overrides)  # Prepravljanje parametra koji se trenutno testira
    prob, duties, trips, x, solve_time = build_and_solve(instance, **params)

    # Slučaj kada solver uopšte ne vrati model ili je pokretanje prekinuto
    if prob is None:
        return {
            'scenario_type': scenario_type,
            'parameter_value': parameter_value,
            'max_duration': params['max_duty_duration'],
            'min_transfer': params['min_transfer'],
            'fixed_cost': params.get('fixed_cost'),
            'objective_value': None,
            'num_selected_duties': 0,
            'num_covered_trips': 0,
            'solver_status': 'Not Solved',
            'solve_time_seconds': solve_time,
        }

    status_text = pulp.LpStatus[prob.status]
    obj = None
    num_selected = 0
    covered = 0

    # Ako je pronađeno optimalno ili dopustivo rešenje, izvlače se metrike
    if status_text in ('Optimal', 'Feasible'):
        obj = prob.objective.value()
        # Izdvajanje dužnosti koje je solver odabrao (gde je binarna promenljiva x >= 0.5)
        selected = [dd for dd in duties if x[dd['id']].value() >= 0.5]
        num_selected = len(selected)
        
        # Brojanje jedinstvenih vožnji koje su pokrivene izabranim dužnostima
        covered_set = set()
        for duty in selected:
            for trip_id in duty['trips']:
                covered_set.add(trip_id)
        covered = len(covered_set)

    return {
        'scenario_type': scenario_type,
        'parameter_value': parameter_value,
        'max_duration': params['max_duty_duration'],
        'min_transfer': params['min_transfer'],
        'fixed_cost': params.get('fixed_cost'),
        'objective_value': obj,
        'num_selected_duties': num_selected,
        'num_covered_trips': covered,
        'solver_status': status_text,
        'solve_time_seconds': solve_time,
    }


def _plot_metric(rows, scenario_type, metric_key, ylabel, title, output_name):
    """
    Generiše i čuva pojedinačni linijski grafikon za određenu metriku
    u zavisnosti od promenjenog parametra scenarija.
    """
    # Filtriranje redova koji pripadaju traženom tipu scenarija
    scenario_rows = [row for row in rows if row['scenario_type'] == scenario_type]
    xs = [row['parameter_value'] for row in scenario_rows]
    # Ako je vrednost None (neizvodljiv model), pretvara se u NaN da grafik preskoči tu tačku
    ys = [
        row[metric_key] if row[metric_key] is not None else float('nan')
        for row in scenario_rows
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs, ys, marker='o')
    ax.set_xlabel(scenario_type)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(os.path.join('outputs', output_name))
    plt.close(fig)


def _plot_overview(rows):
    """
    Generiše zbirni grafikon sa 3 podgrafika (subplots) koji prikazuju
    kako se vrednost funkcije cilja menja kroz sva tri posmatrana parametra.
    """
    scenario_specs = [
        ('max_duration', 'max_duration'),
        ('min_transfer', 'min_transfer'),
        ('fixed_cost', 'fixed_cost'),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    for ax, (scenario_type, title) in zip(axes, scenario_specs):
        scenario_rows = [row for row in rows if row['scenario_type'] == scenario_type]
        xs = [row['parameter_value'] for row in scenario_rows]
        ys = [
            row['objective_value'] if row['objective_value'] is not None else float('nan')
            for row in scenario_rows
        ]
        ax.plot(xs, ys, marker='o')
        ax.set_title(title)
        ax.set_xlabel('Vrednost parametra')
        ax.set_ylabel('Vrednost cilja')

    plt.tight_layout()
    fig.savefig(os.path.join('outputs', 'sensitivity.png'))
    plt.close(fig)


def run_sensitivity(instance, base_params):
    """
    Glavna funkcija za analizu osetljivosti (Sensitivity Analysis).
    Uzastopno menja parametre (trajanje smene, vreme transfera, fiksni trošak),
    beleži ponašanje modela, upisuje ih u CSV i generiše vizuelne grafikone.
    """
    os.makedirs('outputs', exist_ok=True)
    rows = []

    # 1. Testiranje uticaja maksimalnog trajanja dužnosti (u minutima)
    durations = [4*60, 6*60, 8*60, 10*60]
    for d in durations:
        rows.append(
            _collect_scenario_row(
                instance,
                base_params,
                'max_duration',
                d,
                {'max_duty_duration': d},
            )
        )

    # 2. Testiranje uticaja minimalnog vremena za transfer (u minutima)
    transfers = [0, 10, 20, 30]
    for tr in transfers:
        rows.append(
            _collect_scenario_row(
                instance,
                base_params,
                'min_transfer',
                tr,
                {'min_transfer': tr},
            )
        )

    # 3. Testiranje uticaja fiksne cene po angažovanoj dužnosti
    fixeds = [0.0, 20.0, 50.0, 100.0]
    for fc in fixeds:
        rows.append(
            _collect_scenario_row(
                instance,
                base_params,
                'fixed_cost',
                fc,
                {'fixed_cost': fc},
            )
        )

    # Upis svih sakupljenih podataka iz scenarija u jedan CSV fajl
    csv_path = os.path.join('outputs', 'sensitivity.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'scenario_type', 'parameter_value', 'max_duration', 'min_transfer',
            'fixed_cost', 'objective_value', 'num_selected_duties',
            'num_covered_trips', 'solver_status', 'solve_time_seconds',
        ])
        for row in rows:
            writer.writerow([
                row['scenario_type'], row['parameter_value'], row['max_duration'],
                row['min_transfer'], row['fixed_cost'], row['objective_value'],
                row['num_selected_duties'], row['num_covered_trips'],
                row['solver_status'], row['solve_time_seconds'],
            ])

    # Generisanje pojedinačnih grafikona za vrednosti cilja (Objective Value)
    _plot_metric(
        rows, 'max_duration', 'objective_value',
        'Vrednost cilja (objective)', 'Objective prema max_duration',
        'sensitivity_objective_max_duration.png',
    )
    _plot_metric(
        rows, 'min_transfer', 'objective_value',
        'Vrednost cilja (objective)', 'Objective prema min_transfer',
        'sensitivity_objective_min_transfer.png',
    )
    _plot_metric(
        rows, 'fixed_cost', 'objective_value',
        'Vrednost cilja (objective)', 'Objective prema fixed_cost',
        'sensitivity_objective_fixed_cost.png',
    )
    
    # Generisanje pojedinačnih grafikona za broj izabranih dužnosti (smene)
    _plot_metric(
        rows, 'max_duration', 'num_selected_duties',
        'Broj izabranih duznosti', 'Broj izabranih duznosti prema max_duration',
        'sensitivity_num_selected_max_duration.png',
    )
    _plot_metric(
        rows, 'min_transfer', 'num_selected_duties',
        'Broj izabranih duznosti', 'Broj izabranih duznosti prema min_transfer',
        'sensitivity_num_selected_min_transfer.png',
    )
    _plot_metric(
        rows, 'fixed_cost', 'num_selected_duties',
        'Broj izabranih duznosti', 'Broj izabranih duznosti prema fixed_cost',
        'sensitivity_num_selected_fixed_cost.png',
    )
    
    # Generisanje velikog zbirnog preglednog grafikona
    _plot_overview(rows)
    print(f"Analiza osetljivosti sačuvana u {csv_path} i outputs/*.png")


def run_sensitivity_from_main(instance, base_params):
    """Eksterna funkcija omotač (wrapper) za pokretanje analize osetljivosti."""
    run_sensitivity(instance, base_params)


# Izvršavanje skripte direktno iz terminala
if __name__ == '__main__':
    from data_instances import get_instances
    # Dohvatanje srednje instance podataka za testiranje
    inst = get_instances()['medium']
    # Pokretanje analize sa početnim baznim parametrima
    run_sensitivity(inst, {
        'max_duty_duration': 8*60,
        'min_transfer': 15,
        'fixed_cost': 50.0,
        'alpha': 0.5
    })
