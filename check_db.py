import psycopg2

DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres.fnvyxscmxgocxnueabld",
    "password": "ubunfi311m9999",
    "host": "aws-0-eu-west-1.pooler.supabase.com",
    "port": 6543,
    "sslmode": "require"
}

def check():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    print("--- DATABASE STATUS SUMMARY ---")
    
    # 1. Count stations by country
    cursor.execute("""
        SELECT country, COUNT(*) 
        FROM stations 
        GROUP BY country 
        ORDER BY country;
    """)
    rows = cursor.fetchall()
    print("\n[Stations per Country]:")
    for country, count in rows:
        print(f"  Country {country}: {count} stations")

    # 2. Count total fuel prices
    cursor.execute("SELECT COUNT(*) FROM fuel_prices;")
    total_prices = cursor.fetchone()[0]
    print(f"\n[Total Fuel Price Records]: {total_prices}")

    # 3. Sample spatial query (e.g., checking stations near central Madrid or Lisbon)
    cursor.execute("""
        SELECT id, brand, municipality, country 
        FROM stations 
        LIMIT 3;
    """)
    print("\n[Sample Stations]:")
    for s in cursor.fetchall():
        print(f"  ID: {s[0]} | Brand: {s[1]} | City: {s[2]} | Country: {s[3]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check()

