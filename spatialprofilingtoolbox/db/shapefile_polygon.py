import base64
import mmap
import shapefile

def extract_points(shapefile_base64_ascii):
    bytes_original = base64.b64decode(shapefile_base64_ascii.encode('utf-8'))
    mm =  mmap.mmap(-1, len(bytes_original))
    mm.write(bytes_original)
    mm.seek(0)
    sf = shapefile.Reader(shp=mm)
    shape_type = sf.shape(0).shapeType
    shape_type_name = sf.shape(0).shapeTypeName
    if shape_type != 5:
        raise ValueError('Expected shape type index is 5 (according to page 4 of ESRI specification), not %s.', shape_type)
    if shape_type_name != 'POLYGON':
        raise ValueError('Expected shape type is "POLYGON", not %s.', shape_type_name)
    return sf.shape(0).points
