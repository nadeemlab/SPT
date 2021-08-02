

class ComputationalDesign:
    """
    This is an object to collect together any metadata that is specific to a
    particular pipeline/workflow's computation stage. This, as opposed to the input
    data parsing stage, for example.
    """
    def get_database_uri(self):
        """
        Each computational workflow may request persistent storage of intermediate data.
        The implementation class should provide the URI of the database in which to store
        this data.

        Currently, only local sqlite databases are supported. Future version may support
        remote SQL database connections.

        Returns:
            str:
                The Uniform Resource Identifier (URI) identifying the database.
        """
        pass
