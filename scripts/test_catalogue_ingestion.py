from app.catalogue_ingestion import CatalogueIngestionService


service = CatalogueIngestionService()

count = service.ingest_cinemas("Hyderabad")

print(f"Imported cinemas: {count}")