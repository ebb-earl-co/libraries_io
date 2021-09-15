#!/bin/sh

# As of 2020-01-12, the most recent version of the libraries.io data is 1.6.0.
# The below variables have defaults set for this version, so that this script
# can be run without arguments if convenient; i.e. `. download_libraries_io_open_data.sh`
# N.b. calling without arguments will download the 24.9 GB file into the PWD and
# subsequently check the MD5 checksum of the downloaded file.

URL=${1:-https://zenodo.org/record/2536573/files/libraries-1.6.0-2020-01-12.tar.gz?download=1}
FILENAME=${2:-libraries-1.6.0-2020-01-12.tar.gz}
CHECKSUM=${3:-4f2275284b86827751bb31ce74238b15}

curl -SL -XGET "$URL" --output "${FILENAME}"
ACTUAL=$(md5 -q "${FILENAME}")

if [ "${ACTUAL}" = "${CHECKSUM}" ]; then
    2<&1 echo "${ACTUAL}"
    res=0
else
    2<&1 echo "Checksum does not match: Deleting ${FILENAME}"
    rm -f "${FILENAME}"
    res=1
fi

exit $res
