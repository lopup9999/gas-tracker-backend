from ingesters import ingest_spain, ingest_france, ingest_germany, ingest_italy

if __name__ == "__main__":
    print("Starting European multi-country gas station synchronization pipeline...")
    try:
        ingest_spain.run()
        ingest_france.run()
        ingest_germany.run()
        ingest_italy.run()
        print("All European country pipelines executed successfully!")
    except Exception as e:
        print(f"Pipeline failed: {e}")
