from urllib.error import HTTPError
from GoogleDriveService import GoogleDriveService
from VideoGenerator import VideoGenerator
from YouTubeVideoUploader import YouTubeVideoUploader

from PIL import Image, ImageDraw, ImageFont
from IPython.display import display
from moviepy.editor import *
import pandas as pd

# CONSTANT
RAW_DIR = './audio_file/'
OUTPUT_DIR = './output/'
AUDIO_MESSAGE_LIST_FILE_NAME = 'audio_message_list'
AUDIO_MESSAGE_LIST_MIME_TYPE = 'application/vnd.google-apps.spreadsheet'
AUDIO_FOLDER_NAME = 'pulpit_2022_test'
PRINT_LINE_SEP = '=================================================================================================================='

# Excel Column Naming
UPLOAD_START_CN = 'Sys_Start_Video_Upload_Datetime'
UPLOAD_END_CN = 'Sys_End_Video_Upload_Datetime'
GEN_VIDEO_START_CN = 'Sys_Start_Generate_Video_Datetime'
GEN_VIDEO_END_CN = 'Sys_End_Generate_Video_Datetime'


def update_audio_message_list_excel_file(row, df, dt):
    for index in df.index:
        if df.loc[index, "File_Name"] == row["File_Name"]:
            if dt["generate_video_start"] != None:
                df.loc[index, GEN_VIDEO_START_CN] = dt[
                    "generate_video_start"].strftime("%d/%m/%Y %H:%M:%S")

            if dt["generate_video_end"] != None:
                df.loc[index,
                       GEN_VIDEO_END_CN] = dt["generate_video_end"].strftime(
                           "%d/%m/%Y %H:%M:%S")

            if dt["upload_start"] != None:
                df.loc[index, UPLOAD_START_CN] = dt["upload_start"].strftime(
                    "%d/%m/%Y %H:%M:%S")

            if dt["upload_end"] != None:
                df.loc[index, UPLOAD_END_CN] = dt["upload_end"].strftime(
                    "%d/%m/%Y %H:%M:%S")

            if dt["url"] != None:
                df.loc[index, "URL"] = dt["url"]
            return df


def get_file_from_folder_list(file_name, mime_type, folder_list):
    for x in folder_list:
        if (x["name"] == file_name and x["mimeType"] == mime_type):
            return x
    return None


def filter_not_uploaded_recording(df, folder_list):
    not_uploaded_recording_list = []
    df = df.loc[(df[UPLOAD_START_CN] == '') | (df[UPLOAD_END_CN] == '') |
                (df['URL'] == '')]
    for index, row in df.iterrows():
        f = get_file_from_folder_list(row["File_Name"], "audio/mpeg",
                                      folder_list)
        if (f != None):
            not_uploaded_recording_list.append(f)
    return not_uploaded_recording_list, df


def filter_not_video_generated_recording(df, folder_list):
    not_video_generated_recording_list = []
    df = df.loc[(df[GEN_VIDEO_START_CN] == '') | (df[GEN_VIDEO_END_CN] == '') |
                (df['URL'] == '')]
    for index, row in df.iterrows():
        f = get_file_from_folder_list(row["File_Name"], "audio/mpeg",
                                      folder_list)
        if (f != None):
            not_video_generated_recording_list.append(f)
    return not_video_generated_recording_list, df


def print_df(title, df):
    print(f'\n{title}\n')
    display(df)
    print('\n')


def print_process(section, title):
    print('\n' + PRINT_LINE_SEP)
    print(f'Part {section}: {title}')
    print(PRINT_LINE_SEP + '\n')


