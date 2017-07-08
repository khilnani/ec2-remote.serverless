#!/bin/bash

scmd="serverless  "

s-install () {
    npm install -g serverless --upgrade
}

s-requirements () {
    rm -rf ./site-packages
    mkdir -p ./site-packages
    pip install --upgrade -t site-packages/ -r requirements.txt
}

s-deploy () {
    eval $scmd deploy --verbose
}

s-info () {
    eval $scmd info --verbose > INFO.md
    more INFO.md
}

s-remove () {
    if [ -n "$ZSH_VERSION" ]; then
        read "?Are you sure you want to continue?"
    else
        read -p  "?Are you sure you want to continue?" prompt
    fi
    eval $scmd remove --verbose
}

s-logs () {
    eval $scmd logs -f $1 -t --startTime 1m
}
