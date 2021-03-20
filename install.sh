#!/bin/bash
## Define paths
SCRIPT=$(readlink -f "$0")
DIR=$(dirname "$SCRIPT")

## Define some functions
function generatePassword() {
    tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 64
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
    read -e -p "UPLOAD LIMIT (GB): " -i "$UPLOAD_LIMIT_GB" UPLOAD_LIMIT_GB

    sed -i \
        -e "s#TCPPORT=.*#TCPPORT=${TCPPORT}#g" \
        -e "s#DOMAIN=.*#DOMAIN=${DOMAIN}#g" \
        -e "s#UPLOAD_LIMIT_GB=.*#UPLOAD_LIMIT_GB=${UPLOAD_LIMIT_GB}#g" \
        "$(dirname "$0")/.env"
}

# Configure nginx virtual host
nginxit() {
if $(confirm "Install nginx and certbot?") ; then
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install software-properties-common nginx -qy
    sudo DEBIAN_FRONTEND=noninteractive add-apt-repository universe
    sudo DEBIAN_FRONTEND=noninteractive add-apt-repository ppa:certbot/certbot
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install certbot python3-certbot-nginx -qy
fi
if [ ! -f .env ]; then
        echo -e "No .env file found." 
else
    cp nginx.example nginx
    source .env

    sed -i \
        -e "s/TCPPORT/${TCPPORT}/g" \
        -e "s/MYDOMAIN/${DOMAIN}/g" \
        "$(dirname "$0")/nginx"

    sudo cp nginx /etc/nginx/sites-available/"${DOMAIN}"
    rm nginx
    sudo ln -s /etc/nginx/sites-available/"${DOMAIN}" /etc/nginx/sites-enabled/"${DOMAIN}"
    sudo certbot --nginx --expand -d "${DOMAIN}"
fi
}

# Build docker image
builddocker() {
    cd "$DIR"
    docker-compose build --pull --no-cache
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
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy \
        docker-ce docker-ce-cli containerd.io docker-compose
    sudo usermod -aG docker $USER
    sudo systemctl restart docker
    newgrp docker
}

build_executable() {
    cd "$DIR"
    echo -e "Ensuring requirements ..."
    pip install -r requirements_web.txt -r requirements_build.txt -r requirements.txt > /dev/null 2>&1
    ./build.py --web
}

####### Parsing arguments
#Usage print
usage() {
    echo "Usage: $0 -[p|s|b|e|a|c|n|h]" >&2
    echo "
   -p,      Install prerequisites (docker, docker-compose)
   -s,      Setup environment
   -b,      Build docker image
   -e,      Build standalone executable
   -a,      Create anaconda environment
   -c,      Deploy mbzbot.py as system script
   -n,      Generate nginx virtual host
   -h,      Print this help text

If the script will be called without parameters, it will run:
    $0 -p -s -b -n
   ">&2
    exit 1
}

while getopts ':psbeacnh' opt
#putting : in the beginnnig suppresses the errors for invalid options
do
case "$opt" in
   'p')prerequisites;
       ;;
   's')environment;
       ;;
   'b')builddocker;
       ;;
   'e')build_executable;
       ;;
   'a')conda env create -f environment.yml;
       ;;
   'c')deploysystem;
       ;;
   'n')nginxit;
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
    if $(confirm "Generate nginx virtual host?") ; then
        nginxit
    fi
fi
