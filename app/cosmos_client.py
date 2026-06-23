import asyncio

from azure.cosmos import ContainerProxy, CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential

from app.models import ArenaRun
from app.settings import settings


class CosmosDBClient:
    def __init__(self):
        self.client: CosmosClient | None = None
        self.database = None
        self.container: ContainerProxy | None = None

    async def initialize(self):
        """Initialize Cosmos DB connection."""
        if not settings.cosmos_endpoint or not settings.cosmos_db:
            return

        credential = DefaultAzureCredential() if settings.use_entra_id else settings.cosmos_key
        if not credential:
            raise ValueError('COSMOS_KEY is required when USE_ENTRA_ID is false')

        self.client = CosmosClient(settings.cosmos_endpoint, credential=credential)
        self.database = self.client.create_database_if_not_exists(id=settings.cosmos_db)
        self.container = self.database.create_container_if_not_exists(
            id=settings.cosmos_container,
            partition_key=PartitionKey(path='/id'),
            offer_throughput=400,
        )

    async def save_run(self, run: ArenaRun) -> ArenaRun:
        """Save or update run in Cosmos DB."""
        if not self.container:
            return run

        # Convert Pydantic model to dict
        run_dict = run.model_dump(mode='json')
        run_dict['id'] = run.id
        
        await asyncio.to_thread(self.container.upsert_item, run_dict)
        return run

    async def get_run(self, run_id: str) -> ArenaRun | None:
        """Retrieve run by ID."""
        if not self.container:
            return None

        try:
            item = await asyncio.to_thread(self.container.read_item, item=run_id, partition_key=run_id)
            return ArenaRun(**item)
        except Exception:
            return None


# Global instance
cosmos_client = CosmosDBClient()
