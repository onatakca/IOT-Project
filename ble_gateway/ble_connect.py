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
    client = BleakClient(ble_address)
    
    try:
        await client.connect()
        logger.info(f"Connected to BLE device: {client.is_connected}")
        services = client.services
        for service in services:
            logger.info(f"Service: {service.uuid}")
            for char in service.characteristics:
                logger.info(f"  Characteristic: {char.uuid} | Properties: {char.properties}")
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        logger.info(f"      Value: {value}")
                    except Exception as e:
                        logger.warning(f"Failed to read characteristic: {e}")
    except Exception as e:
        logger.error(f"Error during BLE operations: {e}")
    finally:
        try:
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

asyncio.run(main())