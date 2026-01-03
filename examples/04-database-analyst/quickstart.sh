#!/bin/bash
# Quick start script for Database Analyst Agent example

echo "========================================"
echo "Database Analyst Agent - Quick Start"
echo "========================================"
echo

# Check if database exists
if [ ! -f "../../data/databases/sample.db" ]; then
    echo "Creating sample database..."
    python ../../scripts/setup_sample_database.py
    if [ $? -ne 0 ]; then
        echo "Failed to create database!"
        exit 1
    fi
    echo
fi

# Check for API key
if [ -z "$NVAPI_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: No API key found!"
    echo "Please set NVAPI_KEY or OPENAI_API_KEY environment variable"
    echo
    echo "Example:"
    echo "  export NVAPI_KEY=your_api_key_here"
    echo
    exit 1
fi

echo "Starting Database Analyst Agent..."
echo
python run.py --mode interactive
