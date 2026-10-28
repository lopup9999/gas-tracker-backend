import psycopg2
import sys

# Replace these 3 variables with your actual Supabase Pooler details:
DB_HOST = "aws-0-eu-west-1.pooler.supabase.com"  # Copy host from Supabase Pooler tab
DB_USER = "postgres.fnvyxscmxgocxnueabld"         # postgres.<your-project-ref>
DB_PASSWORD = "%40F4c3b00kt43z3b1"  # Put raw password here without encoding

def init_cloud_tables():
    print("Connecting to Supabase PostGIS Cloud Database via IPv4 Pooler...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=6543,                            # Pooler Port 6543
            user=DB_USER,
            password=DB_PASSWORD,
            dbname="postgres",
            sslmode="require"                     # Required by Supabase
        )
        cursor = conn.cursor()

        # 1. Enable PostGIS
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        # 2. Create Stations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                id VARCHAR(100) PRIMARY KEY,
                brand VARCHAR(100),
                address TEXT,
                municipality VARCHAR(100),
                country VARCHAR(5),
                location GEOGRAPHY(Point, 4326)
            );
        """)

        # 3. Create Fuel Prices Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fuel_prices (
                id SERIAL PRIMARY KEY,
                station_id VARCHAR(100) REFERENCES stations(id) ON DELETE CASCADE,
                fuel_type VARCHAR(50),
                price_eur NUMERIC(5, 3),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Create Spatial & Search Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stations_location ON stations USING GIST(location);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuel_prices_station ON fuel_prices(station_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuel_prices_type ON fuel_prices(fuel_type);")

        conn.commit()
        print("Success! Supabase cloud tables & PostGIS spatial indexes created successfully!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error setting up cloud tables: {e}")

if __name__ == "__main__":
    init_cloud_tables()