def main():
    google_drive_service = GoogleDriveService()

    try:
        # Get audio files list from folder for comparison
        audio_folder_id = google_drive_service.get_shared_with_me_folder_id(
            AUDIO_FOLDER_NAME)
        audio_folder_list = google_drive_service.get_folder_list(
            audio_folder_id)
        audio_message_excel_file = get_file_from_folder_list(
            AUDIO_MESSAGE_LIST_FILE_NAME, AUDIO_MESSAGE_LIST_MIME_TYPE,
            audio_folder_list)
        if (audio_message_excel_file != None):
            print_process(
                "1",
                "Download audio_message_list excel file from Google Drive shared folder"
            )
            # Download the audio_message_list.xlsx file
            google_drive_service.download_file(audio_message_excel_file)

            print_process("2", "Compare and filter recordings")
            # Compare and filter for not uploaded sermon recordings
            df = pd.read_excel("./" + AUDIO_MESSAGE_LIST_FILE_NAME + '.xlsx',
                               header=0,
                               keep_default_na=False)

            not_video_generated_gd_file_list, not_video_generated_recording_df = filter_not_video_generated_recording(
                df, audio_folder_list)
            not_uploaded_recording_gd_file_list, not_uploaded_recording_df = filter_not_uploaded_recording(
                df, audio_folder_list)

            print_df('Recording without video',
                     not_video_generated_recording_df)
            print_df('Recording not uploaded', not_uploaded_recording_df)


            if len(not_video_generated_recording_df.index) == 0:
                print_process("Note", "All video files have been generated")
            if len(not_uploaded_recording_df.index) == 0:
                print_process("Note", "All sermon have ben uploaded, refer to the excel file for the URLs")


            print_process("3", "Download sermon recordings that have not generated its video file")
            # Download not uploaded sermon recordings
            google_drive_service.download_audio_files(not_video_generated_gd_file_list)

            print_process("4", "Generate video files and specification -> Upload generated video to YouTube")
            video_generator = VideoGenerator(RAW_DIR, OUTPUT_DIR)
            youtube_uploader = YouTubeVideoUploader()
            for index, row in not_video_generated_recording_df.iterrows():
                # Generate video and spec
                try:
                    video_spec, generate_video_start, generate_video_end = video_generator.generate_video_files(row)
                    print(video_spec)
                    df = update_audio_message_list_excel_file(row, df, dict(
                        upload_start = None,
                        upload_end = None,
                        url = None,
                        generate_video_start = generate_video_start,
                        generate_video_end = generate_video_end
                    ))
                except Exception as error:
                    print(f'''
                    Failed to generate video file, refer to error below:
                    {error}''')

                # Upload one video at a time
                try:
                    url, upload_start, upload_end = youtube_uploader.upload_video(video_spec)
                     # Upload audio_message_list excel file in Google Drive
                    df = update_audio_message_list_excel_file(row, df, dict(
                        upload_start = upload_start,
                        upload_end = upload_end,
                        url = url,
                        generate_video_start = None,
                        generate_video_end = None
                    ))
                except Exception as error:
                    print(f'''
                    Failed to upload video to YouTube, refer to error below:
                    {error}''')

                # Removed unnamed column and save to excel file
                df = df.loc[:,~df.columns.str.match("Unnamed")]
                df.to_excel('./' + AUDIO_MESSAGE_LIST_FILE_NAME + '.xlsx', index=False)
                try:
                    google_drive_service.replace_file(parent_folder_name = AUDIO_FOLDER_NAME
                                                    , existing_file_id = audio_message_excel_file["id"]
                                                    , file_name = audio_message_excel_file["name"]
                                                    , file_path = './' + AUDIO_MESSAGE_LIST_FILE_NAME + '.xlsx'
                                                    , file_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    display(df)
                except Exception as error:
                    print(f'''
                    Failed to replace audio_message_list.xlsx in Google Drive, refer to error below:
                    {error}''')

            print_process("5", "Finish sermon processing")

        else:
            print_process(
                "1",
                f'{AUDIO_MESSAGE_LIST_FILE_NAME}.xlsx can\'t be found in {AUDIO_FOLDER_NAME} in Google Drive. Sermon is not processed.'
            )

    except HTTPError as error:
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()