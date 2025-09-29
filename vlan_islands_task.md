# VLAN Islands Detection Challenge

## Background
In enterprise networks, VLANs (Virtual Local Area Networks) are used to logically segment a single physical network into multiple independent broadcast domains. A common network design issue is the presence of "VLAN islands" - segments of the same VLAN that are disconnected from each other, creating isolated islands within what should be a unified broadcast domain.

VLAN islands represent a network design flaw that can cause various operational problems:
- Failed communication between devices that should be able to communicate
- Unexpected routing behavior
- Difficulty troubleshooting network issues
- Security vulnerabilities due to inconsistent policy enforcement

## Task Description
You are tasked with developing an AI-native solution that analyzes a network topology, identifies all VLAN islands, and provides an interactive chatbot interface to help network administrators fix these islands. Your solution must process a provided network topology file (`network.json`) containing 60 devices and their VLAN configurations, and determine which VLANs have islands and how many islands exist for each affected VLAN.

### Requirements:

1. **Data Processing**:
   - Parse the provided `network.json` file which contains:
     - Network devices (switches, routers, etc.)
     - Physical connections between devices
     - VLAN configurations on each device

2. **VLAN Islands Detection**:
   - For each VLAN in the network:
     - Determine if the VLAN forms a connected graph across all devices
     - If disconnected segments exist, identify them as islands
     - Count the total number of islands for each VLAN

3. **Output**:
   - Generate a report listing:
     - All VLANs with islands
     - The number of islands for each affected VLAN
     - The devices in each island
   - Format the output in a clear, structured format (JSON, CSV, or another structured format)

4. **AI-Powered Chatbot**:
   - Develop a conversational interface using generative AI that allows users to:
     - Ask questions about identified VLAN islands
     - Request recommendations for resolving connectivity issues
     - Receive step-by-step guidance for implementing fixes
     
5. **Performance**:
   - Your solution should efficiently handle the provided network with 60 devices and approximately 20 VLANs
   - Consider how your approach might scale to larger networks (hundreds or thousands of devices)

## Technical Guidelines:

1. **Implementation**:
   - You may use any programming language of your choice
   - Document all dependencies and include instructions for running your code
   - Include appropriate error handling and input validation
   - Add comments to explain your approach and any key algorithms

2. **Data Structures and Algorithms**:
   - Choose appropriate data structures to represent the network topology
   - Implement efficient graph traversal algorithms for island detection
   - Consider time and space complexity in your solution

3. **AI Integration**:
   - Use a generative AI model (e.g., GPT, Claude, or similar)
   - Design effective prompts that generate accurate network recommendations
   - Implement appropriate context management to maintain conversation coherence
   - Ensure the AI provides technically correct and actionable guidance

4. **Testing**:
   - Include test cases that validate your solution
   - Explain how you've verified the correctness of your results

## Evaluation Criteria:

Your solution will be evaluated on:

1. **Correctness**: Does the solution accurately identify all VLAN islands?
2. **Algorithm Efficiency**: Are the chosen algorithms and data structures appropriate and efficient?
3. **Problem Understanding**: Does the solution demonstrate a clear understanding of network topology and VLAN concepts?
4. **Chatbot Effectiveness**: Does the AI assistant provide accurate, helpful guidance for resolving VLAN islands?
5. **Extensibility**: Could the solution be easily extended or modified for similar network analysis tasks?

## Deliverables:

1. Source code implementing the VLAN islands detection algorithm and AI chatbot
2. A README file with:
   - Instructions for running the code
   - An explanation of your approach
   - Any assumptions made
   - Brief description of the algorithms used
   - Documentation of the AI chatbot's capabilities and limitations
3. Output report showing the detected VLAN islands
4. Sample conversation logs demonstrating the chatbot's ability to guide users through island remediation
5. (Optional) Visualization of the network topology highlighting the VLAN islands

## Timeframe:

You have 2 hours to complete this task. Quality is valued over quantity, so focus on delivering a well-thought-out solution rather than implementing every feature.

Good luck!