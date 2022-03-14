#!/usr/bin/env bash
#===============================================================================
#
#          FILE: compile_dwin_ico_files.sh
# 
#         USAGE: ./compile_dwin_ico_files.sh [-v <Marlin Version>] [-o <Output>] [-i <Input>] [-c] [-d]
#                ./compile_dwin_ico_files.sh [-h]
# 
#   DESCRIPTION: Compile the .ICO files required for a logo change in the
#                Ender 3v2. For Marlin V1, we compile:
#                   * 9.ICO
#                For Marlin V2, we compile:
#                   * 3.ICO
#                   * 4.ICO
#                   * 7.ICO
#                We need to have some logos available, in a few sizes:
#                   * 130 x 17
#                   * 128 x 40
#                   * 266 x 238
#                If the script is invoked with the -c flag, we will copy over the logo
#                images required from the 'images/logos/' directory. Otherwise,
#                the script will assume that they are available in the input directory.
# 
#       OPTIONS:
#               -v  -- Specify which version of Marlin we are building for.
#               -i  -- Specify the input directory, where the source .ico and
#                      logo files are kept.
#               -o  -- Specify the output directory.
#               -c  -- Copy images from 'images/logos' into the input directory.
#               -d  -- Turn on debug mode.
#               -h  -- Print the help info and exit.
#  REQUIREMENTS: python3, git
#         NOTES: ---
#===============================================================================

set -Eeuo pipefail

# Set defaults
marlin_version="2"
input_path="input"
output_path="output"
copy_mode="false"
debug_mode="false"

# Print the usage info and exit with the specified return code.
usage() {
    printf "Usage: %s [-v <Marlin Version>] [-i <Input Dir>] [-o <Output Dir>] [-c] [-d]\n" "$0"
    printf "       %s -h\n" "$0"
    printf "Arguments:\n"
    printf "              -v  -- Specify which version of Marlin we are building for.\n"
    printf "              -i  -- Specify the input directory, where the source .ico and\n"
    printf "                     logo files are kept.\n"
    printf "              -o  -- Specify the output directory.\n"
    printf "              -c  -- Copy images from 'images/logos' into the input directory.\n"
    printf "              -d  -- Turn on debug mode.\n"
    printf "              -h  -- Print this message and exit.\n"
    exit 1
}

# Print info if debug mode is on:
debug_printf() {
    if [[ "${debug_mode}" == "true" ]]; then
        printf "$@"
    fi
}

# Check that the required files are available for the specified
# version of Marlin, in the input_path directory:
check_input() {
    if [[ ! -d "${input_path}" ]]; then
        printf "ERROR: You must either specify the input path with the -i flag or put the required files in the input/ directory!\n"
        exit 1
    fi
    if [[ "${marlin_version}" == "1" ]]; then
        if [[ ! -f "${input_path}/9.ICO" ]] || \
           [[ ! -f "${input_path}/130x17.jpg" ]]; then
            # For Marlin v1, we want to check for 9.ICO and a single 130x17 logo:
            printf "For Marlin v1, this script requires that the input directory '%s' contain " "${input_path}"
            printf "the starting .ICO file 9.ICO and the logo 130x17.jpg\n"
            exit 1
        fi
        debug_printf "Marlin v1; have needed files\n"
    elif [[ "${marlin_version}" == "2" ]]; then
         if [[ ! -f "${input_path}/3.ICO" ]] || \
            [[ ! -f "${input_path}/4.ICO" ]] || \
            [[ ! -f "${input_path}/7.ICO" ]] || \
            [[ ! -f "${input_path}/130x17.jpg" ]] || \
            [[ ! -f "${input_path}/128x40.jpg" ]] || \
            [[ ! -f "${input_path}/266x238.jpg" ]]; then
            # For Marlin v2, we want to check for 3.ICO, 4.ICO, and 7.ICO and
            # 130x17, 128x40 and 266x238 logos:
            printf "For Marlin v2, this script requires that the input directory '%s' contain " "${input_path}"
            printf "the starting .ICO files 3.ICO, 4.ICO and 7.ICO as well as the logo files "
            printf "130x17.jpg, 128x40.jpg and 266x238.jpg\n"
            exit 1
        fi
        debug_printf "Marlin v2; have needed files\n"
    fi
    printf "Input directory '%s' has all expected input files.\n" "${input_path}"
}

