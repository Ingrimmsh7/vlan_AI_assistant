# VLAN Islands Detection Solution

## Overview
This solution detects VLAN islands in enterprise networks and provides an AI-powered chatbot to help administrators resolve connectivity issues.

## Features
- **VLAN Island Detection**: Uses graph theory to identify disconnected VLAN segments
- **Comprehensive Reporting**: Generates detailed reports in JSON format
- **AI-Powered Chatbot**: Provides interactive troubleshooting assistance
- **Scalable Architecture**: Efficiently handles networks with hundreds of devices

## Installation

1. Install required packages:
pip install -r requirements.txt

2. Set up OpenAI environment and API key in .env


3. Prerequisites:
    Python 3.7 or higher
    An Azure OpenAI subscription key

    Setup:
    Clone the repository or download the code files.
    Create a .env file in the root directory and add your Azure OpenAI subscription key:

4. Run the Application:

    Execute the script:
    python main.py
    Follow the on-screen instructions to interact with the chatbot.

## Explanation
The approach involves creating a network graph using the NetworkX library to represent the physical and VLAN-specific topologies. The VLAN Island Detector identifies disconnected segments (islands) within VLANs by analyzing connected components in the graph. The chatbot leverages this analysis to provide contextual assistance to users, helping them troubleshoot VLAN issues effectively.

## Assumptions Made
The network topology data provided in the JSON file is correctly formatted and contains all necessary fields (devices, links, VLANs).
The user has a basic understanding of networking concepts, particularly VLANs and network topologies.
The Azure OpenAI service is accessible and properly configured with the provided subscription key.

## Brief Description of the Algorithms Used
Graph Representation: The physical network and VLANs are represented as graphs using NetworkX, allowing for efficient analysis of connectivity.
Connected Components: The algorithm identifies VLAN islands by detecting connected components in the VLAN-specific graphs. Each component represents a group of devices that are interconnected.
Chatbot Interaction: The chatbot uses a conversational model to process user queries and provide responses based on the current network context and detected VLAN issues.

## Documentation of the AI Chatbot's Capabilities and Limitations
Capabilities:
Provides insights into detected VLAN islands and their characteristics.
Offers troubleshooting advice and configuration suggestions for resolving VLAN issues.
Explains complex networking concepts in an understandable manner.
Maintains a conversation history to provide contextually relevant responses.

Limitations:
The chatbot's responses are based on the data provided and may not cover all possible scenarios.
It may not have real-time access to network changes unless the data is updated and reloaded.
The effectiveness of the chatbot depends on the clarity and specificity of user queries.

