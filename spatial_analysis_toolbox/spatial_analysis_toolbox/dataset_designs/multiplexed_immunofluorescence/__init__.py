"""
Multiplexed `immunofluorescence <https://en.wikipedia.org/wiki/Immunofluorescence>`_ is a family of microscopic imaging data modalities.

The result is a series of scalar-valued, 2-dimensional raster images, which may also be called channels. Each channel represents a pixel-level quantification of the amount of a given molecular species present in a specimen prepared as a slice on a histopathology slide. Depending on the exact modality, the channels may have been obtained on near/consecutive slices, or else on the exact same slice. The latter is preferred in order for the implicit co-registration of the images to make sense.

Depending on the pipeline, the components of this toolbox may operate directly on images or instead on extracted cell-level metadata.
"""
