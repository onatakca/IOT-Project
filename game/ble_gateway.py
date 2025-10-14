import asyncio
import logging
import threading
from bleak import BleakClient, BleakScanner

logger = logging.getLogger("ble_gateway")

class BleGateway:
    """
    BLE Gateway that runs in its own thread and communicates with the game via a queue.
    Sends paddle state updates (left_paddle, right_paddle) to the game.
    """
    
    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.device_addresses = []
        self.running = False
        self.thread = None
        self.clients = []
        
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
            
        # TODO: Connect to the devices, configure them as either left or right and start listening
        
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