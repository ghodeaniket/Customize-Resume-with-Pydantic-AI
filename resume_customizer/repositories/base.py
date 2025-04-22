"""Base repository for the Resume Customizer application.

This module defines the base repository class for data operations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel

from resume_customizer.core.logging import app_logger as logger


# Define a type variable for the model
T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository for data operations.
    
    This class defines the base interface for repositories. For Phase 1,
    this will use in-memory storage. In future phases, we can extend this
    to use a database.
    
    Attributes:
        model_class: The Pydantic model class for the repository
        _items: In-memory storage for items
    """
    
    def __init__(self, model_class: Type[T]):
        """Initialize the repository.
        
        Args:
            model_class: The Pydantic model class for the repository
        """
        self.model_class = model_class
        self._items: Dict[str, T] = {}
    
    async def create(self, id: str, item: T) -> T:
        """Create a new item.
        
        Args:
            id: The ID for the item
            item: The item to create
            
        Returns:
            T: The created item
        """
        logger.debug(f"Creating {self.model_class.__name__} with ID {id}")
        self._items[id] = item
        return item
    
    async def get(self, id: str) -> Optional[T]:
        """Get an item by ID.
        
        Args:
            id: The ID of the item
            
        Returns:
            Optional[T]: The item if found, None otherwise
        """
        logger.debug(f"Getting {self.model_class.__name__} with ID {id}")
        return self._items.get(id)
    
    async def update(self, id: str, item: T) -> Optional[T]:
        """Update an item.
        
        Args:
            id: The ID of the item
            item: The updated item
            
        Returns:
            Optional[T]: The updated item if found, None otherwise
        """
        logger.debug(f"Updating {self.model_class.__name__} with ID {id}")
        if id in self._items:
            self._items[id] = item
            return item
        return None
    
    async def delete(self, id: str) -> bool:
        """Delete an item.
        
        Args:
            id: The ID of the item
            
        Returns:
            bool: True if the item was deleted, False otherwise
        """
        logger.debug(f"Deleting {self.model_class.__name__} with ID {id}")
        if id in self._items:
            del self._items[id]
            return True
        return False
    
    async def list(self) -> List[T]:
        """List all items.
        
        Returns:
            List[T]: All items in the repository
        """
        logger.debug(f"Listing all {self.model_class.__name__} items")
        return list(self._items.values())
