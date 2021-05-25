from elasticsearch import Elasticsearch
import os

api_key = (os.environ['ELASTICSEARCH_API_KEY_ID'], os.environ['ELASTICSEARCH_API_KEY_SECRET'])
cloud_id = os.environ['ELASTICSEARCH_CLOUD_ID']
indexName = os.environ['ELASTICSEARCH_INDEXNAME']

def post_elasticsearch(content, api_key=api_key, cloud_id=cloud_id, indexName=indexName):
    """Post content to elasticsearch"""
    es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
    print()
    print("post_elasticsearch", content)
    res = es.index(index=indexName, body=content)
    return res

def search(query, api_key=api_key, cloud_id=cloud_id, indexName=indexName):
    """"""
    es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
    res = es.search(index=indexName, body=query)
    return res

def mapping_elasticsearch(mapping, api_key=api_key, cloud_id=cloud_id, indexName=indexName):
    es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
    return es.indices.create(index=indexName, ignore=400, body=mapping)


def delete_index(api_key=api_key, cloud_id=cloud_id, indexName=indexName):
    es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
    return es.indices.delete(index=indexName, ignore=[400, 404])

