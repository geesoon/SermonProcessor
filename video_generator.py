"""A class that generate video v1"""

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip

from models.video_spec import VideoSpec


class VideoGenerator:
    """A class that generate video v1"""

    def __init__(self, raw_dir, output_dir):
        self.raw_dir = raw_dir
        self.output_dir = output_dir

    def generate_video_files(self, recording):
        """Generate Video Files"""
        dt_start = datetime.now()
        self.generate_video_static_background_image(recording)

        # Get formatted file name
        file_name = self.get_file_name(recording)

        # Load the mp3 file
        audio = AudioFileClip(self.raw_dir + recording["File_Name"])

        # Create a video file with the same length as the mp3 file and a blank image
        video = ImageClip(self.output_dir + file_name + ".jpg").set_duration(
            audio.duration
        )
        video.fps = 1  # Set to 1 frame per second because the video is a static background with audio, smaller fps improve rendering duration
        video_with_audio = video.set_audio(audio)
        # video_with_audio.preview()
        # Write the final video to a file
        # video_with_audio.write_videofile(self.output_dir + file_name + ".mp4",
        #                                  threads=4,
        #                                  audio=True,
        #                                  remove_temp=True,
        #                                  codec="mpeg4",
        #                                  audio_codec='libmp3lame',
        #                                  temp_audiofile = self.output_dir + 'TEMP.mp3',
        #                                  write_logfile=True)

        dt_end = datetime.now()
        return self.build_video_spec(recording), dt_start, dt_end

    def generate_video_static_background_image(self, recording):
        """Create an image with a white background"""
        image = Image.new("RGB", (1920, 1080), (0, 0, 0))

        # Create a draw object to draw on the image
        draw = ImageDraw.Draw(image)

        # Select a font and specify its size
        font = ImageFont.truetype(
            "./Open_Sans/static/OpenSans/OpenSans-Regular.ttf", 48
        )
        title_font = ImageFont.truetype(
            "./Open_Sans/static/OpenSans/OpenSans-Regular.ttf", 60
        )

        font_color = (255, 255, 255)

        # Draw the text on the image
        draw.text((250, 300), "Kajang Gospel Centre", fill=font_color, font=title_font)
        draw.text((250, 450), recording["Topic"], fill=font_color, font=font)
        draw.text((250, 530), recording["Sub_Topic"], fill=font_color, font=font)
        draw.text((250, 610), recording["Passage"], fill=font_color, font=font)

        # Save the image
        image.save(self.output_dir + self.get_file_name(recording) + ".jpg")

    def get_file_name(self, recording):
        """_summary_

        Args:
            recording (_type_): _description_

        Returns:
            _type_: _description_
        """
        return recording["File_Name"].replace(".mp3", "")

    def build_video_spec(self, recording):
        """_summary_

        Args:
            recording (_type_): _description_

        Returns:
            _type_: _description_
        """
        file_name = f"{self.output_dir}{self.get_file_name(recording)}.mp4"
        title = f'[{recording["As_Of_Date"]}] [{recording["Topic"]}] [{recording["Sub_Topic"]}] [{recording["Passage"]}]'
        key_words = f'{recording["Key_Words"]}'
        description = f'{recording["Description"]}'

        return VideoSpec(file_name, title, key_words, description)
