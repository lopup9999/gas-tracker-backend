import requests
import psycopg2

# Updated Supabase Pooler Database Parameters
DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres.fnvyxscmxgocxnueabld",
    "password": "%40F4c3b00kt43z3b1",  # Replace with your actual Supabase password
    "host": "aws-0-eu-west-1.pooler.supabase.com",
    "port": 6543,
    "sslmode": "require"
}

SPAIN_API_URL = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/"

def safe_float(val):
    if val is None: return None
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        val_clean = val.replace(",", ".").strip()
        return float(val_clean) if val_clean else None
    return None

def run():
    print("Syncing Spain data to Supabase...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    res = requests.get(SPAIN_API_URL, timeout=30)
    stations = res.json().get("ListaEESSPrecio", [])

    for s in stations:
        try:
            station_id = f"ES_{s.get('IDEESS')}"
            brand = str(s.get('Rótulo') or "Unknown").strip()
            address = str(s.get('Dirección') or "").strip()
            municipality = str(s.get('Municipio') or "").strip()
            lat, lng = safe_float(s.get('Latitud')), safe_float(s.get('Longitud (WGS84)'))
            
            if not lat or not lng: continue

            cursor.execute("""
                INSERT INTO stations (id, brand, address, municipality, country, location)
                VALUES (%s, %s, %s, %s, 'ES', ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
                ON CONFLICT (id) DO UPDATE 
                SET brand = EXCLUDED.brand, address = EXCLUDED.address, country = 'ES', location = EXCLUDED.location;
            """, (station_id, brand, address, municipality, lng, lat))

            e5 = safe_float(s.get("Precio Gasolina 95 E5"))
            diesel = safe_float(s.get("Precio Gasoleo A"))

            if e5:
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'SP95', %s)", (station_id, e5))
            if diesel:
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'Diesel', %s)", (station_id, diesel))
        except Exception:
            conn.rollback()
            continue
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Spain sync to Supabase complete.")

if __name__ == "__main__":
    run()
