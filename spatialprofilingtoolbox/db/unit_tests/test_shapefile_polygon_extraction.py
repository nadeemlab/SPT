
import spatialprofilingtoolbox
from spatialprofilingtoolbox.db.shapefile_polygon import extract_points

if __name__=='__main__':
    shapefile_contents = 'AAAnCgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAdugDAAAFAAAAAAAAAACatEAAAAAAAAAYwAAAAAAAurRAAAAAAAAAMkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAABABQAAAAAAAAAAmrRAAAAAAAAAGMAAAAAAALq0QAAAAAAAADJAAQAAAAUAAAAAAAAAAAAAAACatEAAAAAAAAAYwAAAAAAAmrRAAAAAAAAAMkAAAAAAALq0QAAAAAAAADJAAAAAAAC6tEAAAAAAAAAYwAAAAAAAmrRAAAAAAAAAGMA='
    points = extract_points(shapefile_contents)
    expected = [(5274.0, -6.0), (5274.0, 18.0), (5306.0, 18.0), (5306.0, -6.0), (5274.0, -6.0)]
    if expected != points:
        exit(1)
