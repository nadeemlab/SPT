class JobsPaths:
    """
    A convenience bundle object to store directory paths pertinent to generic jobs.
    """
    def __init__(
        self,
        job_working_directory,
        output_path,
    ):
        self.job_working_directory = job_working_directory
        self.output_path = './' # testing


class RuntimeEnvironmentSettings:
    """
    A convenience bundle object to store configuration parameters pertaining to
    runtime environment details that ought to be hidden from most pipeline
    components.
    """
    def __init__(
        self,
        runtime_platform,
    ):
        self.runtime_platform = runtime_platform


class DatasetSettings:
    """
    A convenience bundle object to store information about an input dataset's
    location on the file system.
    """
    def __init__(self,
        input_path,
        file_manifest_file,
    ):
        # self.input_path = './' # testing
        self.input_path = input_path
        self.file_manifest_file = file_manifest_file
