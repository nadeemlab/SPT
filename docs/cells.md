
# Data structure to represent summarized cell-level data for one slide

For memory- and time-efficient manipulation, a simple binary data structure is used to represent the cell data for one slide.

The memory map is as follows:

| Byte range start | Byte range end | Number of bytes | Section | Description                                              | Data type                             |
|------------------|----------------|-----------------|---------|----------------------------------------------------------|---------------------------------------|
| 1                | 4              | 4               | Header  | The number of cells represented by this serialization.   | 32-bit integer, big-endian byte order |
| 5                | 8              | 4               |         | Minimum first pixel coordinate occurring in this file.   | 32-bit integer, big-endian byte order |
| 9                | 12             | 4               |         | Maximum first pixel coordinate occurring in this file.   | 32-bit integer, big-endian byte order |
| 13               | 16             | 4               |         | Minimum second pixel coordinate occurring in this file.  | 32-bit integer, big-endian byte order |
| 17               | 20             | 4               |         | Maximum second pixel coordinate occurring in this file.  | 32-bit integer, big-endian byte order |
| 21               | 24             | 4               | Cell 1  | Cell 1 index integer.                                    | 32-bit integer, big-endian byte order |
| 25               | 28             | 4               |         | Cell 1 location's first pixel coordinate integer.        | 32-bit integer, big-endian byte order |
| 29               | 32             | 4               |         | Cell 1 location's second pixel coordinate integer.       | 32-bit integer, big-endian byte order |
| 33               | 40             | 8               |         | Cell 1 phenotype membership bit-mask, up to 64 channels. | 64-bit mask                           |
| 41               | 44             | 4               | Cell 2  | Cell 2 location's first pixel coordinate integer.        | 32-bit integer, big-endian byte order |
| ... | ... | ... | ... | ... |

The ellipsis represents repetition of the per-cell section once for each cell. This is 4 + 4 + 4 + 8 = 20 bytes per cell. The "header" preceding the per-cell sections is 20 bytes.

A representation of an example of the cell sections can be found [here](https://github.com/nadeemlab/SPT/blob/main/test/apiserver/module_tests/celldata.dump).

There is a convenient way to preview the contents at the command line using `xxd`:

```sh
tail -c +21 payload.bin | xxd -b -c 20
```

(The initial `tail` command strips out the header.)
