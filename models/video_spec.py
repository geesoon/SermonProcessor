"""A model that represent video spec"""


class VideoSpec:
    """A model that represent video spec"""

    def __init__(self, file_name, title, key_words, description):
        self.file = file_name
        self.title = title
        self.keywords = key_words
        self.description = description

    def __str__(self):
        return f"""
            File = {self.file}
            Title = {self.title}
            Key Words = {self.keywords}
            Description = {self.description}
        """
