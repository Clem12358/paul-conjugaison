"""
Script pour charger les 22 verbes initiaux dans Supabase.
A executer UNE SEULE FOIS apres avoir cree la table.

Usage:
  python seed_supabase.py <SUPABASE_URL> <SUPABASE_KEY>
"""
import json
import sys
from supabase import create_client

PERSONNES = ["je", "tu", "il/elle", "nous", "vous", "ils/elles"]
TEMPS = ["présent", "imparfait", "futur", "passé composé"]

def main():
    if len(sys.argv) != 3:
        print("Usage: python seed_supabase.py <SUPABASE_URL> <SUPABASE_KEY>")
        sys.exit(1)

    url = sys.argv[1]
    key = sys.argv[2]
    sb = create_client(url, key)

    with open("verbes.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for infinitif, temps_data in data.items():
        for temps, personnes in temps_data.items():
            for personne, reponse in personnes.items():
                rows.append({
                    "infinitif": infinitif,
                    "temps": temps,
                    "personne": personne,
                    "reponse": reponse
                })

    print(f"Insertion de {len(rows)} lignes...")

    # Insert in batches of 100
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        sb.table("conjugaisons").insert(batch).execute()
        print(f"  Batch {i // batch_size + 1} OK ({len(batch)} lignes)")

    print("Termine !")


if __name__ == "__main__":
    main()
