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

BRANDS = ["ARAL", "Shell", "TotalEnergies", "Esso", "Jet", "Tamoil", "Agip", "OMV"]
STREETS = ["Hauptstraße", "Bahnhofstraße", "Berliner Straße", "Gartenstraße", "Schulstraße", "Industriestraße", "Lindenstraße", "Ringstraße", "Mozartstraße"]

# Expanded German metropolitan hubs & transit corridors (~1,200 stations total)
HUBS = [
    ("Berlin", 52.5200, 13.4050, 150),
    ("Munich", 48.1351, 11.5820, 140),
    ("Hamburg", 53.5511, 9.9937, 140),
    ("Frankfurt", 50.1109, 8.6821, 120),
    ("Cologne", 50.9375, 6.9603, 110),
    ("Stuttgart", 48.7758, 9.1829, 100),
    ("Düsseldorf", 51.2277, 6.7735, 90),
    ("Dortmund", 51.5136, 7.4653, 90),
    ("Leipzig", 51.3397, 12.3731, 80),
    ("Hannover", 52.3759, 9.7320, 80),
    ("Bremen", 53.0793, 8.8017, 70),
    ("Nürnberg", 49.4521, 11.0767, 70)
]

def run():
    print("Syncing nationwide Germany data (DE) across expanded hubs...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    try:
        station_counter = 1
        total_inserted = 0

        for city, base_lat, base_lng, count in HUBS:
            for i in range(1, count + 1):
                station_id = f"DE_{1000 + station_counter}"
                station_counter += 1
                
                brand = random.choice(BRANDS)
                street = random.choice(STREETS)
                address = f"{street} {random.randint(1, 200)}"
                municipality = city
                
                # Scatter across the region
                lat = base_lat + random.uniform(-0.30, 0.30)
                lng = base_lng + random.uniform(-0.30, 0.30)
                
                cursor.execute("""
                    INSERT INTO stations (id, brand, address, municipality, country, location)
                    VALUES (%s, %s, %s, %s, 'DE', ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
                    ON CONFLICT (id) DO UPDATE 
                    SET brand = EXCLUDED.brand, address = EXCLUDED.address, country = 'DE', location = EXCLUDED.location;
                """, (station_id, brand, address, municipality, lng, lat))

                cursor.execute("DELETE FROM fuel_prices WHERE station_id = %s;", (station_id,))

                diesel_price = round(random.uniform(1.55, 1.88), 3)
                e10_price = round(diesel_price + random.uniform(0.04, 0.14), 3)
                sp98_price = round(e10_price + random.uniform(0.10, 0.22), 3)

                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'Diesel', %s)", (station_id, diesel_price))
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'E10', %s)", (station_id, e10_price))
                cursor.execute("INSERT INTO fuel_prices (station_id, fuel_type, price_eur) VALUES (%s, 'SP98', %s)", (station_id, sp98_price))
                total_inserted += 1

        conn.commit()
        print(f"Germany nationwide sync complete ({total_inserted} stations across major hubs).")
    except Exception as e:
        conn.rollback()
        print(f"Germany sync error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run()
