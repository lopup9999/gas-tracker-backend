import random
import requests
import psycopg2

# Updated Supabase Pooler Database Parameters
DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres.fnvyxscmxgocxnueabld",
    "password": "%40F4c3b00kt43z3b1",
    "host": "aws-0-eu-west-1.pooler.supabase.com",
    "port": 6543,
    "sslmode": "require"
}

FRANCE_API_URL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/exports/json"

def run():
    print("Syncing live France data from government open-data API...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    try:
        headers = {"User-Agent": "EuroFuelApp/1.0"}
        res = requests.get(FRANCE_API_URL, headers=headers, timeout=60)
        
        if "application/json" not in res.headers.get("Content-Type", ""):
            print(f"Error: Server returned non-JSON response (Status {res.status_code})")
            return

        stations = res.json()
        print(f"Found {len(stations)} stations in France. Processing and inserting...")

        inserted_count = 0
        for s in stations:
            try:
                raw_id = s.get('id') or s.get('id_station')
                if not raw_id: 
                    continue
                station_id = f"FR_{raw_id}"
                
                brand = str(s.get('brand') or s.get('enseigne') or "Unknown").strip()
                address = str(s.get('adresse') or "").strip()
                municipality = str(s.get('ville') or "").strip()
                
                geom = s.get("geom")
                lat = geom.get("lat") if isinstance(geom, dict) else s.get("lat")
                lng = geom.get("lon") if isinstance(geom, dict) else s.get("lon")

                if lat is None or lng is None: 
                    continue

                cursor.execute("""
                    INSERT INTO stations (id, brand, address, municipality, country, location)
                    VALUES (%s, %s, %s, %s, 'FR', ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
                    ON CONFLICT (id) DO UPDATE 
                    SET brand = EXCLUDED.brand, address = EXCLUDED.address, country = 'FR', location = EXCLUDED.location;
                """, (station_id, brand, address, municipality, float(lng), float(lat)))

                cursor.execute("DELETE FROM fuel_prices WHERE station_id = %s;", (station_id,))

                # Map common French fuel fields
                prices = {
                    "Gazole": s.get("gazole_prix"), 
                    "SP95": s.get("sp95_prix"), 
                    "SP98": s.get("sp98_prix"),
                    "E10": s.get("e10_prix"),
                    "E85": s.get("e85_prix"),
                    "GPLc": s.get("gplc_prix")
                }
                
                for fuel, price in prices.items():
                    if price is not None:
                        try:
                            p_val = float(price)
                            if p_val > 0:
                                cursor.execute(
                                    "INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, %s, %s)",
                                    (station_id, fuel, p_val)
                                )
                        except (ValueError, TypeError):
                            continue

                inserted_count += 1
            except Exception:
                # Skip individual bad record without killing the whole sync
                continue

        conn.commit()
        print(f"France live sync complete ({inserted_count} stations successfully synced).")
    except Exception as e:
        conn.rollback()
        print(f"France sync error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run()
