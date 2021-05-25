from elasticsearch import Elasticsearch
import os

# api_key = (os.environ['ELASTICSEARCH_API_KEY_ID'], os.environ['ELASTICSEARCH_API_KEY_SECRET'])
# cloud_id = os.environ['ELASTICSEARCH_CLOUD_ID']
# indexName = os.environ['ELASTICSEARCH_INDEXNAME']

# def post_elasticsearch(content, api_key=api_key, cloud_id=cloud_id, indexName=indexName):
#     """Post content to elasticsearch"""
#     es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
#     print()
#     print("post_elasticsearch", content)
#     res = es.index(index=indexName, body=content)
#     return res

# def search(query, api_key=api_key, cloud_id=cloud_id, indexName=indexName):
#     """
#     for searching a query from elasticsearch on predefined index
#     """
#     es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
#     res = es.search(index=indexName, body=query)
#     return res

# def mapping_elasticsearch(mapping, api_key=api_key, cloud_id=cloud_id, indexName=indexName):
#     """
#     for creating mapping on predefined index
#     """
#     es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
#     return es.indices.create(index=indexName, ignore=400, body=mapping)


# def delete_index(api_key=api_key, cloud_id=cloud_id, indexName=indexName):
#     es = Elasticsearch(api_key=api_key, cloud_id=cloud_id)
#     return es.indices.delete(index=indexName, ignore=[400, 404])


class ElasticsearchHelper:
    def __init__(self):
        self.indexName = os.environ['ELASTICSEARCH_INDEXNAME']
        self.es = Elasticsearch(api_key = (os.environ['ELASTICSEARCH_API_KEY_ID'], os.environ['ELASTICSEARCH_API_KEY_SECRET']),
                                cloud_id = os.environ['ELASTICSEARCH_CLOUD_ID']
                                )

    def post_document(self, content):
        """
        create a new document in given index
        """
        res = self.es.index(index=self.indexName, body=content)
        return res
    
    def search(self, query):
        """
        search indexName based on query
        """
        return self.es.search(index=self.indexName, body=query)
    
    def create_mapping(self, mapping):
        """
        Create mapping if not already exist else first delete and then recreate
        """
        return self.es.indices.create(index=self.indexName, ignore=400, body=mapping)
    
    def delete_index(self):
        """
        delete the index 
        """
        return self.es.indices.delete(index=self.indexName, ignore=[400, 404])