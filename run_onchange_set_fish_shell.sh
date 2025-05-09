#!/bin/bash

# Check if fish is installed
if command -v fish >/dev/null 2>&1; then
    FISH_PATH=$(command -v fish)

    # Check if fish is already the default shell
    if [ "$SHELL" = "$FISH_PATH" ]; then
        echo "Fish is already the default shell. Skipping."
        exit 0
    fi

    # Add fish to /etc/shells if it's not already there
    if ! grep -q "$FISH_PATH" /etc/shells; then
        echo "Adding $FISH_PATH to /etc/shells..."
        echo "$FISH_PATH" | sudo tee -a /etc/shells
    fi

    # Change the default shell to fish
    echo "Changing default shell to fish..."
    chsh -s "$FISH_PATH"
    echo "Fish shell set as default."
else
    echo "Fish shell is not installed. Aborting."
    exit 1
fi

