import os
from os.path import join
FIND_FILES_USING_PATH = ('FIND_FILES_USING_PATH' in os.environ)


class DatasetSettings:
    """
    A convenience bundle object to store information about an input dataset's
    location on the file system.
    """
    def __init__(self,
        input_path,
        file_manifest_file,
    ):
        self.input_path = input_path
        if FIND_FILES_USING_PATH:
            self.file_manifest_file = join(input_path, file_manifest_file)
        else:
            self.file_manifest_file = file_manifest_file
