from __future__ import print_function

import os.path
import io
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class GoogleDriveService:
    # If modifying these scopes, delete the file token.json.
    # SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
    SCOPES = ['https://www.googleapis.com/auth/drive']
    GOOGLE_DRIVE_TOKEN_FILE_PATH = "./creds/GoogleDrive/token.json"
    GOOGLE_DRIVE_CREDENTIAL_FILE_PATH = "./creds/GoogleDrive/credentials.json"
    DOWNLOAD_FILE_DIR = "./audio_file/"

    def __init__(self):
        self.credential = self.get_google_drive_cred()
        self.service = build('drive', 'v3', credentials=self.credential)

    def get_google_drive_cred(self):
        credential = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.GOOGLE_DRIVE_TOKEN_FILE_PATH):
            credential = Credentials.from_authorized_user_file(
                self.GOOGLE_DRIVE_TOKEN_FILE_PATH, self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not credential or not credential.valid:
            if credential and credential.expired and credential.refresh_token:
                credential.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.GOOGLE_DRIVE_CREDENTIAL_FILE_PATH, self.SCOPES)
                credential = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.GOOGLE_DRIVE_TOKEN_FILE_PATH, 'w') as token:
                token.write(credential.to_json())
        return credential

    def get_shared_with_me_folder_id(self, folder_name):
        folder_result = self.service.files().list(
            q=f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
        ).execute()
        folder = folder_result.get('files', [])
        folder_id = folder[0].get('id')
        return folder_id

    def get_folder_list(self, folder_id):
        results = self.service.files().list(
            q=f"'{folder_id}' in parents",
            fields="nextPageToken, files(id, name, mimeType)").execute()
        folder = results.get('files', [])
        return folder

    def print_start_download(self, file_name):
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print('\n' + dt_string + ' Start Downloading: ' + file_name)

    def print_finish_download(self, file_name):
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(dt_string + ' Finished Downloading ' + file_name + '\n')

    def download_audio_files(self, file_list):
        print('\nStart downloading audio file to generate video...\n')
        for f in range(0, len(file_list)):
            try:
                if (file_list[f].get('mimeType') == 'audio/mpeg'):
                    f_id = file_list[f].get('id')
                    file_request = self.service.files().get_media(fileId=f_id)
                    fh = open(
                        self.DOWNLOAD_FILE_DIR + file_list[f].get('name'),
                        'wb')
                    self.print_start_download(file_list[f].get('name'))
                    downloader = MediaIoBaseDownload(fh, file_request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        if (done):
                            self.print_finish_download(
                                file_list[f].get('name'))
            except Exception as error:
                print(f'''Audio File Download Error: 
                    {error}
                ''')

    # currently only support spreadsheet, all other mimeType is treated as binary content
    def download_file(self, file):
        file_id = file["id"]
        file_name = file["name"]

        if (file["mimeType"] == 'application/vnd.google-apps.spreadsheet'):
            self.export_document(file_id, file_name)
        else:
            self.download_binary_content(file_id, file_name)

    def download_binary_content(self, file_id, file_name):
        file_request = self.service.files().get_media(fileId=file_id)
        fh = open('./' + file_name, 'wb')

        print('Start Downloading: ' + file_name)
        downloader = MediaIoBaseDownload(fh, file_request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if (done):
                print('Finished Downloading: ' + file_name)

    # Export to excel only
    def export_document(self, file_id, file_name):
        file_request = self.service.files().export_media(
            fileId=file_id,
            mimeType=
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        file_name = file_name + '.xlsx'
        fh = open('./' + file_name, 'wb')
        self.print_start_download(file_name)
        downloader = MediaIoBaseDownload(fh, file_request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if (done):
                self.print_finish_download(file_name)

    def replace_file(self, parent_folder_name, existing_file_id, file_name,
                     file_path, file_type):
        print(
            f'\nUploading {file_name} to Google Drive [{parent_folder_name}]')

        try:
            media = MediaFileUpload(file_path, mimetype=file_type)
            upload_request = self.service.files().update(
                media_body=media, fileId=existing_file_id,
                fields='id').execute()
            print(F'File ID: {upload_request.get("id")}')

        except HttpError as error:
            print(F'An error occurred: {error}')
            upload_request = None

        return upload_request.get('id')
