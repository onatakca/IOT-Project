import asyncio
import logging
import threading
from bleak import BleakClient, BleakScanner
from .ble_message import Message

logger = logging.getLogger("ble_gateway")

class BleGateway:
    """
    BLE Gateway that runs in its own thread and communicates with the game via a queue.
    Sends paddle state updates (left_paddle, right_paddle) to the game.
    """
    
    def __init__(self, message: Message):
        self.message = message
        self.device_addresses = []
        self.running = False
        self.thread = None
        self.paddles = {}
        
        # Constants for paddle configuration
        self.PADDLE_SERVICE_UUID = "ef680200-9b35-4933-9b10-52ffa9740042"  # Example UUID, replace with actual
        self.PADDLE_LEFT = bytearray([0x01])
        self.PADDLE_RIGHT = bytearray([0x02])
        self.CONFIG_CHAR_UUID = "ef680201-9b35-4933-9b10-52ffa9740042"  # Example UUID, replace with actual
        
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        logger.info("BLE Gateway started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("BLE Gateway stopped")
    
    def _run_async_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._main_async())
        except Exception as e:
            logger.error(f"Error in BLE gateway async loop: {e}")
        finally:
            loop.close()
            
    async def _main_async(self):
        """Main async function that handles BLE connection and communication."""
        await self._scan_for_devices()
        await self._connect_to_devices()
        await self._listen_to_paddles()
        
    async def _scan_for_devices(self, max_attempts=6, scan_timeout=2):
        """
        Scan for BLE devices with automatic retry logic.
        
        Args:
            max_attempts: Maximum number of scan attempts before giving up
            scan_timeout: Starting timeout in seconds (increases by 2s each retry)
        
        Raises:
            ValueError: If no devices found after all retry attempts
        """
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Scanning for BLE devices ({scan_timeout}s) - attempt {attempt}/{max_attempts}...")
            # TODO: Filter by service UUID 
            # devices = await BleakScanner.discover(timeout=scan_timeout, service_uuids=[self.PADDLE_SERVICE_UUID])
            devices = await BleakScanner.discover(timeout=scan_timeout)
                
            if devices:
                logger.info(f"Found {len(devices)} devices")
                for device in devices:
                    logger.info(f"  - {device.name}: {device.address}")
                    self.device_addresses.append(device.address)
                
            if self.device_addresses:
                logger.info("Successfully found the Thingy paddles")
                return  # Success!
            else:
                logger.warning(f"BLE scan failed attempt {attempt}/{max_attempts}")
                scan_timeout += 2
                
        if attempt == max_attempts:
            logger.error("Max BLE scan attempts reached, giving up")
            raise ValueError("No paddle Thingies were found")
        
    async def _connect_to_devices(self):
        """Connect and configure both paddles."""
        if len(self.device_addresses) < 2:
            logger.warning("Expected 2 paddle devices, but found fewer")
            raise ValueError("Not enough paddle devices found")
        
        # Assign first device as LEFT paddle
        self.paddles["LEFT"] = BleakClient(self.device_addresses[0])
        await self.paddles["LEFT"].connect()
        # TODO: How to check if write was successful?
        await  self.paddles["LEFT"].write_gatt_char(self.CONFIG_CHAR_UUID, self.PADDLE_LEFT, response=True)
        
        # Assign second device as RIGHT paddle
        self.paddles["RIGHT"] = BleakClient(self.device_addresses[1])
        await self.paddles["RIGHT"].connect()
        await  self.paddles["RIGHT"].write_gatt_char(self.CONFIG_CHAR_UUID, self.PADDLE_RIGHT, response=True)
        
        self.message.CONFIGURED.set()
        logger.info("Connected and configured both paddles")
        
    async def _listen_to_paddles(self):
        """Listen to paddle state changes from connected devices."""
        tasks = []
        for paddle in self.paddles:
            # asyncio.TaskGroup() ?
            task = asyncio.create_task(self._monitor_paddle(paddle))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks)
    
    # TODO: Implement actual monitoring logic
    async def _monitor_paddle(self, paddle):
        pass
    
    # TODO: Implement cleanup logic
    async def _cleanup(self):
        pass