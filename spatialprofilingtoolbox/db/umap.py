"""Convenience accessor of precomputed UMAP visualizations."""
from io import BytesIO
from base64 import b64decode
from base64 import b64encode

from PIL import Image

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import UMAPChannel
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider


class UMAPAccess(SimpleReadOnlyProvider):
    """Access to precomputed UMAP visualizations in database."""
    def get_umap_rows(self, study: str) -> list[tuple[str, str]]:
        self.cursor.execute('''
        SELECT up.channel, up.png_base64 FROM umap_plots up
        WHERE up.study=%s
        ORDER BY up.channel ;
        ''', (study,))
        return [(row[0], row[1]) for row in self.cursor.fetchall()]

    def get_umap_row_for_channel(self, study: str, channel: str) -> UMAPChannel:
        self.cursor.execute('''
        SELECT up.channel, up.png_base64 FROM umap_plots up
        WHERE up.study=%s AND up.channel=%s
        ORDER BY up.channel ;
        ''', (study, channel))
        rows = self.cursor.fetchall()
        row = rows[0]
        return UMAPChannel(channel=row[0], base64_png=row[1])

    @staticmethod
    def downsample_umaps_base64(umap_rows: list[tuple[str, str]]) -> list[UMAPChannel]:
        downsampled_rows = []
        for row in umap_rows:
            input_buffer = BytesIO(b64decode(row[1]))
            output_buffer = BytesIO()
            with Image.open(input_buffer) as image:
                new_size = 550
                image_resized = image.resize((new_size, new_size))
                image_resized.save(output_buffer, format='PNG')
                output_buffer.seek(0)
                downsampled_64 = b64encode(output_buffer.getvalue()).decode('utf-8')
            output_buffer.close()
            input_buffer.close()
            downsampled_rows.append(UMAPChannel(channel=row[0], base64_png=downsampled_64))
        return downsampled_rows
