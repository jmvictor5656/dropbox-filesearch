import boto3
import os


class DropboxS3FileSyncer:
    """
    Class to sync the files from dropbox to S3 and only upload those
    files which are not already available in S3 bucket
    """
    def __init__(self, token, destination_bucket, path='', s3_path='') -> None:
        """
        token: dropbox token
        destination_bucket: bucket name where files from dropbox will be uploaded for processing
        path: path in dropbox from where files need to be picked
        s3_path: prefix in s3 bucket
        """
        import dropbox
        self.dbx = dropbox.Dropbox(token)
        self.path = path
        self.s3_resource = boto3.resource('s3')
        self.destination_bucket = destination_bucket
        self.client = boto3.client('s3')
        self.s3_path = s3_path

    @staticmethod
    def _process_dropbox_files(files) -> list:
        """
        Returns list of file path in dropbox
        """
        paths = []

        for file in files:
            paths.append(file.path_display)
        return paths

    def _get_dropbox_file_paths(self) -> list:
        """
        Returns list of file paths present in self.path
        """
        files = self.dbx.files_list_folder(self.path)
        paths = self._process_dropbox_files(files.entries)
        
        if files.has_more:
            files = self.dxb.files_list_folder_continue(files.cursor)
            paths += self._process_dropbox_files(files.entries)
        return paths

    def download_from_dropbox_and_upload_to_s3(self):#, dropbox_file_paths):
        """
        it reads filestream from dropbox and upload to s3
        """
        dropbox_file_paths = self._filter_files()

        for file in dropbox_file_paths:
            _, f = self.dbx.files_download(file)
            print(f'uploading file {file}')
            self.s3_resource.Bucket(self.destination_bucket).put_object(
                Key=os.path.join(self.s3_path, os.path.basename(file)),
                Body=f.content
            )

    def _filter_files(self) -> list:
        """
        returns list of files that are present in dropbox but not in s3
        """
        all_s3_files = self._get_all_files_from_s3_path()
        dropbox_files = self._get_dropbox_file_paths()

        files_to_be_downloaded = list(filter(lambda file: os.path.basename(file) not in all_s3_files, dropbox_files))
        return files_to_be_downloaded

    def _get_all_files_from_s3_path(self):
        """
        Returns a list of all files present in self.s3_path
        """
        file_names = []
        continuation_token = None
        kwargs = {"Bucket": self.destination_bucket, 'Prefix': self.path}

        while True:
            if continuation_token:
                kwargs['ContinuationToken'] = continuation_token
            response = self.client.list_objects_v2(**kwargs)
            continuation_token = response.get('NextContinuationToken')

            get_res_obj_destination = response.get('Contents', [])
            # get all files which are already present in destination bucket
            for obj in get_res_obj_destination:
                file_name = str(os.path.basename(obj['Key']))
                file_names.append(file_name)

            if not response.get('IsTruncated'):  # At the end of the list?
                break
        return file_names