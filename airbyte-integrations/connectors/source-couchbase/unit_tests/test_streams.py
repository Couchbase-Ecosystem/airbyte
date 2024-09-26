#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#

from unittest.mock import MagicMock, patch

import pytest
from source_couchbase.streams import Buckets, Scopes, Collections, Documents
from source_couchbase.queries import (
    get_buckets_query,
    get_scopes_query,
    get_collections_query,
    get_documents_query,
    get_buckets_list_query
)

@pytest.fixture
def mock_cluster():
    return MagicMock()

@pytest.mark.parametrize("stream_class", [Buckets, Scopes, Collections, Documents])
def test_stream_initialization(stream_class, mock_cluster):
    stream = stream_class(mock_cluster)
    assert stream.cluster == mock_cluster

def test_buckets_read_records(mock_cluster):
    mock_cluster.query.return_value = [
        {"name": "bucket1", "bucketType": "membase", "numReplicas": 1, "ramQuota": 100, "replicaNumber": 1},
        {"name": "bucket2", "bucketType": "membase", "numReplicas": 1, "ramQuota": 200, "replicaNumber": 1}
    ]
    
    buckets_stream = Buckets(mock_cluster)
    records = list(buckets_stream.read_records(sync_mode=None))
    
    assert len(records) == 2
    assert records[0]["name"] == "bucket1"
    assert records[1]["name"] == "bucket2"
    mock_cluster.query.assert_called_once_with(get_buckets_query())

def test_scopes_read_records(mock_cluster):
    mock_cluster.query.return_value = [
        {"bucket": "bucket1", "name": "scope1", "uid": "uid1"},
        {"bucket": "bucket1", "name": "scope2", "uid": "uid2"}
    ]
    
    scopes_stream = Scopes(mock_cluster)
    records = list(scopes_stream.read_records(sync_mode=None))
    
    assert len(records) == 2
    assert records[0]["bucket"] == "bucket1"
    assert records[0]["name"] == "scope1"
    assert records[1]["name"] == "scope2"
    mock_cluster.query.assert_called_once_with(get_scopes_query())

def test_collections_read_records(mock_cluster):
    mock_cluster.query.return_value = [
        {"bucket": "bucket1", "scope": "scope1", "name": "collection1", "uid": "uid1"},
        {"bucket": "bucket1", "scope": "scope1", "name": "collection2", "uid": "uid2"}
    ]
    
    collections_stream = Collections(mock_cluster)
    records = list(collections_stream.read_records(sync_mode=None))
    
    assert len(records) == 2
    assert records[0]["bucket"] == "bucket1"
    assert records[0]["scope"] == "scope1"
    assert records[0]["name"] == "collection1"
    assert records[1]["name"] == "collection2"
    mock_cluster.query.assert_called_once_with(get_collections_query())

def test_documents_read_records(mock_cluster):
    mock_cluster.query.side_effect = [
        [{"name": "bucket1"}],  # Mocking buckets_list_query result
        [  # Mocking documents_query result
            {"id": "doc1", "bucket": "bucket1", "scope": "scope1", "collection": "collection1", "content": {"key": "value"}, "expiration": 0, "flags": 0, "cas": "123456"},
            {"id": "doc2", "bucket": "bucket1", "scope": "scope1", "collection": "collection1", "content": {"key2": "value2"}, "expiration": 0, "flags": 0, "cas": "789012"}
        ]
    ]
    
    mock_bucket = MagicMock()
    mock_scope = MagicMock()
    mock_collection = MagicMock()
    
    # Set specific names for bucket, scope, and collection
    mock_bucket.name = "bucket1"
    mock_scope.name = "scope1"
    mock_collection.name = "collection1"
    
    mock_bucket.collections.return_value.get_all_scopes.return_value = [mock_scope]
    mock_scope.collections = [mock_collection]
    mock_cluster.bucket.return_value = mock_bucket
    
    documents_stream = Documents(mock_cluster)
    records = list(documents_stream.read_records(sync_mode=None))
    
    assert len(records) == 2
    assert records[0]["id"] == "doc1"
    assert records[0]["bucket"] == "bucket1"
    assert records[0]["scope"] == "scope1"
    assert records[0]["collection"] == "collection1"
    assert records[0]["content"] == {"key": "value"}
    assert records[0]["metadata"]["cas"] == "123456"
    
    assert mock_cluster.query.call_count == 2
    mock_cluster.query.assert_any_call(get_buckets_list_query())
    expected_query = get_documents_query().format("bucket1", "scope1", "collection1")
    mock_cluster.query.assert_any_call(expected_query)

@pytest.mark.parametrize("stream_class", [Buckets, Scopes, Collections, Documents])
def test_stream_primary_key(stream_class, mock_cluster):
    stream = stream_class(mock_cluster)
    assert stream.primary_key is not None

@pytest.mark.parametrize("stream_class,expected_name", [
    (Buckets, "buckets"),
    (Scopes, "scopes"),
    (Collections, "collections"),
    (Documents, "documents")
])
def test_stream_name(stream_class, expected_name, mock_cluster):
    stream = stream_class(mock_cluster)
    assert stream.name == expected_name

def test_documents_json_schema(mock_cluster):
    documents_stream = Documents(mock_cluster)
    schema = documents_stream.json_schema
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "id" in schema["properties"]
    assert "bucket" in schema["properties"]
    assert "scope" in schema["properties"]
    assert "collection" in schema["properties"]
    assert "content" in schema["properties"]
    assert "metadata" in schema["properties"]
