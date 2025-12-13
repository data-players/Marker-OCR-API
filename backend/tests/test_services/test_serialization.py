"""
Unit tests for the serialization utilities.
Tests the serialize_pydantic_objects function to ensure proper JSON serialization.
"""

import pytest
import json
from pydantic import BaseModel
from app.services.document_parser import serialize_pydantic_objects


class MockImage:
    """Mock PIL Image object."""
    def __init__(self, width=100, height=200):
        self.size = (width, height)
        self.format = "PNG"
        self.mode = "RGB"


class NestedModel(BaseModel):
    """Nested Pydantic model for testing."""
    field1: str
    field2: int


class MockPydanticObject(BaseModel):
    """Mock Pydantic object similar to Marker's objects."""
    block_type: str
    id: str
    content: str
    nested: NestedModel
    items: list


class TestSerializePydanticObjects:
    """Test suite for serialize_pydantic_objects function."""
    
    def test_serialize_basic_types(self):
        """Test serialization of basic Python types."""
        # Strings
        assert serialize_pydantic_objects("hello") == "hello"
        
        # Numbers
        assert serialize_pydantic_objects(42) == 42
        assert serialize_pydantic_objects(3.14) == 3.14
        
        # Booleans
        assert serialize_pydantic_objects(True) is True
        assert serialize_pydantic_objects(False) is False
        
        # None
        assert serialize_pydantic_objects(None) is None
    
    def test_serialize_list(self):
        """Test serialization of lists."""
        data = [1, "two", 3.0, True, None]
        result = serialize_pydantic_objects(data)
        assert result == data
        assert isinstance(result, list)
    
    def test_serialize_dict(self):
        """Test serialization of dictionaries."""
        data = {
            "key1": "value1",
            "key2": 42,
            "key3": True
        }
        result = serialize_pydantic_objects(data)
        assert result == data
        assert isinstance(result, dict)
    
    def test_serialize_pil_image(self):
        """Test serialization of PIL Image objects."""
        image = MockImage(width=800, height=600)
        result = serialize_pydantic_objects(image)
        
        assert isinstance(result, dict)
        assert result["width"] == 800
        assert result["height"] == 600
        assert result["format"] == "PNG"
        assert result["mode"] == "RGB"
    
    def test_serialize_pydantic_model(self):
        """Test serialization of Pydantic models."""
        nested = NestedModel(field1="test", field2=123)
        model = MockPydanticObject(
            block_type="Document",
            id="/document/0",
            content="Test content",
            nested=nested,
            items=["item1", "item2"]
        )
        
        result = serialize_pydantic_objects(model)
        
        assert isinstance(result, dict)
        assert result["block_type"] == "Document"
        assert result["id"] == "/document/0"
        assert result["content"] == "Test content"
        assert isinstance(result["nested"], dict)
        assert result["nested"]["field1"] == "test"
        assert result["nested"]["field2"] == 123
        assert result["items"] == ["item1", "item2"]
    
    def test_serialize_complex_nested_structure(self):
        """Test serialization of complex nested structures."""
        nested = NestedModel(field1="nested", field2=456)
        model = MockPydanticObject(
            block_type="Page",
            id="/page/0",
            content="Page content",
            nested=nested,
            items=["a", "b"]
        )
        
        data = {
            "document": model,
            "images": {
                "img1": MockImage(100, 200),
                "img2": MockImage(300, 400)
            },
            "metadata": {
                "author": "Test",
                "pages": 10,
                "nested_model": nested
            },
            "items": [model, "text", 123]
        }
        
        result = serialize_pydantic_objects(data)
        
        # Verify structure
        assert isinstance(result, dict)
        assert isinstance(result["document"], dict)
        assert result["document"]["block_type"] == "Page"
        
        # Verify images
        assert isinstance(result["images"], dict)
        assert result["images"]["img1"]["width"] == 100
        assert result["images"]["img2"]["width"] == 300
        
        # Verify metadata
        assert result["metadata"]["author"] == "Test"
        assert result["metadata"]["pages"] == 10
        assert isinstance(result["metadata"]["nested_model"], dict)
        
        # Verify list with mixed types
        assert isinstance(result["items"], list)
        assert len(result["items"]) == 3
        assert isinstance(result["items"][0], dict)
    
    def test_json_serializable(self):
        """Test that serialized output is JSON serializable."""
        nested = NestedModel(field1="test", field2=789)
        model = MockPydanticObject(
            block_type="Document",
            id="/doc/1",
            content="Content",
            nested=nested,
            items=["x", "y", "z"]
        )
        
        data = {
            "model": model,
            "image": MockImage(500, 600),
            "list": [model, nested],
            "nested_dict": {
                "key1": model,
                "key2": MockImage(200, 300)
            }
        }
        
        result = serialize_pydantic_objects(data)
        
        # This should not raise an exception
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # Verify we can reload it
        reloaded = json.loads(json_str)
        assert reloaded["model"]["block_type"] == "Document"
        assert reloaded["image"]["width"] == 500
    
    def test_serialize_list_of_pydantic_objects(self):
        """Test serialization of lists containing Pydantic objects (like Marker's children)."""
        nested1 = NestedModel(field1="first", field2=1)
        nested2 = NestedModel(field1="second", field2=2)
        
        obj1 = MockPydanticObject(
            block_type="Block1",
            id="/block/1",
            content="Content 1",
            nested=nested1,
            items=["a"]
        )
        obj2 = MockPydanticObject(
            block_type="Block2",
            id="/block/2",
            content="Content 2",
            nested=nested2,
            items=["b"]
        )
        
        # This mimics Marker's children structure
        children = [obj1, obj2]
        
        result = serialize_pydantic_objects(children)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert isinstance(result[1], dict)
        assert result[0]["block_type"] == "Block1"
        assert result[1]["block_type"] == "Block2"
        
        # Ensure it's JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
    
    def test_serialize_preserves_none_values(self):
        """Test that None values are preserved."""
        data = {
            "key1": "value",
            "key2": None,
            "key3": [1, None, 3]
        }
        
        result = serialize_pydantic_objects(data)
        
        assert result["key1"] == "value"
        assert result["key2"] is None
        assert result["key3"][1] is None
    
    def test_serialize_empty_structures(self):
        """Test serialization of empty structures."""
        assert serialize_pydantic_objects([]) == []
        assert serialize_pydantic_objects({}) == {}
        assert serialize_pydantic_objects("") == ""
    
    def test_redis_compatible_output(self):
        """Test that output is compatible with Redis storage (via JSON)."""
        from app.services.redis_service import RedisService
        import uuid
        
        # Create complex structure
        nested = NestedModel(field1="redis_test", field2=999)
        model = MockPydanticObject(
            block_type="TestBlock",
            id="/test/0",
            content="Redis test content",
            nested=nested,
            items=["redis", "test"]
        )
        
        data = {
            "rich_structure": {
                "block_type": "Document",
                "children": [model, model]
            },
            "images": {
                "img1": MockImage(123, 456)
            },
            "metadata": {
                "test": "value",
                "nested": nested
            }
        }
        
        # Serialize
        serialized = serialize_pydantic_objects(data)
        
        # Verify JSON serialization works (this is what Redis does internally)
        json_str = json.dumps(serialized)
        reloaded = json.loads(json_str)
        
        assert reloaded["rich_structure"]["block_type"] == "Document"
        assert len(reloaded["rich_structure"]["children"]) == 2
        assert reloaded["images"]["img1"]["width"] == 123
        assert reloaded["metadata"]["nested"]["field1"] == "redis_test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


