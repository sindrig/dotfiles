#!/bin/bash

pgrep -x mako > /dev/null && echo "🔔" || echo "🔕"

