import json
import os

from src.api.main import app

# Generate OpenAPI schema with app-level metadata and tags
openapi_schema = app.openapi()

# Write to interfaces/openapi.json for other containers to consume
output_dir = "interfaces"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "openapi.json")

with open(output_path, "w") as f:
    json.dump(openapi_schema, f, indent=2)
