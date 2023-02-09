"""
Basic interface for the initializer pattern for Nextflow workflows.
"""
# from abc import ABC, abstractmethod


# class Initializer(ABC):
#     """Interface for the intializer job for the Nextflow-managed workflows."""
#     def __init__(self, dataset_design=None, computational_design=None, **kwargs): # pylint: disable=unused-argument
#         self.dataset_design = dataset_design
#         self.computational_design = computational_design

#     @staticmethod
#     @abstractmethod
#     def solicit_cli_arguments(parser):
#         pass

#     def initialize(self, **kwargs):
#         pass
