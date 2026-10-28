from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
from typing import Optional
import os
from urllib.parse import unquote, urlparse

app = FastAPI(
    title="Euro Fuel Tracker API",
    description="Backend API for locating the cheapest fuel stations across Europe using PostGIS.",
    version="1.0.0"
)

# Enable CORS for cross-platform Flutter client communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("🔥 ERROR: DATABASE_URL environment variable is missing on Render!")
        raise HTTPException(status_code=500, detail="DATABASE_URL environment variable is not set.")
    
    try:
        parsed = urlparse(db_url)
        username = unquote(parsed.username) if parsed.username else ""
        
        # SAFETY FIX: If Render has just "postgres", automatically inject your full Supabase project ref!
        if username == "postgres":
            username = "postgres.fnvyxscmxgocxnueabld"
            
        password = unquote(parsed.password) if parsed.password else ""
        hostname = parsed.hostname or "aws-0-eu-west-1.pooler.supabase.com"
        port = parsed.port or 6543
        dbname = parsed.path.lstrip('/') or "postgres"

        return psycopg2.connect(
            dbname=dbname,
            user=username,
            password=password,
            host=hostname,
            port=port,
            sslmode="require",
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    except Exception as e:
        print(f"🔥 PSYCOPG2 CONNECTION FAILURE: {repr(e)}")
        raise e

@app.get("/")
def health_check():
    """Health check endpoint to verify server and database connectivity."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total_stations FROM stations;")
        count = cursor.fetchone()["total_stations"]
        cursor.close()
        conn.close()
        return {"status": "healthy", "database_connected": True, "total_stations": count}
    except Exception as e:
        print(f"🔥 HEALTH CHECK FAILED: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.get("/stations/nearest")
def get_nearest_stations(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(15.0, description="Search radius in kilometers"),
    fuel_type: str = Query("Diesel", description="Fuel type (e.g., Diesel, SP95, E10, Gazole)"),
    limit: int = Query(20, description="Max results to return")
):
    radius_meters = radius_km * 1000.0
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT 
                s.id, s.brand, s.address, s.municipality, s.country,
                ST_Y(s.location::geometry) AS latitude,
                ST_X(s.location::geometry) AS longitude,
                ST_Distance(
                    s.location::geography, 
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS distance_meters,
                fp.fuel_type, fp.price_eur, fp.updated_at
            FROM stations s
            JOIN fuel_prices fp ON s.id = fp.station_id
            WHERE ST_DWithin(
                s.location::geography, 
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 
                %s
            )
            AND LOWER(fp.fuel_type) = LOWER(%s)
            ORDER BY fp.price_eur ASC
            LIMIT %s;
        """
        cursor.execute(query, (lng, lat, lng, lat, radius_meters, fuel_type, limit))
        stations = cursor.fetchall()
        
        return {
            "search_params": {"lat": lat, "lng": lng, "radius_km": radius_km, "fuel_type": fuel_type},
            "count": len(stations),
            "stations": stations
        }
    except Exception as e:
        print(f"🔥 NEAREST STATIONS QUERY ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
