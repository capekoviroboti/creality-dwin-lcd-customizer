#!/usr/bin/env python3
'''
hzk_tool.py

Encode or decode HZK font files.
'''
import os
from typing import BinaryIO, List, Literal
import PIL
from gooey import Gooey, GooeyParser


PIXEL_WIDTHS: List[int] = [6, 8, 10, 12, 14, 16, 20, 24, 28, 32]


# pylint: disable=too-many-locals
def encode_hzk_file(input_image_dir: str, output_filename: str) -> None:
    '''
    Generate a new .hzk font file. This is based heavily on this
    package:
        https://github.com/Quint097/DWIN_Font_Tools/
    The file name scheme used here should ensure compatibility with the
    package mentioned above.
    '''
    output_hzk_file: BinaryIO = open(output_filename, 'wb')
    for i, width in enumerate(PIXEL_WIDTHS):
        height = width * 2
        image_width = ((width + 1) * 16) + 1
        image_height = ((height + 1) * 8) + 1
        img_name = f'{input_image_dir}/0x{i:02}_{width}x{height}_0-127.png'
        print(f'Processing image: {img_name}')
        with PIL.Image.open(img_name, 'r') as img:
            # Create a giant 2-d array of pixel data for the image:
            pixel_array = img.load()
            # Now make sure we have the expected dimensions for the input image:
            try:
                assert img.height == image_height
                assert img.width == image_width
            except AssertionError as ex:
                print(
                    f'ERROR: Incorrect dimensions for image {img_name}. ' +
                    f'Was: {img.width}x{img.height}. ' +
                    f'Expected: {image_width}x{image_height}.'
                )
                raise AssertionError(
                    f'Bad Dimensions: {img_name} ({img.width}x{img.height})'
                ) from ex
            for row in range(8):
                for col in range(16):
                    if i == 9 and row == 7 and col == 15:
                        continue
                    # pylint: disable=invalid-name
                    for h in range(1, height):
                        bit_array: List[Literal[0, 1]] = []
                        # in_bytes = input_hzk_file.read(num_bytes)
                        # pylint: disable=invalid-name
                        for w in range(1, width):
                            _r, _g, _b, _a = pixel_array[col * (width + 1) + w,
                                                         row * (height + 1) + h]
                            # if _a < 65000:
                            #     break
                            if (_r, _g, _b) == (0, 0, 0):
                                # Black pixel
                                bit_array.append(1)
                            elif (_r, _g, _b) == (255, 255, 255):
                                # White pixel
                                bit_array.append(0)
                            else:
                                raise ValueError(
                                    f'Invalid image: \'{img_name}\' - ' +
                                    f'image contains RGB value: {_r}, {_g}, {_b}'
                                )
                        output_hzk_file.write(bits_to_byte_array(bit_array))
        print(f'Completed handling file: {img_name}')
    output_hzk_file.close()


# pylint: disable=too-many-locals
def decode_hzk_file(input_hzk_filename: str, output_dir: str) -> None:
    '''
    Parsing an existing .hzk font file into a directory of PNG images.
    This is based heavily on this package:
        https://github.com/Quint097/DWIN_Font_Tools/
    The file name scheme used here should ensure compatibility with the
    package mentioned above.

    '''
    input_hzk_file: BinaryIO = open(input_hzk_filename, 'rb')
    for i, width in enumerate(PIXEL_WIDTHS):
        height = width * 2
        return


def bits_to_byte_array(bit_array: List[Literal[0, 1]]) -> bytearray:
    '''
    Given a list of 1s and 0s representing a bit array,
    generate a native Python bytearray.
    '''
    remainder = len(bit_array) % 8
    if remainder != 0:
        for _ in range(8 - remainder):
            bit_array.append(0)
    return bytearray(
        sum(v << i for i, v in enumerate(bit_array[::-1]))
    )


@Gooey
def main() -> None:
    '''
    Main. Handle parsing the command line arguments, and then
    selecting the correct code path to either encode a new HZK file
    using PNG images as input OR decode an existing HZK file into
    new PNG images.
    '''
    # Parse command line arguments:
    parser_description = 'Encode and decode .hzk font files.'
    parser = GooeyParser(description=parser_description)
    # Set the encode/decode mode; it should be required and mutually exclusive
    # (exactly one should be specified):
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--encode', '-e', action='store_true',
                         help='Encode a .HZK file')
    actions.add_argument('--decode', '-d', action='store_true',
                         help='Decode a .HZK file')
    # The following arguments are sensitive to the encode/decode mode, but can be passed
    # using the same commandline syntax either way:
    parser.add_argument('--input', '-i', widget='FileChooser', dest='input_path', required=True,
                        help='Path to the input file (decode) or directory (encode)')
    parser.add_argument('--output', '-o', widget='FileChooser', dest='output_path', required=True,
                        help='Path to the output directory (decode) or file (encode)')
    args = parser.parse_args()
    encode_mode = args.encode
    if encode_mode:
        # Handle encode mode:
        input_dir = args.input_path
        output_file = args.output_path
        # Validate the input path:
        print(f'Checking whether --input {input_dir} is valid...')
        try:
            assert os.path.isdir(input_dir) and \
                   any((f.name.endswith('.png') for f in os.scandir(input_dir)))
            print(f'{input_dir} is valid')
        except (AssertionError, IOError) as ex:
            raise IOError(
                f'Invalid input path: `{input_dir}`. ' +
                'Path must be a readable directory with .png files in it.'
            ) from ex
        # Validate the output file path:
        print(f'Checking whether --output {output_file} is valid...')
        try:
            assert output_file.lower().endswith('.hzk') and \
                   (os.path.exists(output_file) or os.access(os.path.dirname(output_file), os.W_OK))
            print(f'{output_file} is valid')
        except (AssertionError, IOError) as ex:
            raise IOError(
                f'Invalid output file: `{output_file}`. ' +
                'File must be of type \'.hzk\' and be writeable by this program.'
            ) from ex
        # Start up the encoder:
        print(f'hzk_encoder.py ---> Generating {output_file} from input directory {input_dir}')
        encode_hzk_file(input_dir, output_file)
    else:
        # Handle decode mode:
        input_file = args.input_path
        output_dir = args.output_path
        # Validate the input path:
        print(f'Checking whether --input {input_file} is valid...')
        try:
            assert input_file.lower().endswith('.hzk') and os.path.exists(input_file)
            print(f'{input_file} is valid')
        except (AssertionError, IOError) as ex:
            raise IOError(
                f'Invalid input file: `{input_file}`. ' +
                'File must be of type \'.hzk\' and be readable by this program.'
            ) from ex
        # Validate the output file path:
        print(f'Checking whether --output {output_dir} is valid...')
        try:
            assert os.path.isdir(output_dir) or \
                   os.access(os.path.dirname(output_dir), os.W_OK)
            print(f'{output_dir} is valid')
        except (AssertionError, IOError) as ex:
            raise IOError(
                f'Invalid output path: `{output_dir}`. ' +
                'Path must be a writeable directory.'
            ) from ex
        # Start up the encoder:
        print(f'hzk_encoder.py ---> Generating {output_dir} from input file {input_file}')
        decode_hzk_file(input_file, output_dir)


if __name__ == '__main__':
    main()
