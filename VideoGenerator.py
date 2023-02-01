from PIL import Image, ImageDraw, ImageFont
from IPython.display import display
from moviepy.editor import *
import pandas as pd
from datetime import datetime


class VideoGenerator:

    def __init__(self, raw_dir, output_dir):
        self.raw_dir = raw_dir
        self.output_dir = output_dir

    # Generate Video Files
    def generate_video_files(self, recording):
        dt_start = datetime.now()
        self.generate_video_static_background_image(recording)

        # Get formatted file name
        file_name = self.get_file_name(recording)

        # Load the mp3 file
        audio = AudioFileClip(self.raw_dir + recording["File_Name"])

        # Create a video file with the same length as the mp3 file and a blank image
        video = ImageClip(self.output_dir + file_name + ".jpg").set_duration(
            audio.duration)
        video.fps = 30
        video_with_audio = video.set_audio(audio)
        # video_with_audio.preview()
        # Write the final video to a file
        video_with_audio.write_videofile(self.output_dir + file_name + ".mp4",
                                         threads=4,
                                         audio=True,
                                         remove_temp=True,
                                         codec="mpeg4",
                                         audio_codec='libmp3lame',
                                         temp_audiofile = self.output_dir + 'TEMP.mp3',
                                         write_logfile=True)

        dt_end = datetime.now()
        return self.build_video_spec(recording), dt_start, dt_end

    def generate_video_static_background_image(self, recording):
        # Create an image with a white background
        image = Image.new("RGB", (1500, 844), (255, 255, 255))

        # Create a draw object to draw on the image
        draw = ImageDraw.Draw(image)

        # Select a font and specify its size
        font = ImageFont.truetype(
            "./Open_Sans/static/OpenSans/OpenSans-Regular.ttf", 36)

        # Draw the text on the image
        draw.text((250, 200),
                  "Kajang Gospel Centre",
                  fill=(0, 0, 0),
                  font=font)
        draw.text((250, 350), recording["Topic"], fill=(0, 0, 0), font=font)
        draw.text((250, 400),
                  recording["Sub_Topic"],
                  fill=(0, 0, 0),
                  font=font)
        draw.text((250, 450), recording["Passage"], fill=(0, 0, 0), font=font)

        # Save the image
        image.save(self.output_dir + self.get_file_name(recording) + ".jpg")

    def get_file_name(self, recording):
        return recording["File_Name"].replace('.mp3', '')

    def build_video_spec(self, recording):
        file_name = f'{self.output_dir}{self.get_file_name(recording)}.mp4'
        title = f'[{recording["As_Of_Date"]}] [{recording["Topic"]}] [{recording["Sub_Topic"]}] [{recording["Passage"]}]'
        key_words = f'{recording["Key_Words"]}'
        description = f'{recording["Description"]}'

        return YouTubeVideoSpec(file_name, title, key_words, description)


class YouTubeVideoSpec():

    def __init__(self, file_name, title, key_words, description):
        self.file = file_name
        self.title = title
        self.keywords = key_words
        self.description = description

    def __str__(self):
        return f'''
            File = {self.file}
            Title = {self.title}
            Key Words = {self.keywords}
            Description = {self.description}
        '''