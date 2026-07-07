import os

# Uvoz funkcija iz sopstvenih modula (model, data_instances, results, sensitivity)
from model import build_and_solve
from data_instances import get_instances, describe_instance
from results import (
    display_results,
    export_selected_duties_csv,
    export_summary_results_csv,
)
import sensitivity


def run_instance(name, instance, params):
    """
    Pokreće optimizaciju za jednu konkretnu instancu podataka.
    Prikazuje opis problema, poziva solver, ispisuje rezultate na ekranu,
    izvozi ih u CSV i vraća sumarni red za statistiku.
    """
    print(f"\n--- Rešavanje instance: {name} ---")
    
    # Dohvatanje i ispis metapodataka o instanci (broj vožnji, stanica, trajanje...)
    description = describe_instance(instance)
    print(
        "Opis instance: "
        f"broj vožnji = {description['num_trips']}, "
        f"broj stanica = {description['num_stations']}, "
        f"vremenski raspon = {description['time_span']}, "
        f"prosečno trajanje vožnje = {description['average_trip_duration']:.1f} min"
    )
    print(f"Stanice: {', '.join(description['stations'])}")
    
    # Kreiranje matematičkog modela i njegovo rešavanje (PuLP solver)
    prob, duties, trips, x_vars, solve_time = build_and_solve(instance, **params)
    
    # Obrada, validacija i prikaz rezultata u konzoli
    report = display_results(name, instance, prob, duties, trips, x_vars, solve_time, params)
    
    # Izvoz detaljnih podataka o selektovanim dužnostima (smenama) u CSV fajl
    selected_path = export_selected_duties_csv(name, report['selected_duty_rows'])
    print(f"Sačuvan CSV izabranih dužnosti: {os.path.abspath(selected_path)}")
    
    # Vraćanje sumarnog reda koji će se koristiti za pravljenje zbirnog izveštaja
    return report['summary_row']


def main():
    """
    Glavna funkcija programa koja koordinira učitavanje podataka,
    izvršavanje optimizacije na više instanci i pokretanje analize osetljivosti.
    """
    # Učitavanje svih dostupnih instanci (npr. small, medium, large)
    instances = get_instances()
    
    # Kreiranje 'outputs' direktorijuma za čuvanje rezultata ukoliko ne postoji
    os.makedirs('outputs', exist_ok=True)
    
    # Defisanje osnovnih (baznih) parametara za optimizaciju rasporeda
    params = {
        "max_duty_duration": 8 * 60,  # Maksimalno trajanje smene u minutima (8 sati)
        "min_transfer": 15,           # Minimalno vreme za transfer između vožnji (15 minuta)
        "fixed_cost": 50.0,           # Fiksni trošak angažovanja jedne dužnosti/smene
        "alpha": 0.5                  # Težinski faktor u funkciji cilja (balans troškova)
    }
    summary_rows = []

    # 1. Pokretanje optimizacije za malu ("small") instancu
    summary_rows.append(run_instance("small", instances["small"], params))

    # 2. Pokretanje optimizacije za srednju ("medium") instancu
    summary_rows.append(run_instance("medium", instances["medium"], params))

    # Izvoz zbirnih rezultata za sve pokrenute instance u jedan zajednički CSV fajl
    summary_path = export_summary_results_csv(summary_rows)
    print(f"\nSačuvan zbirni CSV rezultata: {os.path.abspath(summary_path)}")

    # 3. Pokretanje analize osetljivosti na srednjoj instanci
    # Ova funkcija će automatski menjati parametre i generisati grafikone promena
    print("\n--- Pokretanje analize osetljivosti ---")
    sensitivity.run_sensitivity(instances["medium"], base_params=params)


# Obezbeđuje da se funkcija main() izvrši samo ako se skripta pokrene direktno
if __name__ == "__main__":
    main()
