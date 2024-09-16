"""A YouTube Client"""

import http.client
import os
import random
import sys
import time
from datetime import datetime

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


class YouTubeClient:
    """
    # YouTube API Quota
    # https://developers.google.com/youtube/v3/determine_quota_cost"""

    id = ""

    # Explicitly tell the underlying HTTP transport library not to retry, since
    # we are handling retry logic ourselves.
    httplib2.RETRIES = 1

    # Maximum number of times to retry before giving up.
    MAX_RETRIES = 10

    # Always retry when these exceptions are raised.
    RETRIABLE_EXCEPTIONS = (
        httplib2.HttpLib2Error,
        IOError,
        http.client.NotConnected,
        http.client.IncompleteRead,
        http.client.ImproperConnectionState,
        http.client.CannotSendRequest,
        http.client.CannotSendHeader,
        http.client.ResponseNotReady,
        http.client.BadStatusLine,
    )

    # Always retry when an apiclient.errors.HttpError with one of these status
    # codes is raised.
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

    # The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
    # the OAuth 2.0 information for this application, including its client_id and
    # client_secret. You can acquire an OAuth 2.0 client ID and client secret from
    # the Google API Console at
    # https://console.cloud.google.com/.
    # Please ensure that you have enabled the YouTube Data API for your project.
    # For more information about using OAuth2 to access the YouTube Data API, see:
    #   https://developers.google.com/youtube/v3/guides/authentication
    # For more information about the client_secrets.json file format, see:
    #   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    CLIENT_SECRETS_FILE = "./creds/client_secrets.json"

    # This OAuth 2.0 access scope allows an application to upload files to the
    # authenticated user's YouTube channel, but doesn't allow other types of access.
    YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    # This variable defines a message to display if the CLIENT_SECRETS_FILE is
    # missing.
    MISSING_CLIENT_SECRETS_MESSAGE = """
    WARNING: Please configure OAuth 2.0

    To make this sample run you will need to populate the client_secrets.json file
    found at:

    %s

    with information from the API Console
    https://console.cloud.google.com/

    For more information about the client_secrets.json file format, please visit:
    https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    """ % os.path.abspath(
        os.path.join(os.path.abspath(""), CLIENT_SECRETS_FILE)
    )

    VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

    def upload_video(self, option):
        """_summary_

        Args:
            option (_type_): _description_

        Returns:
            _type_: _description_
        """
        argparser.add_argument("--file", help="Video file to upload")
        argparser.add_argument("--title", help="Video title", default="")
        argparser.add_argument("--description", help="Video description", default="")
        argparser.add_argument(
            "--category",
            default="22",
            help="Numeric video category. "
            + "See https://developers.google.com/youtube/v3/docs/videoCategories/list",
        )
        argparser.add_argument(
            "--keywords", help="Video keywords, comma separated", default=""
        )
        argparser.add_argument(
            "--privacyStatus",
            choices=self.VALID_PRIVACY_STATUSES,
            default=self.VALID_PRIVACY_STATUSES[0],
            help="Video privacy status.",
        )
        args = argparser.parse_args()

        args.file = option.file
        args.title = option.title
        args.description = option.description
        args.keywords = option.keywords

        if not os.path.exists(args.file):
            exit("Please specify a valid file using the --file= parameter.")

        youtube = self.get_authenticated_service(args)

        try:
            dt_start, dt_end = self.initialize_upload(youtube, args)
            return self.get_youtube_video_url(), dt_start, dt_end
        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    def resumable_upload(self, insert_request):
        """
        Summary:
            This method implements an exponential backoff strategy to resume a failed upload.
        Args:
            insert_request (_type_): _description_
        """
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if "id" in response:
                        print(
                            "Video id '%s' was successfully uploaded." % response["id"]
                        )
                        self.uploaded_video_id = response["id"]
                    else:
                        exit(
                            "The upload failed with an unexpected response: %s"
                            % response
                        )
            except HttpError as e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (
                        e.resp.status,
                        e.content,
                    )
                else:
                    raise
            except self.RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                print(error)
                retry += 1
            if retry > self.MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2**retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)

    def get_authenticated_service(self, args):
        """_summary_

        Args:
            args (_type_): _description_

        Returns:
            _type_: _description_
        """
        flow = flow_from_clientsecrets(
            self.CLIENT_SECRETS_FILE,
            scope=self.YOUTUBE_UPLOAD_SCOPE,
            message=self.MISSING_CLIENT_SECRETS_MESSAGE,
        )

        storage = Storage("./creds/YouTube/%s-oauth2.json" % sys.argv[0])
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, args)

        return build(
            self.YOUTUBE_API_SERVICE_NAME,
            self.YOUTUBE_API_VERSION,
            http=credentials.authorize(httplib2.Http()),
        )

    def initialize_upload(self, youtube, options):
        """_summary_

        Args:
            youtube (_type_): _description_
            options (_type_): _description_

        Returns:
            _type_: _description_
        """
        tags = None
        if options.keywords:
            tags = options.keywords.split(",")

        body = dict(
            snippet=dict(
                title=options.title,
                description=options.description,
                tags=tags,
                categoryId=options.category,
            ),
            status=dict(privacyStatus=options.privacyStatus),
        )

        # Call the API's videos.insert method to create and upload the video.
        insert_request = youtube.videos().insert(
            part=",".join(list(body.keys())),
            body=body,
            # The chunksize parameter specifies the size of each chunk of data, in
            # bytes, that will be uploaded at a time. Set a higher value for
            # reliable connections as fewer chunks lead to faster uploads. Set a lower
            # value for better recovery on less reliable connections.
            #
            # Setting "chunksize" equal to -1 in the code below means that the entire
            # file will be uploaded in a single HTTP request. (If the upload fails,
            # it will still be retried where it left off.) This is usually a best
            # practice, but if you're using Python older than 2.6 or if you're
            # running on App Engine, you should set the chunksize to something like
            # 1024 * 1024 (1 megabyte).
            media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True),
        )

        dt_start = datetime.now()
        print("Start uploading video to YouTube: ", options.title)
        # self.resumable_upload(insert_request)
        print("Finish uploading video to YouTube: ", options.title)
        dt_end = datetime.now()
        return dt_start, dt_end

    def get_youtube_video_url(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return f"https://www.youtube.com/watch?v={self.id}"
