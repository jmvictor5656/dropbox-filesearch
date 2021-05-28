import logging
import json
from io import BytesIO
import os

from chalicelib import dropbox_s3_file_syncer, elasticsearch, filehandlers

from chalice import Chalice, Rate, CORSConfig
import boto3


app = Chalice(app_name='dropbox-s3-elasticsearch-lambda')
app.log.setLevel(logging.DEBUG)

cors_config = CORSConfig(
    allow_origin='*',
    allow_headers=['X-Special-Header'],
    max_age=600,
    expose_headers=['X-Special-Header'],
    allow_credentials=True
)

@app.schedule(Rate(5, unit=Rate.MINUTES))
def dropbox_s3_sync(event):
    """
    Lambda function to sync the data between dropbox and S3.
    """
    app.log.debug(f"environment keys {os.environ['DROPBOX_ACCESS_TOKEN']}, {os.environ['BUCKET_NAME']}, {os.environ['DROPBOX_DIRECTORY_PATH']}, {os.environ['BUCKET_KEY']}")
    dbx = dropbox_s3_file_syncer.DropboxS3FileSyncer(os.environ['DROPBOX_ACCESS_TOKEN'],
                                                     os.environ['BUCKET_NAME'],
                                                     os.environ['DROPBOX_DIRECTORY_PATH'],
                                                     os.environ['BUCKET_KEY'])
    dbx.download_from_dropbox_and_upload_to_s3()

@app.on_s3_event(bucket=os.environ['BUCKET_NAME'], events=['s3:ObjectCreated:*'])
def s3_to_elasticsearch(event):
    """
    post data from s3 to Elasticsearch in format {'filename': 'abc.pdf', 'content': 'content of file'}
    """
    bucket, file_name = event.bucket, event.key
    _, file_extension = os.path.splitext(file_name)
    s3 = boto3.client('s3')
    
    s3_object = s3.get_object(Bucket=bucket, Key=file_name)
    file = BytesIO(s3_object['Body'].read())
    
    file_content = ''
    print(file_name, file_extension)
    if file_extension == '.pdf':
        file_content = filehandlers.get_pdf_content(file)
    elif file_extension in ('.docx', '.doc'):
        file_content = filehandlers.get_doc_content(file)
    print(file_content)
    
    es = elasticsearch.ElasticsearchHelper()
    res = es.post_document(content = {'filename': file_name, 'content': file_content})
    app.log.info(f'response recieved from elasticsearch {res}')
    return res

@app.route('/search', methods=['POST'], cors=cors_config)
def search_elasticsearch():
    """
    search elasticsearch index based on search query provided as ?search="<text to be searched>" else
    post a search query in json format like 'requests.post(url, headers={'content-type': 'application/json'}, json={"query": {"match_all": {}}})'
    """
    search_query = json.load(open(os.path.join(os.path.dirname(__file__), 'chalicelib', 'config',  'search_query.json')))
    search_text = None

    if app.current_request.query_params:
        search_text = dict(app.current_request.query_params).get('search')
    
    if search_text:
        body = json.loads(json.dumps(search_query).replace("$REPLACE_WITH_SEARCH_TEXT", search_text))
    else:
        body = app.current_request.json_body
    app.log.debug(f"search_elasticsearchAPI{body}")
    
    if not body:
        body = json.loads(json.dumps(search_query).replace("$REPLACE_WITH_SEARCH_TEXT", ''))
    
    es = elasticsearch.ElasticsearchHelper()
    return es.search(body)


@app.route('/delete_index', methods=['DELETE'], cors=cors_config)
def delete_index():
    """
    deletes any index in elasticsearch
    """
    app.log.info("deleting index")
    es = elasticsearch.ElasticsearchHelper()
    return es.delete_index()

@app.route('/create-mapping', methods=['POST'], cors=cors_config)
def create_mapping():
    """
    creates a mapping based on default mapping template unless a template has been provided in json format.
    """
    defalt_mapping = json.load(open(os.path.join(os.path.dirname(__file__), 'chalicelib', 'config',  'index_mapping.json')))
    
    try:
        body = app.current_request.json_body
    except Exception:
        app.log.info("using default mapping template")
        body = None
        
    mapping = body if body else defalt_mapping
    app.log.debug(f"create_mappingAPI# {mapping}")
    es = elasticsearch.ElasticsearchHelper()
    
    return es.create_mapping(mapping)

@app.route('/download/{filename}', methods=['GET'], cors=cors_config)
def download(filename):
    """
    returns a downloadable s3 presigned url for downloading the file with name filename in S3
    """
    filename = filename.replace("%20", " ")
    s3 = boto3.client('s3')
    response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': os.environ.get('BUCKET_NAME'),
                                                            'Key': filename,
                                                            },
                                                    ExpiresIn=5*60,  HttpMethod='GET')
    
    return response
