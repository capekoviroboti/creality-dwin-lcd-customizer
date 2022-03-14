#!/usr/bin/env python3
'''
creality_dwin_lcd_customizer.py

Generate a custom build of Marlin + DWIN_SET directory
for Creality printers that use DWIN LCDs, including:
    * Ender-3 V2
    * Ender 3 Max
    * Ender 5
    * Ender 5+
    * Ender 5 Pro
    * Ender 6
    * CR10S Pro
    * CR10S Pro V2
    * CR10 Max
    * CR-X / Pro
    * CR10 V2/V3
    * CR20 and Pro
    * CR10S
    * CR10S4 400mm
    * CR10S5 500mm
    * CR6 / Max
Other Creality printers that use DWIN LCDs
may work, but you will need to experiment
with baseline configurations to see what works.
'''
import os
import pathlib
import shutil
import tempfile
import subprocess
from typing import Callable, List, Set
from gooey import Gooey, GooeyParser
import DWIN_ICO


# Class definitions:
class DropDownChoice():
    '''
    Minimal wrapper object for holding info for a drop down
    menu choice.
    '''
    def __init__(self, name, dir_name, directory=None):
        self.name = name
        if directory:
            self.directory = directory
        else:
            self.directory = DropDownChoice.generate_directory_name(name, dir_name)

    @staticmethod
    def generate_directory_name(input_name: str, dir_name: str) -> str:
        '''
        If a directory is unspecified, guess what it is
        with this class-level method. This uses the absolute path
        of the script itself, so that the resulting path
        will work regardless of what directory you run the
        script from.
        '''
        return str(
            pathlib.Path(
                os.path.realpath(__file__)
            ).resolve().parent.parent / f'{dir_name}/{input_name}'
        )

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.directory == other.directory
        return False


# pylint: disable=too-few-public-methods,too-many-instance-attributes
class PrinterChoice(DropDownChoice):
    '''
    Minimal wrapper object for holding printer info.
    '''
    # pylint: disable=too-many-arguments
    def __init__(self, name, build_env, parser_arguments: List[Callable],
                 screen_name: str,
                 default_font_hzk: str = '',
                 default_bootscreen: str = '',
                 default_logo: str = '',
                 default_icon_pack: str = '',
                 baseline_directory: str = '') -> None:
        if baseline_directory:
            super().__init__(name, None, baseline_directory)
        else:
            super().__init__(name, None, PrinterChoice.generate_directory_name(name, 'baseline'))
        self.parser_arguments = parser_arguments
        self.build_env = build_env
        self.screen_name = screen_name
        self.default_font_hzk = default_font_hzk
        self.default_bootscreen = default_bootscreen
        self.default_logo = default_logo
        self.default_icon_pack = default_icon_pack

    @staticmethod
    def generate_directory_name(input_name: str, dir_name: str) -> str:
        '''
        If a directory is unspecified, guess what it is
        with this class-level method. This uses the absolute path
        of the script itself, so that the resulting path
        will work regardless of what directory you run the
        script from.
        '''
        return str(
            pathlib.Path(
                os.path.realpath(__file__)
            ).resolve().parent.parent / f'{dir_name}/{"-".join(input_name.split())}'
        )


# pylint: disable=too-few-public-methods
class ColorSchemeChoice(DropDownChoice):
    '''
    Minimal wrapper object for holding color scheme info.
    '''
    def __init__(self, name, directory=None):
        super().__init__(name, 'color-schemes', directory)


# pylint: disable=too-few-public-methods
class LanguageChoice(DropDownChoice):
    '''
    Minimal wrapper object for holding language info.
    '''
    def __init__(self, name, directory=None):
        super().__init__(name, 'languages', directory)


# Add defaults:
DEFAULT_OUTPUT_PATH = str(pathlib.Path(os.path.realpath(__file__)).resolve().parent.parent)
DEFAULT_MARLIN_PATH = 'submodules/Marlin/'

# Gooey subparser argument generator functions: this code below allows you to
# dynamically create parsers, one per printer, and assign each of them the correct
# arguments.


