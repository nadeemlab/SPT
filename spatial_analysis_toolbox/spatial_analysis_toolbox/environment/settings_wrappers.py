class JobsPaths:
    """
    A convenience bundle object to store directory paths pertinent to generic jobs.
    """
    def __init__(
        self,
        job_working_directory,
        jobs_path,
        logs_path,
        schedulers_path,
        output_path,
    ):
        self.job_working_directory = job_working_directory
        self.jobs_path = jobs_path
        self.logs_path = logs_path
        self.schedulers_path = schedulers_path
        self.output_path = output_path


class RuntimeEnvironmentSettings:
    """
    A convenience bundle object to store configuration parameters pertaining to
    runtime environment details that ought to be hidden from most pipeline
    components.
    """
    def __init__(
        self,
        runtime_platform,
        sif_file,
    ):
        self.runtime_platform = runtime_platform
        self.sif_file = sif_file


class DatasetSettings:
    """
    A convenience bundle object to store information about an input dataset's
    location on the file system.
    """
    def __init__(
        self,
        input_path,
        file_manifest_file,
        outcomes_file,
    ):
        self.input_path = input_path
        self.file_manifest_file = file_manifest_file
        self.outcomes_file = outcomes_file
