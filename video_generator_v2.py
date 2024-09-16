"""A class that generate video."""

import os
from pprint import pprint
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip
from mutagen.easyid3 import EasyID3


class VideoGeneratorV2:
    """Class that generate a video"""

    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.render()

    def render(self):
        """Get the list of audio files in input_dir, loop through to generate videos"""
        file_names = os.listdir(self.input_dir)
        file_names = sorted(file_names)
        for fn in file_names:
            print(fn)
            self.generate_video_file(fn)

    def generate_video_file(self, file_name):
        """Generate Video Files"""
        full_dir = self.input_dir + file_name

        video_metadata = self.get_audio_metadata(full_dir)
        self.generate_video_static_background_image(video_metadata, file_name)

        # Load the mp3 file
        audio = AudioFileClip(full_dir)

        # # Create a video file with the same length as the mp3 file and a blank image
        # # Set to 1 frame per second because the video is a static background with audio, smaller fps improve rendering duration
        video_with_audio = (
            ImageClip(self.output_dir + "background/" + file_name + ".jpg")
            .set_duration(audio.duration)
            .set_fps(1)
            .set_audio(audio)
        )

        # # video_with_audio.preview()
        # # Write the final video to a file
        video_with_audio.write_videofile(
            self.output_dir + file_name + ".mp4",
            threads=4,
            audio=True,
            remove_temp=True,
            codec="mpeg4",
            audio_codec="libmp3lame",
            temp_audiofile=self.output_dir + "TEMP.mp3",
        )

    def generate_video_static_background_image(self, audio_metadata, file_name):
        """Create an image with a white background"""
        image = Image.new("RGB", (1920, 1080), (0, 0, 0))
        logo = Image.open("./KGC Logo - no background.png")
        max_size = (200, 200)
        logo.thumbnail(max_size)
        logo_pos = (230, 250)
        image.paste(logo, logo_pos, logo)

        # Create a draw object to draw on the image
        draw = ImageDraw.Draw(image)

        # Select a font and specify its size
        font = ImageFont.truetype(
            "./Open_Sans/static/OpenSans/OpenSans-Regular.ttf", 48
        )
        title_font = ImageFont.truetype(
            "./Open_Sans/static/OpenSans/OpenSans-Regular.ttf", 70
        )

        font_color = (255, 255, 255)
        # dt = datetime.strptime(audio_metadata["date"][0], '%Y-%m-%d %H:%M:%S')
        # # Format the datetime object to a date string
        # date_str = dt.strftime('%Y-%m-%d')

        # Draw the text on the image
        draw.text((450, 300), "Kajang Gospel Centre", fill=font_color, font=title_font)
        draw.text(
            (250, 450),
            "{:<4} {:<10}".format("Title:", audio_metadata["title"][0]),
            fill=font_color,
            font=font,
        )
        draw.text(
            (250, 550),
            "{:<2} {:<10}".format("Speaker:", audio_metadata["artist"][0]),
            fill=font_color,
            font=font,
        )
        draw.text(
            (250, 650),
            "{:<3} {:<10}".format("Series:", audio_metadata["album"][0]),
            fill=font_color,
            font=font,
        )

        # Create the output directory if not already available
        bg_output = self.output_dir + "background/"
        if not os.path.exists(bg_output):
            os.makedirs(bg_output)

        # Save the image
        image.save(bg_output + file_name + ".jpg")

    def get_audio_metadata(self, full_dir):
        """read the audio/video file from the command line arguments"""
        audio = EasyID3(full_dir)
        pprint(audio)
        return audio
