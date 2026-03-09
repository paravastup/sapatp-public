#!/bin/bash
# Script to start Ollama with network access for Docker containers

echo "Starting Ollama with network access for Docker..."
echo "This allows Docker containers to connect to Ollama"
echo ""

# Set Ollama to listen on all interfaces
export OLLAMA_HOST=0.0.0.0:11434

# Start Ollama
ollama serve

# Note: Keep this terminal window open while using the chatbot
# Press Ctrl+C to stop Ollama