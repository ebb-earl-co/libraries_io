#!/bin/sh

# As of 2018-12-22, the most recent version of the libraries.io data is 1.4.0.
# The below variables have defaults set for this version, so that this script
# can be run without arguments if convenient; i.e. `. download_libraries_io_open_data.sh`
# N.b. calling without arguments will download the 12.2 GB file into the PWD.

URL=${1:-https://zenodo.org/record/2536573/files/Libraries.io-open-data-1.4.0.tar.gz?download=1}
FILENAME=${2:-Libraries.io-open-data-1.4.0.tar.gz}
CHECKSUM=${3:-5bf302e6944cb1a8283a316f65b24093}

curl -SL -XGET "$URL" --output "${FILENAME}"
ACTUAL=$(md5 -q "${FILENAME}")

if [ "${ACTUAL}" = "${CHECKSUM}" ]; then
    2<&1 echo "${ACTUAL}"
    res=0
else
    2<&1 echo "Checksum did not match. Deleting ${FILENAME}"
    rm -f "${FILENAME}"
    res=1
fi

exit $res