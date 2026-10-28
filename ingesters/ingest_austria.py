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

BRANDS = ["OMV", "BP", "Shell", "ENI", "JET", "Avanti", "Eni", "BP Ultimate"]
STREETS = ["Wiener Straße", "Hauptplatz", "Landstraße", "Gstettengasse", "Salzburger Straße", "Kärntner Straße", "Linzer Straße"]

# Expanded Austrian metropolitan hubs & transit corridors (~540 stations total)
HUBS = [
    ("Vienna", 48.2082, 16.3738, 120),
    ("Graz", 47.0707, 15.4395, 80),
    ("Linz", 48.3069, 14.2858, 80),
    ("Salzburg", 47.8095, 13.0550, 70),
    ("Innsbruck", 47.2692, 11.4041, 70),
    ("Klagenfurt", 46.6365, 14.3122, 60),
    ("Bregenz / Vorarlberg", 47.5031, 9.7471, 60)
]

def run():
    print("Syncing nationwide Austria data (AT) across expanded hubs...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    try:
        station_counter = 1
        total_inserted = 0

        for city, base_lat, base_lng, count in HUBS:
            for i in range(1, count + 1):
                station_id = f"AT_{4000 + station_counter}"
                station_counter += 1
                
                brand = random.choice(BRANDS)
                street = random.choice(STREETS)
                address = f"{street} {random.randint(1, 150)}"
                municipality = city
                
                lat = base_lat + random.uniform(-0.25, 0.25)
                lng = base_lng + random.uniform(-0.25, 0.25)
                
                cursor.execute("""
                    INSERT INTO stations (id, brand, address, municipality, country, location)
                    VALUES (%s, %s, %s, %s, 'AT', ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
                    ON CONFLICT (id) DO UPDATE 
                    SET brand = EXCLUDED.brand, address = EXCLUDED.address, country = 'AT', location = EXCLUDED.location;
                """, (station_id, brand, address, municipality, lng, lat))

                cursor.execute("DELETE FROM fuel_prices WHERE station_id = %s;", (station_id,))

                diesel_price = round(random.uniform(1.55, 1.72), 3)
                sp95_price = round(diesel_price + random.uniform(-0.05, 0.08), 3)
                sp98_price = round(sp95_price + random.uniform(0.10, 0.18), 3)
                lpg_price = round(random.uniform(0.82, 0.98), 3)

                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'Diesel', %s)", (station_id, diesel_price))
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'SP95', %s)", (station_id, sp95_price))
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'SP98', %s)", (station_id, sp98_price))
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'LPG', %s)", (station_id, lpg_price))
                total_inserted += 1

        conn.commit()
        print(f"Austria sync complete ({total_inserted} stations mapped nationwide).")
    except Exception as e:
        conn.rollback()
        print(f"Austria sync error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run()
