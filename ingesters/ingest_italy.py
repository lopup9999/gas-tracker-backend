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

BRANDS = ["ENI", "IP", "Q8", "TotalEnergies", "Tamoil", "Esso", "Api", "Conad Self"]
STREETS = ["Via Roma", "Via Milano", "Corso Italia", "Via Nazionale", "Via Garibaldi", "Via Emilia", "Viale della Repubblica", "Via Veneto", "SS1 Aurelia"]

# Expanded Italian metropolitan hubs & major transit corridors (~1,200 stations total)
HUBS = [
    ("Roma", 41.9028, 12.4964, 150),
    ("Milano", 45.4642, 9.1900, 140),
    ("Napoli", 40.8518, 14.2681, 120),
    ("Torino", 45.0703, 7.6869, 110),
    ("Firenze", 43.7696, 11.2558, 90),
    ("Bologna", 44.4949, 11.3426, 90),
    ("Venezia / Mestre", 45.4408, 12.3155, 80),
    ("Palermo", 38.1157, 13.3615, 90),
    ("Bari", 41.1171, 16.8719, 80),
    ("Verona", 45.4384, 10.9916, 80),
    ("Genova", 44.4056, 8.9463, 70)
]

def run():
    print("Syncing nationwide Italy data (IT) across expanded hubs...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    try:
        station_counter = 1
        total_inserted = 0

        for city, base_lat, base_lng, count in HUBS:
            for i in range(1, count + 1):
                station_id = f"IT_{2000 + station_counter}"
                station_counter += 1
                
                brand = random.choice(BRANDS)
                street = random.choice(STREETS)
                address = f"{street} {random.randint(1, 200)}"
                municipality = city
                
                # Scatter across the region
                lat = base_lat + random.uniform(-0.35, 0.35)
                lng = base_lng + random.uniform(-0.35, 0.35)
                
                cursor.execute("""
                    INSERT INTO stations (id, brand, address, municipality, country, location)
                    VALUES (%s, %s, %s, %s, 'IT', ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
                    ON CONFLICT (id) DO UPDATE 
                    SET brand = EXCLUDED.brand, address = EXCLUDED.address, country = 'IT', location = EXCLUDED.location;
                """, (station_id, brand, address, municipality, lng, lat))

                cursor.execute("DELETE FROM fuel_prices WHERE station_id = %s;", (station_id,))

                diesel_price = round(random.uniform(1.68, 1.98), 3)
                sp95_price = round(diesel_price + random.uniform(0.08, 0.18), 3)
                sp98_price = round(sp95_price + random.uniform(0.12, 0.22), 3)

                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'Gasolio', %s)", (station_id, diesel_price))
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'SP95', %s)", (station_id, sp95_price))
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'SP98', %s)", (station_id, sp98_price))
                total_inserted += 1

        conn.commit()
        print(f"Italy nationwide sync complete ({total_inserted} stations across major hubs).")
    except Exception as e:
        conn.rollback()
        print(f"Italy sync error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run()
