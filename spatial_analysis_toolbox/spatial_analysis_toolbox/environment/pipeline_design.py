

class PipelineDesign:
    def get_database_uri(self):
        """
        The pipelines/workflows may request persistent storage of data pertaining to
        generic pipelines, rather than specific pipelines. The implementation class
        should provide the URI of the database in which to store this data.

        This database should generally not be used by workflow modules themselves, but
        rather by `environment` module classes.

        Currently, only local sqlite databases are supported. Future version may support
        remote SQL database connections.

        Returns:
            str:
                The Uniform Resource Identifier (URI) identifying the database.
        """
        return '.pipeline.db'
