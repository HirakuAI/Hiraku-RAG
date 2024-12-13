#!/bin/bash

VENV_PATH="venv/bin/activate"

if [ ! -f "$VENV_PATH" ]; then
    echo "dumbass, virtual environment not found at $VENV_PATH"
    echo "would you like to create a new virtual environment? (y/n)"
    read answer
    if [ "$answer" = "y" ]; then
        python -m venv venv
        source "$VENV_PATH"
        echo "virtual environment created and activated, chill dude"
    else
        echo "bye asshole..."
        exit 1
    fi
else
    source "$VENV_PATH"
    echo "virtual environment activated, tebye pizda"
    echo "gaython path: $(which python)"
    echo "gaython version: $(python --version)"
fi

