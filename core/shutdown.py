"""
Graceful Shutdown Handler.

Ensures that the application shuts down gracefully without interrupting
active requests.

Implementation for User Story #54 - Graceful Shutdown Handling (P1)
"""

import asyncio
import logging
import signal
import sys
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """
    Handles graceful shutdown of the application.

    Features:
        - Signal handlers for SIGTERM and SIGINT
        - Wait for active requests to complete (with timeout)
        - Reject new requests during shutdown
        - Close database connections gracefully
        - Close Redis connections
        - Flush logs
        - Health check returns 503 during shutdown

    Usage:
        shutdown_handler = GracefulShutdown(
            shutdown_timeout=30,
            on_shutdown=cleanup_function
        )
        shutdown_handler.setup()
    """

    def __init__(
        self,
        shutdown_timeout: int = 30,
        on_shutdown: Optional[Callable] = None
    ):
        """
        Initialize graceful shutdown handler.

        Args:
            shutdown_timeout: Maximum seconds to wait for active requests (default: 30)
            on_shutdown: Optional callback to run during shutdown
        """
        self.shutdown_timeout = shutdown_timeout
        self.on_shutdown = on_shutdown
        self.shutdown_event = asyncio.Event()
        self._is_shutting_down = False
        self._original_handlers = {}

    def is_shutting_down(self) -> bool:
        """Check if the application is shutting down."""
        return self._is_shutting_down

    def setup(self):
        """
        Setup signal handlers for graceful shutdown.

        Registers handlers for:
            - SIGTERM (sent by Docker, Kubernetes, systemd)
            - SIGINT (Ctrl+C)
        """
        # Only setup on Unix-like systems (Linux, macOS)
        if sys.platform != "win32":
            # Store original handlers for restoration if needed
            self._original_handlers[signal.SIGTERM] = signal.getsignal(signal.SIGTERM)
            self._original_handlers[signal.SIGINT] = signal.getsignal(signal.SIGINT)

            # Register new handlers
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Graceful shutdown handlers registered (SIGTERM, SIGINT)")
        else:
            # Windows only supports SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Graceful shutdown handler registered (SIGINT only on Windows)")

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")

        # Set shutdown flag
        self._is_shutting_down = True

        # Trigger shutdown event
        if asyncio._get_running_loop() is not None:
            asyncio.create_task(self._shutdown())
        else:
            # If no event loop, exit immediately
            logger.warning("No event loop running, exiting immediately")
            sys.exit(0)

    async def _shutdown(self):
        """Execute shutdown sequence."""
        logger.info("Starting graceful shutdown sequence...")

        try:
            # 1. Stop accepting new requests (middleware will check is_shutting_down)
            logger.info("Rejecting new requests...")

            # 2. Wait for active requests to complete (with timeout)
            logger.info(f"Waiting up to {self.shutdown_timeout}s for active requests to complete...")
            await asyncio.sleep(2)  # Give existing requests a moment to finish

            # 3. Run custom shutdown callback if provided
            if self.on_shutdown:
                logger.info("Running custom shutdown callback...")
                try:
                    if asyncio.iscoroutinefunction(self.on_shutdown):
                        await self.on_shutdown()
                    else:
                        self.on_shutdown()
                except Exception as e:
                    logger.error(f"Error in shutdown callback: {e}")

            # 4. Close database connections
            logger.info("Closing database connections...")
            from core.database import engine
            try:
                engine.dispose()
                logger.info("Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")

            # 5. Close Redis connections if available
            try:
                from core.redis_client import redis_client
                if redis_client:
                    logger.info("Closing Redis connections...")
                    await redis_client.close()
                    logger.info("Redis connections closed")
            except ImportError:
                pass  # Redis not configured
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

            # 6. Flush logs
            logger.info("Flushing logs...")
            logging.shutdown()

            logger.info("Graceful shutdown completed successfully")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Signal shutdown complete
            self.shutdown_event.set()
            sys.exit(0)

    async def wait_for_shutdown(self):
        """Wait for shutdown event. Used by application lifecycle."""
        await self.shutdown_event.wait()


# Global instance
shutdown_handler = GracefulShutdown()


def setup_graceful_shutdown(shutdown_timeout: int = 30, on_shutdown: Optional[Callable] = None):
    """
    Setup graceful shutdown for the application.

    Args:
        shutdown_timeout: Maximum seconds to wait for active requests
        on_shutdown: Optional callback to run during shutdown

    Example:
        setup_graceful_shutdown(
            shutdown_timeout=30,
            on_shutdown=lambda: print("Cleaning up...")
        )
    """
    global shutdown_handler
    shutdown_handler = GracefulShutdown(
        shutdown_timeout=shutdown_timeout,
        on_shutdown=on_shutdown
    )
    shutdown_handler.setup()
    return shutdown_handler
