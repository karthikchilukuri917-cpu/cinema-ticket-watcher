from app.catalogue_ingestion import CatalogueIngestionService


service = CatalogueIngestionService()

count = service.ingest_movies("Hyderabad")

print(f"Imported movies: {count}")