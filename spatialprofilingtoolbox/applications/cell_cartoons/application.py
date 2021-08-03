
from ...environment.cell_metadata import CellMetadata


class CellPhenotypeGeometryVisualization:
    """
    This will be the main class of the standalone "Cell Cartoons" visualization
    application.
    """
    def __init__(self,
        dataset_design=None,
        file_manifest_file: str=None,
        input_files_path: str=None,
    ):
        self.cell_metadata = CellMetadata(
            dataset_design=dataset_design,
            file_manifest_file=file_manifest_file,
            input_files_path=input_files_path,
        )
        self.cell_metadata.initialize()

    def initialize_gui_components(self):
        pass

    def start_gui(self):
        pass
