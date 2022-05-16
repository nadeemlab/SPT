class WorkflowModules:
    """
    A wrapper object in which to list implementation classes comprising a workflow
    definition.
    """
    def __init__(
        self,
        generator=None,
        initializer=None,
        dataset_design=None,
        computational_design=None,
        core_job=None,
        integrator=None,
    ):
        self.generator = generator
        self.initializer = initializer
        self.dataset_design = dataset_design
        self.computational_design = computational_design
        self.core_job = core_job
        self.integrator = integrator
