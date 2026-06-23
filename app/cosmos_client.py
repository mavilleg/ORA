from azure.cosmos import ContainerProxy, CosmosClient
from azure.identity import DefaultAzureCredential

from app.models import ArenaRun
from app.settings import settings


class CosmosDBClient:
    def __init__(self):
        self.client = None
        self.database = None
        self.container = None

    async def initialize(self):
        """Initialize Cosmos DB connection."""
        if not settings.cosmos_endpoint or not settings.cosmos_db:
            return

        # Use DefaultAzureCredential for Entra ID auth
        credential = DefaultAzureCredential()
        self.client = CosmosClient(settings.cosmos_endpoint, credential=credential)
        self.database = self.client.get_database_client(settings.cosmos_db)
        
        # Create or get container
        try:
            self.container = self.database.get_container_client(settings.cosmos_container)
        except Exception:
            # Container doesn't exist, create it
            self.container = self.database.create_container(
                id=settings.cosmos_container,
                partition_key='/id',
                offer_throughput=400,
            )

    async def save_run(self, run: ArenaRun) -> ArenaRun:
        """Save or update run in Cosmos DB."""
        if not self.container:
            return run

        # Convert Pydantic model to dict
        run_dict = run.model_dump(mode='json')
        run_dict['id'] = run.id
        
        self.container.upsert_item(run_dict)
        return run

    async def get_run(self, run_id: str) -> ArenaRun | None:
        """Retrieve run by ID."""
        if not self.container:
            return None

        try:
            item = self.container.read_item(item=run_id, partition_key=run_id)
            return ArenaRun(**item)
        except Exception:
            return None


# Global instance
cosmos_client = CosmosDBClient()
