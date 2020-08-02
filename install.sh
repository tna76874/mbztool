#!/bin/bash
condaenv="mbz"
usage="$(basename "$0") [-h|-i|-p|-u|-s|-b|-e]  -- simple environment installer for $condaenv environment and docker image builder

where:
    -h  show this help text
    -i	install conda environment and packages from environment.yml
    -p	install pip packages from requirement.txt
    -u  remove conda environment
    -s  copy script to /usr/local/bin
    -b  build docker image
    -e	create environment.xml from anaconda environment
"

while [ "$1" != "" ]; do
    case $1 in
        -i | --install )       	conda env create -f environment.yml
				exit 1
                                ;;
        -p | --pip )            pip install -r requirements.txt --user
                                exit 1
                                ;;
        -u | --uninstall )    	conda remove -y --name $condaenv --all
				exit
                                ;;
        -e | --environment )    conda env export --from-history > environment.yml
                                exit 1
                                ;;
        -s | --system )         sudo cp mbzbot.py /usr/local/bin
                                sudo chmod 775 /usr/local/bin/mbzbot.py
                                exit 1
                                ;;
        -b | --build )          docker build -t tna76874/mbztool:latest .
                                exit 1
                                ;;
        * )                     echo "$usage" >&2
                                exit 1
    esac
    shift
done
