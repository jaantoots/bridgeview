#!/usr/bin/env python2
"""Convert an OpenEXR image file containing depth data to plain text tab-separated values."""
import sys
import os
import glob
import argparse
import numpy as np
import OpenEXR
import Imath

def convert_to_tsv(src, dest):
    """Convert OpenEXR to TSV."""
    # Input from any channel as binary data
    exr = OpenEXR.InputFile(src)
    red_str = exr.channel('R', Imath.PixelType(Imath.PixelType.FLOAT))
    red = np.fromstring(red_str, dtype=np.float32)

    # Shape the array according to image dimensions
    window = exr.header()['dataWindow']
    red.shape = (window.max.y - window.min.y + 1, window.max.x - window.min.x + 1)

    np.savetxt(dest, red, header=("Depth data converted from OpenEXR ({:s})".format(
        os.path.basename(__file__))))

def main():
    """Run conversion using files supplied as arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)
    parser.add_argument('src', type=str, nargs='+', help="Input OpenEXR file(s)")
    parser.add_argument('dest', type=str,
                        help="Output file, or directory (tsv extension is added to filenames)")
    args = parser.parse_args()

    src = [path for pathname in args.src for path in glob.glob(pathname)]
    if len(src) == 0:
        sys.exit("{:s}: No matching source files found".format(os.path.basename(__file__)))
    if os.path.isdir(args.dest):
        for exr in src:
            convert_to_tsv(exr, os.path.join(args.dest,
                                             os.path.splitext(os.path.basename(exr))[0] + '.tsv'))
    elif len(src) == 1:
        convert_to_tsv(src[0], args.dest)
    else:
        sys.exit("{:s}: Output directory does not exist".format(os.path.basename(__file__)))

if __name__ == "__main__":
    main()
