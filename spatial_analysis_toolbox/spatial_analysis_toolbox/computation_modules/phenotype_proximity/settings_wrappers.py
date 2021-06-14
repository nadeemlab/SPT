
class JobPaths:
    def __init__(
        self,
        job_working_directory,
        jobs_path,
        logs_path,
        schedulers_path,
        output_path,
    ):
        self.output_path = output_path
        self.job_working_directory = job_working_directory
        self.jobs_path = jobs_path
        self.logs_path = logs_path
        self.schedulers_path = schedulers_path


class RuntimeEnvironmentSettings:
    def __init__(
        self,
        runtime_platform,
        sif_file,
    ):
        self.runtime_platform = runtime_platform
        self.sif_file = sif_file


class DatasetSettings:
    def __init__(
        self,
        input_path,
        file_manifest_file,
        outcomes_file,
    ):
        self.input_path = input_path
        self.file_manifest_file = file_manifest_file
        self.outcomes_file = outcomes_file


# The below may not be needed, since there are already wrapper-style classes about these settings:

# class DatasetDesignSettings:
#     def __init__(
#         self,
#         elementary_phenotypes_file,
#     ):
#         self.elementary_phenotypes_file = elementary_phenotypes_file

# class ComputationalDesignSettings:
#     def __init__(
#         self,
#         complex_phenotypes_file,
#     ):
#         self.complex_phenotypes_file = complex_phenotypes_file
