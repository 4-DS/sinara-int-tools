#!/bin/bash
#set -euxo pipefail
set -euo pipefail
# Parse arguments
while [ $# -gt 0 ]; do
    if [[ $1 == *"--"* ]]; then
        v="${1/--/}"
        declare $v="$2"
    fi
    shift
done

containerName=jovyan-single-use

instanceName="${instanceName:-$containerName}"

echo "Note, that image tag for your Docker model image is the step run-id"
echo "Note, that image name for your Docker model image is the step output entity (bentoservice)"

read -p "Please, enter ENTITY_PATH for your bentoservice: " bentoservicePath
defaultImageTag=$(basename $(dirname "$bentoservicePath")) 

read -p "Please, enter Docker registry address for your model image: " dockerRegistry

modelImageTag="${defaultImageTag}"

bentoservice_dir="$(basename $bentoservicePath)"

rm -rf $bentoservice_dir

docker cp $instanceName:/$bentoservicePath .

cd $bentoservice_dir

unzip model.zip
rm -f _SUCCESS
rm -f model.zip
source save_info.txt

modelName=$(echo $BENTO_SERVICE | sed 's/\.[^.]*$//')
docker build . -t $dockerRegistry/$modelName:$modelImageTag
