from chalice import Chalice, Rate
from chalicelib import dropbox_s3_file_syncer, elasticsearch, filehandlers
import os
import boto3
from io import BytesIO
import logging
import json

# TODO:
#1. ACCESS_LEY, SECRET_KEY_FIX

app = Chalice(app_name='dropbox-s3-elasticsearch-lambda')
app.log.setLevel(logging.DEBUG)

@app.schedule(Rate(2, unit=Rate.HOURS))
def dropbox_s3_sync(event):
    app.log.debug(f"environment keys {os.environ['DROPBOX_ACCESS_TOKEN']}, {os.environ['BUCKET_NAME']}, {os.environ['DROPBOX_DIRECTORY_PATH']}, {os.environ['BUCKET_KEY']}")
    dbx = dropbox_s3_file_syncer.DropboxS3FileSyncer(os.environ['DROPBOX_ACCESS_TOKEN'],
                                                     os.environ['BUCKET_NAME'],
                                                     os.environ['DROPBOX_DIRECTORY_PATH'],
                                                     os.environ['BUCKET_KEY'])
    dbx.download_from_dropbox_and_upload_to_s3()

@app.on_s3_event(bucket=os.environ['BUCKET_NAME'], events=['s3:ObjectCreated:*'])
def s3_to_elasticsearch(event):
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
    elasticsearch.post_elasticsearch(content = {'filename': file_name, 'content': file_content})


@app.route('/search', methods=['POST'])
def search_elasticsearch():
    import pdb;pdb.set_trace()
    search_query = json.load(open(os.path.join(os.path.dirname(__file__), 'chalicelib', 'config',  'search_query.json')))
    search_text = None
    
    if app.current_request.query_params:
        search_text = dict(app.current_request.query_params).get('search')
    
    if search_text:
        body = json.loads(json.dumps(search_query).replace("$REPLACE_WITH_SEARCH_TEXT", search_text))
    else:
        body = app.current_request.json_body
    app.log.debug(f"search_elasticsearchAPI{body}")
    
    # print(body)
    # query = body['search']
    return elasticsearch.search(body)

@app.route('/delete_index', methods=['DELETE'])
def delete_index():
    app.log.info("deleting index")
    return elasticsearch.delete_index()

@app.route('/create-mapping', methods=['POST'])
def create_mapping():
    import pdb;pdb.set_trace()
    defalt_mapping = json.load(open(os.path.join(os.path.dirname(__file__), 'chalicelib', 'config',  'index_mapping.json')))
    
    try:
        body = app.current_request.json_body
    except Exception:
        app.log.info("using default mapping template")
        body = None
        
    mapping = body if body else defalt_mapping
    # mapping = body['mapping']
    app.log.debug(f"create_mappingAPI# {mapping}")
    return elasticsearch.mapping_elasticsearch(mapping)
