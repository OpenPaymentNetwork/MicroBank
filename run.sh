#!/bin/bash

cd $(dirname $0)

# Run the server in the foreground with auto-reload
bin/paster serve --reload development.ini "$@"