# pylint: disable=unused-argument
def add_baseline_path_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the baseline_path argument to a printer parser.'''
    baseline_path_help = 'Set the baseline DWIN_SET directory to use as a source ' + \
        f'(default: {printer.directory})'
    printer_parser.add_argument(
        '--baseline-path',
        metavar='Baseline DWIN_SET directory',
        widget='DirChooser',
        dest='baseline_path',
        help=baseline_path_help
    )


# pylint: disable=unused-argument
def add_output_path_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the output_path argument to a printer parser.'''
    output_path_help = 'Specify where the new DWIN_SET directory should be placed ' + \
        f'(default: {DEFAULT_OUTPUT_PATH})'
    printer_parser.add_argument(
        '--output-path',
        metavar='Output path',
        widget='DirChooser',
        dest='output_path',
        help=output_path_help
    )


def add_icon_pack_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the icon_pack argument to a printer parser.'''
    ico_path_help = 'Specify a .ICO file to use as the basis of the icons ' + \
        f'(default: {printer.default_icon_pack})'
    printer_parser.add_argument(
        '--icon-pack',
        metavar='.ICO icon pack',
        widget='FileChooser',
        dest='icon_pack',
        help=ico_path_help
    )


# pylint: disable=unused-argument
def add_logo_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the logo_image argument to a printer parser.'''
    logo_help = 'Choose the logo icon to insert into the baseline .ICO file ' + \
        f'(default: {printer.default_logo})'
    printer_parser.add_argument(
        '--logo',
        metavar='Logo icon',
        widget='FileChooser',
        dest='logo_image',
        help=logo_help
    )


# pylint: disable=unused-argument
def add_bootscreen_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the bootscreen_image argument to a printer parser.'''
    bootscreen_help = 'Choose the bootscreen image ' + \
        f'(default: {printer.default_bootscreen})'
    printer_parser.add_argument(
        '--bootscreen-image',
        metavar='Bootscreen',
        widget='FileChooser',
        dest='bootscreen_image',
        help=bootscreen_help
    )


# pylint: disable=unused-argument
def add_font_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the font_hzk_file argument to a printer parser.'''
    font_hzk_help = 'Specify the .HZK file that should be used as the font ' + \
        f'(default: {printer.default_font_hzk})'
    printer_parser.add_argument(
        '--font',
        metavar='.HZK font file',
        widget='FileChooser',
        dest='font_hzk_file',
        help=font_hzk_help
    )


# pylint: disable=unused-argument
def add_color_scheme_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the color_scheme argument to a printer parser.'''
    color_scheme_help = f'Set the color scheme (default: {str(COLOR_SCHEMES[0])})'
    printer_parser.add_argument(
        '--color-scheme',
        metavar='Color scheme',
        widget='Dropdown',
        dest='color_scheme',
        choices=available_color_schemes(),
        help=color_scheme_help
    )


# pylint: disable=unused-argument
def add_language_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the language argument to a printer parser.'''
    language_help = 'Set the display language (default: English)'
    printer_parser.add_argument(
        '--language',
        metavar='Language',
        widget='Dropdown',
        dest='language',
        choices=available_languages(),
        help=language_help
    )


