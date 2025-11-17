#!/bin/bash
cd /home/kavia/workspace/code-generation/ticket-booking-app-148553-149049/BackendAPI
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

