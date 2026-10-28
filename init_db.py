import psycopg2

DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "secret",
    "host": "localhost",
    "port": "5432"
}

def init_database():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Enable PostGIS extension for geolocation queries
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    
    # 1. Create Stations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id VARCHAR(50) PRIMARY KEY,
            brand VARCHAR(100),
            address TEXT,
            municipality VARCHAR(100),
            country VARCHAR(10) DEFAULT 'ES',
            location GEOGRAPHY(Point, 4326)
        );
    """)
    
    # 2. Create Fuel Prices Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fuel_prices (
            id SERIAL PRIMARY KEY,
            station_id VARCHAR(50) REFERENCES stations(id) ON DELETE CASCADE,
            fuel_type VARCHAR(20),
            price_eur NUMERIC(5, 3),
            fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 3. Create Spatial & Indexing Keys for ultra-fast distance search
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stations_geo ON stations USING GIST(location);
        CREATE INDEX IF NOT EXISTS idx_prices_station_time ON fuel_prices(station_id, fetched_at);
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Database tables & PostGIS spatial indexes created successfully!")

if __name__ == "__main__":
    init_database()
