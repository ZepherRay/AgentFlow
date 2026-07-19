"""Neo4j connection manager for Graph RAG."""

from neo4j import GraphDatabase, AsyncGraphDatabase, AsyncDriver
from loguru import logger
from config import settings

_driver: AsyncDriver | None = None


async def get_neo4j_driver() -> AsyncDriver:
    """Get or create the shared Neo4j async driver singleton."""
    global _driver
    if _driver is None:
        logger.info(
            f"Connecting to Neo4j: {settings.NEO4J_URI} "
            f"db={settings.NEO4J_DATABASE}"
        )
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        # Verify connection
        async with _driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.run("RETURN 1")
        logger.info("Neo4j connection established")
    return _driver


async def close_neo4j_driver():
    """Close the Neo4j driver singleton."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j connection closed")
