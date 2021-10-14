class WorkflowModules:
    """
    A wrapper object in which to list implementation classes comprising a workflow definition.
    """
    def __init__(self, generator=None, dataset_design=None, computational_design=None, analyzer=None, integrator=None):
        self.generator = generator
        self.dataset_design = dataset_design
        self.computational_design = computational_design
        self.analyzer = analyzer
        self.integrator = integrator