# pylint: disable=unused-argument
def add_compile_mainboard_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the compile_mainboard argument to a printer parser.'''
    # Decide whether we should trigger recompilation of Marlin for the mainboard
    # via PlatformIO
    compile_mainboard_help = 'Recompile the firmware .bin for the mainboard using PlatformIO'
    printer_parser.add_argument(
        '--compile-mainboard',
        metavar='Compile Marlin',
        action='store_true',
        default=False,
        dest='compile_mainboard',
        help=compile_mainboard_help
    )


# pylint: disable=unused-argument
def add_marlin_path_argument(printer_parser, printer: PrinterChoice) -> None:
    '''Add the marlin_path argument to a printer parser.'''
    marlin_path_help = 'Path to the top Marlin directory if recompiling the ' + \
        f'mainboard firmware (default: {DEFAULT_MARLIN_PATH}'
    printer_parser.add_argument(
        '--marlin-path',
        metavar='Marlin path',
        widget='DirChooser',
        required=False,
        dest='marlin_path',
        help=marlin_path_help
    )


# Global definitions:
DWIN_SET_DIRECTORY_NAME = 'DWIN_SET'
# For T5UIC1 (Class 1) screens:
#    Defaults:
T5UIC1_DEFAULT_LOGO_IMAGE = 'images/logos/awcy-red-logo-black-bg-130x17.jpg'
T5UIC1_DEFAULT_BOOTSCREEN = 'images/bootscreens/AWCY-boot-screen-ender3v2-noprog.jpg'
T5UIC1_DEFAULT_HZK_FONT_FILE = 'fonts/DWIN Font (Original)/0T5UIC1.HZK'
#    Output names:
T5UIC1_BOOTSCREEN_IMAGE_FILE_NAME = '0_start.jpg'
T5UIC1_ICON_PACK_FILE_NAME = '9.ICO'
T5UIC1_FONT_HZK_FILE_NAME = '0T5UIC1.HZK'
T5UIC1_LOGO_FILE_NAME = '/000-ICON_LOGO.jpg'
DWIN_MAINBOARD_FIRMWARE_PATH = 'Marlin/src/lcd/e3v2/creality/'
# For T5L (Class 2) screens:
#    Defaults:
T5L_DEFAULT_HZK_FONT_FILE = 'fonts/CR6-Community-Font/B612Mono-CR6.HZK'
#    Output names:
T5L_FONT_HZK_FILE_NAME = '0_DWIN_ASC.HZK'


# For T5UID1 (Class 3) screens:
#    Defaults:
# TODO: Once we can compile T5UID1 .ICO files, add this back in.
# T5UID1_DEFAULT_LOGO_IMAGE = 'images/logos/awcy-red-logo-black-bg-130x17.ico'
T5UID1_DEFAULT_BOOTSCREEN = 'images/bootscreens/AWCY-boot-screen-ender3v2-noprog.bmp'
T5UID1_DEFAULT_HZK_FONT_FILE = 'fonts/InsanityAutomation-CombinedScreens/0_DWIN_ASC.HZK'
#    Output names:
T5UID1_BOOTSCREEN_IMAGE_FILE_NAME = '00_starting.bmp'
T5UID1_FONT_HZK_FILE_NAME = '0_DWIN_ASC.HZK'
SHARED_ARGUMENTS = [
    add_baseline_path_argument,
    add_output_path_argument,
    add_bootscreen_argument,
    add_font_argument,
    add_color_scheme_argument,
    add_language_argument
]
MARLIN_COMPILE_ARGUMENTS = [
    add_compile_mainboard_argument,
    add_marlin_path_argument
]
PRINTER_OPTIONS = {
    'Ender-3-V2': PrinterChoice('Ender 3 V2',
                                'STM32F103RET6_creality',
                                SHARED_ARGUMENTS + [
                                    add_logo_argument,
                                    add_icon_pack_argument
                                ] + MARLIN_COMPILE_ARGUMENTS,
                                'T5UIC1',
                                default_font_hzk=T5UIC1_DEFAULT_HZK_FONT_FILE,
                                default_bootscreen=T5UIC1_DEFAULT_BOOTSCREEN,
                                default_logo=T5UIC1_DEFAULT_LOGO_IMAGE,
                                default_icon_pack='icon-packs/Jyers Icons/CREALITY.ICO'),
    'Voxelab-Aquila': PrinterChoice('Voxelab Aquila',
                                    'STM32F103RET6_voxelab_aquila',
                                    SHARED_ARGUMENTS + [
                                        add_logo_argument,
                                        add_icon_pack_argument
                                    ] + MARLIN_COMPILE_ARGUMENTS,
                                    'T5UIC1',
                                    default_font_hzk=T5UIC1_DEFAULT_HZK_FONT_FILE,
                                    default_bootscreen=T5UIC1_DEFAULT_BOOTSCREEN,
                                    default_logo=T5UIC1_DEFAULT_LOGO_IMAGE,
                                    default_icon_pack='icon-packs/alexqzd Icons/VOXELAB-RED.ICO'),
    'Voxelab-Aquila-X2': PrinterChoice('Voxelab Aquila X2',
                                       'STM32F103RET6_voxelab_aquila_N32',
                                       SHARED_ARGUMENTS + [
                                           add_logo_argument,
                                           add_icon_pack_argument
                                       ] + MARLIN_COMPILE_ARGUMENTS,
                                       'T5UIC1',
                                       default_font_hzk=T5UIC1_DEFAULT_HZK_FONT_FILE,
                                       default_bootscreen=T5UIC1_DEFAULT_BOOTSCREEN,
                                       default_logo=T5UIC1_DEFAULT_LOGO_IMAGE,
                                       default_icon_pack='icon-packs/alexqzd Icons/VOXELAB-RED.ICO',
                                       baseline_directory='baseline/Voxelab-Aquila'),
    'CR6': PrinterChoice('CR6',
                         'mega2560',
                         SHARED_ARGUMENTS + MARLIN_COMPILE_ARGUMENTS,
                         'T5L',
                         default_font_hzk=T5L_DEFAULT_HZK_FONT_FILE),
    'Other': PrinterChoice('Other',
                           '',
                           # TODO: How do we handle the build environment for this?
                           # Once we figure this out we can start supporting Marlin
                           # compilation.
                           SHARED_ARGUMENTS,
                           'T5UID1',
                           default_font_hzk=T5UID1_DEFAULT_HZK_FONT_FILE,
                           default_bootscreen=T5UID1_DEFAULT_BOOTSCREEN)
}
COLOR_SCHEMES = [
    ColorSchemeChoice('Default'),
    ColorSchemeChoice('AWCY-Black')
]
LANGUAGES = [
    LanguageChoice('English'),
    LanguageChoice('Chinese')
]
# Use a batch file for the Marlin build script on Windows and a shell script
# on other platforms (macOS, Linux - other platforms may work but are untested).
MARLIN_BUILD_SCRIPT_BASENAME = ('scripts/build_marlin.ps1' if os.name == 'nt'
                                else 'scripts/build_marlin.sh')
MBS_FULL_PATH = str(pathlib.Path(os.path.realpath(__file__)).resolve().parent.parent /
                    MARLIN_BUILD_SCRIPT_BASENAME)
MBS_WINDOWS = 'powershell -executionpolicy bypass -noexit "& "{MBS_FULL_PATH}"'
MARLIN_BUILD_SCRIPT = MBS_WINDOWS if os.name == 'nt' else MBS_FULL_PATH


def available_printers() -> List[str]:
    '''
    Return the currently available list of printers;
    we should compile for the selected printer.
    '''
    return list(PRINTER_OPTIONS.keys())


def available_color_schemes() -> List[str]:
    '''
    Return the currently available list of color schemes
    for the display firmware.
    '''
    return [str(x) for x in COLOR_SCHEMES]


def available_languages() -> List[str]:
    '''
    Return the currently available list of languages
    that the display firmware knows how to display.
    '''
    return [str(x) for x in LANGUAGES]


def rm_rf(path: str) -> None:
    '''
    Equivalent to `rm -rf ...`
    '''
    try:
        shutil.rmtree(path, ignore_errors=True)
        if os.path.exists(path):
            if os.path.isdir(path):
                os.rmdir(path)
            elif os.path.isfile(path):
                os.remove(path)
    except FileNotFoundError:
        pass


def cleanup_intermediate_files(file_list: List[str]) -> None:
    '''
    This is a helper function to cleanup any intermediate
    files that are generated.
    '''
    for f in file_list:
        rm_rf(f)


def recursive_copy_dir(from_path: str, to_path: str) -> None:
    '''
    Recursively copy a directory over to the to_path.
    The `to_path` should not already exist.
    '''
    shutil.copytree(from_path, to_path,
                    ignore_dangling_symlinks=True,
                    dirs_exist_ok=True)


def copy_file(from_path: str, to_path: str) -> None:
    '''
    Copy over a single file.
    '''
    try:
        shutil.copyfile(from_path, to_path)
    except shutil.SameFileError:
        pass


def copy_baseline_files(baseline_path: str, output_dir: str) -> None:
    '''
    Create the baseline version of the DWIN_SET directory using files
    from baseline_path.
    '''
    print(f'Cleaning up any existing files in directory {output_dir}')
    rm_rf(output_dir)
    print(f'Copying baseline files from {baseline_path} into {output_dir}')
    recursive_copy_dir(baseline_path, output_dir)


def compile_mainboard_firmware(marlin_dir: str, refresh_dir: bool, build_env: str) -> None:
    '''
    Compile the mainboard firmware here.
    '''
    command = [MARLIN_BUILD_SCRIPT, '-m', marlin_dir, '-e', build_env]
    if refresh_dir:
        command.append('-f')
    print(f'Calling script with `{" ".join(command)}`')
    subprocess.run(command, check=True)


def compile_ico(logo_image: str, icon_pack_path: str, compiled_ico_path: str) -> None:
    '''
    Add a logo image to an .ICO file.
    '''
    ico = DWIN_ICO.DWIN_ICO_File()
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            ico.splitFile(icon_pack_path, tmp_dir)
        except KeyError:
            pass
        copy_file(logo_image, str(tmp_dir) + T5UIC1_LOGO_FILE_NAME)
        ico.createFile(tmp_dir, compiled_ico_path)


def validate_file(file_path: str, expected_file_types: Set[str], err_message: str) -> None:
    '''
    Validate that the path passed in to the script for a particular file
    is one of the expected file types and actually exists (as a readable file).
    '''
    try:
        assert any((file_path.lower().endswith(f'.{_}') for _ in expected_file_types))
        assert os.path.exists(file_path) and os.path.isfile(file_path)
    except AssertionError as err:
        raise ValueError(err_message) from err


def add_printer_to_gooey_parser(gooey_subparser, printer: PrinterChoice) -> None:
    '''
    Call this function to add a printer to the subparsers list.

    args_to_add should be a list of functions which add an argument to
    a parser.
    '''
    printer_parser = gooey_subparser.add_parser(
        '-'.join(printer.name.split())
    )
    for add_arg_fn in printer.parser_arguments:
        add_arg_fn(printer_parser, printer)
    return printer_parser


# pylint: disable=too-many-arguments,too-many-statements,too-many-branches
def run_build(printer: PrinterChoice, baseline_path: str, output_dir: str,
              icon_pack_path: str, font_hzk_file: str,
              logo_image: str, bootscreen_image: str, color_scheme: ColorSchemeChoice,
              language: LanguageChoice, compile_mainboard: bool,
              marlin_path: str) -> None:
    '''
    This function does all of the heavy lifting of generating a DWIN_SET
    directory build. The main function just parsers the gooey args,
    then hands the results over to this function.
    '''
    # Validate each file passed in:
    validate_file(font_hzk_file, {'hzk'}, 'Invalid font file')
    if printer.screen_name == 'T5UIC1':
        validate_file(icon_pack_path, {'ico'}, 'Invalid icon pack')
        validate_file(bootscreen_image, {'jpeg', 'jpg'}, 'Invalid bootscreen image')
        validate_file(logo_image, {'jpeg', 'jpg'}, 'Invalid logo image')
    elif printer.screen_name == 'T5UID1':
        validate_file(bootscreen_image, {'bmp'}, 'Invalid bootscreen image')
        # TODO: add this back in once compiling T5UID1 .ICOs is doable:
        # validate_file(logo_image, {'ico'}, 'Invalid logo image')
    output_dir_path = pathlib.Path(output_dir) / DWIN_SET_DIRECTORY_NAME
    try:
        # Validate that we can write to a directory by checking
        # the write bit and execute bit via os.access:
        if os.path.exists(str(output_dir_path)):
            assert os.access(str(output_dir_path), os.W_OK | os.X_OK)
        else:
            output_dir_path.mkdir(parents=True, exist_ok=True)
            assert os.path.exists(str(output_dir_path))
    except (AssertionError, PermissionError, IOError) as err:
        raise IOError(f'Output directory (\'{str(output_dir_path)}\') is inaccessible!') from err
    if color_scheme != COLOR_SCHEMES[0] and not compile_mainboard:
        print('Selecting a non-default color scheme requires recompilation ' +
              'of the mainboard firmware. This flag was not chosen, so you will need to ' +
              'recompile it yourself for the color scheme changes to have an effect.')
    if compile_mainboard:
        if not marlin_path or not os.path.exists(marlin_path) or not os.access(marlin_path,
                                                                               os.W_OK | os.R_OK):
            raise ValueError(f'Specified --marlin-path (\'{marlin_path}\') is invalid!')

    # Copy over baseline files; this is important for the files -
    #   T5UIC1:
    #     * 1_English.jpg
    #     * 2_Chinese.jpg
    #     * T5UIC1.CFG
    #     * T5UIC1_V20_4页面_191022.BIN
    #   T5L:
    #     * All .icl, .BIN and .CFG files
    #   T5UID1:
    #     * All .BIN and .CFG files
    copy_baseline_files(baseline_path, str(output_dir_path))

    # TODO: eliminate some of this branching below with an object or dict to hold this info.

    # Copy over the bootscreen image:
    if printer.screen_name == 'T5UIC1':
        copy_file(bootscreen_image, str(output_dir_path / T5UIC1_BOOTSCREEN_IMAGE_FILE_NAME))
    elif printer.screen_name == 'T5UID1':
        copy_file(bootscreen_image, str(output_dir_path / T5UID1_BOOTSCREEN_IMAGE_FILE_NAME))
    else:
        print('Setting the bootscreen image for CR6 printers is currently unsupported')

    # Copy over the font file:
    if printer.screen_name == 'T5UIC1':
        copy_file(font_hzk_file, str(output_dir_path / T5UIC1_FONT_HZK_FILE_NAME))
    elif printer.screen_name == 'T5UID1':
        copy_file(font_hzk_file, str(output_dir_path / T5UID1_FONT_HZK_FILE_NAME))
    else:
        copy_file(font_hzk_file, str(output_dir_path / T5L_FONT_HZK_FILE_NAME))

    # Now compile the ICO file from the logo and the existing .ICO
    if printer.screen_name == 'T5UIC1':
        compiled_ico_path = 'temporary-icon-pack.ICO'
        print(f'Compiling temporary .ICO file: {compiled_ico_path}')
        compile_ico(logo_image, icon_pack_path, compiled_ico_path)
        # Copy over the compiled ICO file:
        copy_file(compiled_ico_path, str(output_dir_path / T5UIC1_ICON_PACK_FILE_NAME))
    elif icon_pack_path:
        print(f'Ignoring icon_pack_path {icon_pack_path} as it is not needed for ' +
              f'the selected printer: {str(printer)}')

    # Apply .patch files and otherwise edit the firmware source
    # files here:
    if compile_mainboard:
        print(f'Using the \'{str(color_scheme)}\' color scheme')
        print(f'Copying from {color_scheme.directory}')
        recursive_copy_dir(color_scheme.directory,
                           str(pathlib.Path(marlin_path) / DWIN_MAINBOARD_FIRMWARE_PATH))
        # TODO: rewrite this using something that applies patch files/diffs:
        # apply_patch_files(color_scheme.directory,
        #                   str(pathlib.Path(marlin_path) / DWIN_MAINBOARD_FIRMWARE_PATH))
        print(f'Using language: {str(language)}')
        if language != LANGUAGES[0]:
            print('TODO: Language choice support is not currently implemented')
            # Maybe:
            # recursive_copy_dir(language.directory,
            #                    str(pathlib.Path(marlin_path) / DWIN_MAINBOARD_FIRMWARE_PATH))
            # Or maybe:
            # apply_patch_files(language.directory,
            #                   str(pathlib.Path(marlin_path) / DWIN_MAINBOARD_FIRMWARE_PATH))
        print('Compiling mainboard firmware')
        compile_mainboard_firmware(marlin_path, False, printer.build_env)

    print(f'Finished building display firmware for {printer.name} in ' +
          f'output directory: {str(output_dir_path)}')
    # For now the only intermediate file is the compiled ico
    if printer.screen_name == 'T5UIC1':
        intermediate_files = [compiled_ico_path]
        print(f'Cleaning up intermediate files: {intermediate_files}')
        cleanup_intermediate_files(intermediate_files)
    print('Clean up completed!')
    print('All steps complete!')


# pylint: disable=too-many-locals
@Gooey(
    program_name='Creality DWIN LCD Customizer',
    clear_before_run=True,
    default_size=(1000, 750),
    sidebar_title='Printers',
    menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'Creality DWIN LCD Customizer',
                'description': 'A tool for compiling Creality DWIN LCD display firmware',
                'version': '1.0.0',
                'copyright': '2021',
                'website': 'https://gitlab.com/capekoviroboti/creality-dwin-lcd-customizer',
                'developer': 'capekoviroboti',
                'license': 'MIT'
            }, {
                'type': 'Link',
                'menuTitle': 'AWCY? Site',
                'url': 'https://areweconsumersyet.com'
            }, {
                'type': 'AboutDialog',
                'menuTitle': 'Thanks To',
                'name': 'Thanks To:',
                'description': ' * Planning and design by _invaderzip\n * ' +
                'Programming by capekoviroboti\n * Testing by ' +
                'capekoviroboti, invaderzip_ and trophytrout'
            }]
        }, {
            'name': 'Dependencies',
            'items': [{
                'type': 'Link',
                'menuTitle': 'dwin-ico-tools (dependency)',
                'url': 'https://github.com/b-pub/dwin-ico-tools'
            }, {
                'type': 'Link',
                'menuTitle': 'Jyers/Marlin (dependency/submodule)',
                'url': 'https://github.com/Jyers/Marlin/'
            }, {
                'type': 'Link',
                'menuTitle': 'alexqzd/Marlin (source of icon packs)',
                'url': 'https://github.com/alexqzd/Marlin/'
            }, {
                'type': 'Link',
                'menuTitle': 'Quint097/DWIN_Font_Tools (inspiration)',
                'url': 'https://github.com/Quint097/DWIN_Font_Tools'
            }]
        }, {
        'name': 'Help',
        'items': [{
            'type': 'Link',
            'menuTitle': 'Documentation',
            'url':
            'https://gitlab.com/capekoviroboti/creality-dwin-lcd-customizer/-/blob/main/README.md'
        }]
    }]
)
def main() -> None:
    '''
    Main function. Grab the command line arguments, parse
    them and use them to generate the final output file.

    The @Gooey decorator + use of GooeyParser in the place of
    argparse.ArgumentParser turns the script into a GUI program.
    '''
    # Parse the command line arguments:
    parser_description = 'A wizard for packaging customized display ' + \
        'firmware for printers with Creality DWIN LCDs'

    parser = GooeyParser(description=parser_description)
    printer_help = 'Select your printer from the drop down menu. If you don\'t ' + \
        'see your printer, select \'Other\''
    sub_parsers = parser.add_subparsers(help=printer_help, dest='printer')
    for printer_choice in PRINTER_OPTIONS.values():
        add_printer_to_gooey_parser(sub_parsers, printer_choice)

    args = parser.parse_args()
    printer = PRINTER_OPTIONS[args.printer]
    # Check if this printer does or does not use .ICO icon packs:
    if printer.screen_name == 'T5UIC1':
        icon_pack_path = args.icon_pack if args.icon_pack else printer.default_icon_pack
        logo_image = args.logo_image if args.logo_image else printer.default_logo
    else:
        # Make sure we don't check the Namespace for the `icon_pack` in this case
        icon_pack_path = printer.default_icon_pack
        logo_image = printer.default_logo
    baseline_path = args.baseline_path if args.baseline_path else f'{printer.directory}/DWIN_SET'
    output_dir = args.output_path if args.output_path else DEFAULT_OUTPUT_PATH
    font_hzk_file = args.font_hzk_file if args.font_hzk_file else printer.default_font_hzk
    bootscreen_image = (args.bootscreen_image if args.bootscreen_image
                        else printer.default_bootscreen)
    color_scheme = ColorSchemeChoice(args.color_scheme) if args.color_scheme else COLOR_SCHEMES[0]
    language = LanguageChoice(args.language) if args.language else LANGUAGES[0]
    if printer.screen_name == 'T5UID1':
        # TODO: Add support for mainboard compilation here.
        compile_mainboard = False
        marlin_path = ''
    else:
        compile_mainboard = args.compile_mainboard
        marlin_path = args.marlin_path
    # Send parsed args to the run_build() function
    run_build(
        printer, baseline_path, output_dir, icon_pack_path,
        font_hzk_file, logo_image, bootscreen_image, color_scheme,
        language, compile_mainboard, marlin_path
    )


if __name__ == '__main__':
    main()
