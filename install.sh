#!/bin/bash
## Define some functions
function generatePassword() {
    openssl rand -hex 16
}

confirm() {
    # call with a prompt string or use a default
    read -r -p "$@"" [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

#Setup environments
environment() {
    if [ ! -f .env ]; then
        cp env.example .env
    fi
    if [ ! -f docker-compose.yml ]; then
        cp docker-compose.yml.example docker-compose.yml
    fi    

    source .env

    read -e -p "TCPPORT: " -i "$TCPPORT" TCPPORT
    read -e -p "DOMAIN: " -i "$DOMAIN" DOMAIN

    sed -i \
        -e "s#TCPPORT=.*#TCPPORT=${TCPPORT}#g" \
        -e "s#DOMAIN=.*#DOMAIN=${DOMAIN}#g" \
        "$(dirname "$0")/.env"
}

# Configure nginx virtual host
nginxit() {
if [ ! -f .env ]; then
        echo -e "No .env file found." 
else
    cp nginx.example nginx
    source .env

    sed -i \
        -e "s/TCPPORT/${HTTPPORT}/g" \
        -e "s/MYDOMAIN/${HOSTNAME}/g" \
        "$(dirname "$0")/nginx"

    sudo cp nginx /etc/nginx/sites-available/"${HOSTNAME}"
    rm nginx
    sudo ln -s /etc/nginx/sites-available/"${HOSTNAME}" /etc/nginx/sites-enabled/"${HOSTNAME}"
    sudo certbot --nginx --expand -d "${HOSTNAME}"
fi
}

# Build docker image
builddocker() {
    docker build -t tna76874/mbztool:latest "$(dirname "$0")"
}

# Deploy mbzbot.py as system script
deploysystem() {
    sudo cp "$(dirname "$0")/"mbzbot.py /usr/local/bin
    sudo chmod 775 /usr/local/bin/mbzbot.py
}

# Install prerequisites (docker, docker-compose)
# https://docs.docker.com/engine/install/ubuntu/
prerequisites() {
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository \
        "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) \
        stable"
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install docker-ce docker-ce-cli containerd.io -qy
}

####### Parsing arguments
#Usage print
usage() {
    echo "Usage: $0 -[p|s|b|a|c|h]" >&2
    echo "
   -p,      Install prerequisites (docker, docker-compose)
   -s,      Setup environment
   -b,      Build docker image
   -a,      Create anaconda environment
   -c,      Deploy mbzbot.py as system script
   -h,      Print this help text

If the script will be called without parameters, it will run:
    $0 -p -s -b``
   ">&2
    exit 1
}

while getopts ':psbach' opt
#putting : in the beginnnig suppresses the errors for invalid options
do
case "$opt" in
   'p')prerequisites;
       ;;
   's')environment;
       ;;
   'b')builddocker;
       ;;
   'a')conda env create -f environment.yml;
       ;;
   'c')deploysystem;
       ;;
   'h')usage;
       ;;
    *) usage;
       ;;
esac
done
if [ $OPTIND -eq 1 ]; then
    if $(confirm "Install prerequisites (docker, docker-compose)?") ; then
        prerequisites
    fi
    if $(confirm "Setup environments?") ; then
        environment
    fi
    if $(confirm "Build docker image?") ; then
        builddocker
    fi
fi



