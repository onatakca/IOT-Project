import asyncio
import logging
import logging.config
import yaml
from bleak import BleakClient

# Load logging config from YAML
with open("log_config.yaml", "r") as f:
    config = yaml.safe_load(f)
logging.config.dictConfig(config)
logger = logging.getLogger("root")

async def main():
    ble_address = "C6:43:EA:BC:7A:D4"

    async with BleakClient(ble_address) as client:
        logger.info(f"Connected to BLE device: {client.is_connected}")
        services = client.services
        for service in services:
            logger.info(f"Service: {service.uuid}")
            for char in service.characteristics:
                logger.info(f"  Characteristic: {char.uuid} | Properties: {char.properties}")
                if "read" in char.properties:
                    logger.info(f"      Value: {await client.read_gatt_char(char.uuid)}") 

asyncio.run(main())