# Clean up the intermediate unpacked .ICO directories, from any previous runs:
clean_intermediate_directories() {
    rm -rf "3-ico-dir"
    rm -rf "4-ico-dir"
    rm -rf "7-ico-dir"
    rm -rf "9-ico-dir"
}

# Parse the commandline arguments:
while getopts "v:i:o:cdh" opt; do
    case "${opt}" in
        v)
            marlin_version="${OPTARG}"
            pattern="[12]"
            if [[ ! "${marlin_version}" =~ $pattern ]]; then
                printf "ERROR: Unknown Marlin version specified! Version must be 1 or 2.\n"
                exit 1
            fi
            ;;
        i)
            input_path="${OPTARG}"
            ;;
        o)
            output_path="${OPTARG}"
            ;;
        c)
            copy_mode="true"
            ;;
        d)
            debug_mode="true"
            ;;
        h)
            usage 0
            ;;
        *)
            # Unknown argument(s):
            printf "Unknown argument: %s\n" "${opt}"
            usage 1
            ;;
    esac
done

# First, if we are in copy mode, copy over the required logo files:
if [[ "${copy_mode}" == "true" ]]; then
    debug_printf "Copying over images from 'images/logos/' into '%s'\n" "${input_path}"
    cp images/logos/*.jpg "${input_path}"
fi

# Check the input directory has all files we will need:
check_input

# Clean up any old runs:
clean_intermediate_directories

# Install the Python packages we will need. At present, this is limited to
# Pillow, an implementation of the Python image processing library.
pip3 install pillow

# Grab the dwin-ico-tools from GitHub:
if [[ ! -d dwin-ico-tools ]]; then
    debug_printf "Grabbing dwin-ico-tools from GitHub...\n"
    git clone https://github.com/b-pub/dwin-ico-tools.git
else
    debug_printf "Using already downloaded dwin-ico-tools...\n"
fi

# Make sure that the output directory exists:
mkdir -p "${output_path}"

# Now actually compile the required .ICO files:
printf "Compiling .ICO files...\n"
if [[ "${marlin_version}" == "1" ]]; then
    debug_printf "Compiling 9.ICO\n"
    python3 dwin-ico-tools/splitIco.py "${input_path}/9.ICO" "9-ico-dir"
    cp "${input_path}/130x17.jpg" "9-ico-dir/000-ICO_LOGO.jpg"
    rm -f "${output_path}/9.ICO"
    python3 dwin-ico-tools/makeIco.py "9-ico-dir" "${output_path}/9.ICO"
else
    debug_printf "Compiling 3.ICO\n"
    python3 dwin-ico-tools/splitIco.py "${input_path}/3.ICO" "3-ico-dir"
    cp "${input_path}/266x238.jpg" "3-ico-dir/000-ICO_LOGO.jpg"
    rm -f "${output_path}/3.ICO"
    python3 dwin-ico-tools/makeIco.py "3-ico-dir" "${output_path}/3.ICO"
    debug_printf "Compiling 4.ICO\n"
    python3 dwin-ico-tools/splitIco.py "${input_path}/4.ICO" "4-ico-dir"
    cp "${input_path}/128x40.jpg" "4-ico-dir/000-ICO_LOGO.jpg"
    rm -f "${output_path}/4.ICO"
    python3 dwin-ico-tools/makeIco.py "4-ico-dir" "${output_path}/4.ICO"
    debug_printf "Compiling 7.ICO\n"
    python3 dwin-ico-tools/splitIco.py "${input_path}/7.ICO" "7-ico-dir"
    cp "${input_path}/130x17.jpg" "7-ico-dir/000-ICO_LOGO.jpg"
    rm -f "${output_path}/7.ICO"
    python3 dwin-ico-tools/makeIco.py "7-ico-dir" "${output_path}/7.ICO"
fi

printf "Compilation complete! The .ICO files are available in '%s'\n" "${output_path}"
# If we are in debug mode, we want to hold on to the intermediate files, so avoid cleaning up:
if [[ "${debug_mode}" == "true" ]]; then
    debug_printf "Skipping clean up!\n"
    exit 0
fi
printf "Cleaning up...\n"
clean_intermediate_directories
printf "Clean up complete!\nDone!\n"
