#!/bin/bash - 
#===============================================================================
#
#          FILE: build_marlin.sh
# 
#         USAGE: ./build_marlin.sh -m "<Marlin directory>" [-f] [-b "<Branch>"]
#                                  [-e "Build environment"] [-p "Platformio penv path"]
#                ./build_marlin.sh -h
# 
#   DESCRIPTION: Build Marlin
# 
#       OPTIONS:
#                 * -m  -- Specify the Marlin directory.
#                 * -b  -- Specify the branch to use; defaults to current branch.
#                 * -e  -- Specify the build environment; defaults to
#                          "STM32F103RET6_creality".
#                 * -p  -- Specify the path to the Platformio penv; defaults to
#                          "${HOME}/.platformio/penv/bin/activate".
#                 * -f  -- Fetch the latest code in the current branch.
#                 * -h  -- Print help info and exit.
#  REQUIREMENTS: git, python
#         NOTES: ---
#===============================================================================

set -Eeuo pipefail

# Set defaults
fetch=false
marlin_dir=""
branch_name=""
current_branch_name="$(git branch --show-current)"
build_env="STM32F103RET6_creality" # Default: Ender 3v2 build env
platformio_penv_path="${HOME}/.platformio/penv/bin/activate"
platformio_penv_set_manually=false

# Print the usage info
usage() {
    printf "Usage: %s -m \"<Marlin directory>\" [-f] [-b \"<Branch>\"] " "$0"
    printf "[-e \"<Build environment>\"] [-p \"<Platformio penv path>\"]\n"
    printf "       %s -h\n" "$0"
    printf "Arguments:\n"
    printf "             -m  -- Specify the Marlin directory.\n"
    printf "             -b  -- Specify the branch to use. Default: current branch (%s).\n" "${current_branch_name}"
    printf "             -e  -- Specify the build environment to use. Default: %s (Ender 3v2).\n" "${build_env}"
    printf "             -p  -- Specify the Platformio penv path. Default: %s\n" "${platformio_penv_path}"
    printf "             -f  -- Pull the latest commits from the remote.\n"
    printf "             -h  -- Print the help info and exit.\n"
    exit $1
}

while getopts "m:b:e:fh" opt; do
    case "${opt}" in
        m)
            marlin_dir="${OPTARG}"
            ;;
        f)
            fetch=true
            ;;
        b)
            branch_name="${OPTARG}"
            ;;
        e)
            build_env="${OPTARG}"
            ;;
        p)
            platformio_penv_path="${OPTARG}"
            platformio_penv_set_manually=true
            ;;
        h)
            usage 0
            ;;
        *)
            printf "Unknown argument: %s\n" "${opt}"
            usage 1
            ;;
    esac
done

if [[ -z "${marlin_dir}" ]]; then
    printf "ERROR: Marlin directory must be set.\n"
    exit 1
elif [[ ! -d "${marlin_dir}" ]]; then
    printf "ERROR: Marlin directory must exist.\n"
    exit 1
fi

if [[ -z "${build_env}" ]]; then
    printf "ERROR: Build environment must exist.\n"
    exit 1
fi

if [[ ! -f "${platformio_penv_path}" ]]; then
    printf "ERROR: bad Platformio path."
    if [[ "${platformio_penv_set_manually}" == "false" ]]; then
        printf " Are you sure Platformio is installed (correctly)? If so, specify the path.\n"
    else
        printf " Is there a typo in the path specified: %s\n" "${platformio_penv_path}"
    fi
    exit 1
fi

cd "${marlin_dir}"

printf "Currently on branch: '%s'\n" "${current_branch_name}"
if [[ -n "${branch_name}" ]]; then
    printf "Branch '%s' was specified.\n" "${branch_name}"
    if [[ "${current_branch_name}" != "${branch_name}" ]]; then
        printf "Switching branches!\n"
        git checkout "${branch_name}"
    else
        printf "Current branch matches specified branch.\n"
    fi
fi

if [[ "${fetch}" == "true" ]]; then
    git pull
fi

# Source the penv for platformio
source "${platformio_penv_path}"

# Clean:
platformio run --target clean -e "${build_env}"
# Run the build:
platformio run -e "${build_env}"
