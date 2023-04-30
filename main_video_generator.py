from VideoGeneratorV2 import VideoGeneratorV2

# CONSTANT
INPUT_DIR = './family_camp_2023/'
OUTPUT_DIR = './family_camp_2023_output/'

# Find all the audio files in RAW_DIR
# Get metadata from each audio file
# Get subtitle SRT file for each audio file
# Add subtitle to video
# Generate video with black background and message information from metadata
# Output video to OUTPUT_DIR

def main():
    VideoGeneratorV2(INPUT_DIR, OUTPUT_DIR)

if __name__ == '__main__':
    main()