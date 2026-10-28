import psycopg2

DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "secret",
    "host": "localhost",
    "port": "5432"
}

def find_cheapest_nearby(user_lat, user_lng, radius_km=15, fuel_type='Diesel'):
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # High-performance PostGIS query
    query = """
        SELECT 
            s.id, s.brand, s.address, s.municipality,
            fp.price_eur,
            ROUND((ST_Distance(s.location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000)::numeric, 2) AS distance_km
        FROM stations s
        JOIN fuel_prices fp ON s.id = fp.station_id
        WHERE ST_DWithin(s.location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s * 1000)
          AND fp.fuel_type = %s
        ORDER BY fp.price_eur ASC
        LIMIT 5;
    """
    
    cursor.execute(query, (user_lng, user_lat, user_lng, user_lat, radius_km, fuel_type))
    results = cursor.fetchall()
    
    print(f"\n--- TOP 5 CHEAPEST {fuel_type} STATIONS WITHIN {radius_km}KM ---")
    for r in results:
        print(f"Brand: {r[1]} | Address: {r[2]}, {r[3]} | Price: €{r[4]}/L | Distance: {r[5]} km")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Example GPS coordinates for Central Madrid: 40.4167, -3.7037
    find_cheapest_nearby(user_lat=40.4167, user_lng=-3.7037, radius_km=10, fuel_type='Diesel')
