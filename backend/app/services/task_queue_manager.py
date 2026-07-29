"""
Task Queue Manager.

Abstracts background task processing. Currently uses FastAPI BackgroundTasks 
(or direct async spawning) as the implementation, providing an easy migration 
path to Celery or Redis in the future.
"""

import logging
from typing import Callable, Any, Coroutine
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

class TaskQueueManager:
    """Manages asynchronous tasks, abstracting the underlying queuing mechanism."""

    @staticmethod
    def enqueue_background_task(
        background_tasks: BackgroundTasks,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        **kwargs
    ) -> None:
        """
        Add an async task to the queue. 
        Currently uses FastAPI BackgroundTasks which run after the HTTP response.
        """
        task_name = getattr(func, '__name__', 'unknown_task')
        logger.info(f"TaskQueueManager: Enqueuing background task '{task_name}'")
        
        # Wrapped function to add top-level error handling
        async def _task_wrapper():
            try:
                await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Background task '{task_name}' failed with error: {e}")

        background_tasks.add_task(_task_wrapper)

    @staticmethod
    def enqueue_fire_and_forget(
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        task_name: str | None = None,
        **kwargs
    ) -> None:
        """
        Add an async task immediately to the event loop.
        Useful when BackgroundTasks object isn't available.
        """
        import asyncio
        name = task_name or getattr(func, '__name__', 'unknown_task')
        logger.info(f"TaskQueueManager: Spawning fire-and-forget task '{name}'")
        
        async def _task_wrapper():
            try:
                await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Fire-and-forget task '{name}' failed with error: {e}")

        asyncio.create_task(_task_wrapper(), name=f"task-queue-{name}")
