"""
Wrapper class for describing the components of a given workflow.
"""
class WorkflowModules:
    """
    A wrapper object in which to list implementation classes comprising a workflow
    definition.
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
