"""Convenience accessor of precomputed UMAP visualizations."""
from io import BytesIO
from base64 import b64decode
from base64 import b64encode

from PIL import Image

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import UMAPChannel

def _get_umap_rows(cursor, study: str) -> list[tuple[str, str]]:
    cursor.execute('''
    SELECT up.channel, up.png_base64 FROM umap_plots up
    WHERE up.study=%s
    ORDER BY up.channel ;
    ''', (study,))
    return [(row[0], row[1]) for row in cursor.fetchall()]


def _get_umap_row_for_channel(cursor, study: str, channel: str) -> tuple[str, str]:
    cursor.execute('''
    SELECT up.channel, up.png_base64 FROM umap_plots up
    WHERE up.study=%s AND up.channel=%s
    ORDER BY up.channel ;
    ''', (study, channel))
    rows = cursor.fetchall()
    return rows[0]


def _downsample_umaps_base64(umap_rows: list[tuple[str, str]]) -> list[UMAPChannel]:
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
