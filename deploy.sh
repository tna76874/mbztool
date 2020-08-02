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

## Environment and docker-compose handling
if $(confirm "Set up environment and docker-compose?") ; then
    if [ ! -f .env ]; then
        TCPPORT="5893"
        DOMAIN="mydomain.xyz"
        cp env.example .env
    else
        source .env
    fi

    read -e -p "TCPPORT: " -i "$TCPPORT" TCPPORT
    read -e -p "DOMAIN: " -i "$DOMAIN" DOMAIN


    cp docker-compose.yml.example docker-compose.yml

    sed -i \
        -e "s#TCPPORT=.*#TCPPORT=${TCPPORT}#g" \
        -e "s#DOMAIN=.*#DOMAIN=${DOMAIN}#g" \
        "$(dirname "$0")/.env"
fi


## Nginx server handling
if $(confirm "Set up nginx virtual host?") ; then
    if [ ! -f .env ]; then
        echo -e "No .env file found." 
    else
        source .env
        cp nginx.example nginx
        sed -i \
            -e "s/TCPPORT/${TCPPORT}/g" \
            -e "s/MYDOMAIN/${DOMAIN}/g" \
            "$(dirname "$0")/nginx"
        sudo cp nginx /etc/nginx/sites-available/"${DOMAIN}"
        rm nginx
        if $(confirm "generate certificate?") ; then
            sudo ln -s /etc/nginx/sites-available/"${DOMAIN}" /etc/nginx/sites-enabled/"${DOMAIN}"
            sudo certbot --nginx --expand -d "${DOMAIN}"
        fi
    fi
fi