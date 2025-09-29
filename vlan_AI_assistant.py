import json
import networkx as nx
from collections import defaultdict
from typing import Dict, List, Set
from dataclasses import dataclass
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv() 

@dataclass
class VLANIsland:
    vlan_id: int
    vlan_name: str
    island_id: int
    devices: Set[str]

class VLANIslandDetector:
    def __init__(self, network_file: str):
        """Initialize the VLAN island detector with network topology data."""
        self.network_data = self._load_network_data(network_file)
        self.physical_graph = nx.Graph()
        self.vlan_graphs = {}
        self.vlan_info = {}
        self.islands = defaultdict(list)
        self._build_network_graphs()
    
    def _load_network_data(self, network_file: str) -> dict:
        """Load and validate network topology data."""
        try:
            with open(network_file, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Network file {network_file} not found")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in network file")
    
    def _build_network_graphs(self):
        """Build physical and VLAN-specific network graphs."""
        # Build physical topology graph
        for device in self.network_data.get('devices', []):
            device_id = device['id']
            self.physical_graph.add_node(device_id, **device)
        
        # Add physical links
        for link in self.network_data.get('links', []):
            self.physical_graph.add_edge(
                link['source'], 
                link['target'],
                link_type=link.get('type', 'ethernet'),
                speed=link.get('speed', 'unknown')
            )
        
        # Build VLAN-specific graphs
        self._build_vlan_graphs()
    
    def _build_vlan_graphs(self):
        """Create separate graphs for each VLAN based on VLAN configurations."""
        for vlan in self.network_data.get('vlans', []):
            vlan_id = vlan['id']
            vlan_name = vlan['name']
            vlan_devices = set(vlan['devices'])
            
            # Store VLAN metadata
            self.vlan_info[vlan_id] = {
                'name': vlan_name,
                'description': vlan.get('description', ''),
                'devices': vlan_devices
            }
            
            # Create VLAN graph
            vlan_graph = nx.Graph()
            
            # Add devices to VLAN graph
            for device_id in vlan_devices:
                if device_id in self.physical_graph.nodes:
                    device_data = self.physical_graph.nodes[device_id]
                    vlan_graph.add_node(device_id, **device_data)
            
            # Add edges between VLAN devices that are physically connected
            for device1 in vlan_devices:
                for device2 in vlan_devices:
                    if (device1 != device2 and 
                        device1 in self.physical_graph.nodes and 
                        device2 in self.physical_graph.nodes and
                        self.physical_graph.has_edge(device1, device2)):
                        
                        # Copy edge attributes from physical graph
                        edge_data = self.physical_graph.edges[device1, device2]
                        vlan_graph.add_edge(device1, device2, **edge_data)
            
            self.vlan_graphs[vlan_id] = vlan_graph
    
    def detect_islands(self) -> Dict[int, List[VLANIsland]]:
        """Detect VLAN islands using connected components analysis."""
        self.islands = defaultdict(list)
        
        for vlan_id, vlan_graph in self.vlan_graphs.items():
            if len(vlan_graph.nodes) <= 1:
                continue
            
            # Find connected components (islands)
            connected_components = list(nx.connected_components(vlan_graph))
            
            if len(connected_components) > 1:
                # Multiple components = islands detected
                vlan_name = self.vlan_info[vlan_id]['name']
                for i, component in enumerate(connected_components):
                    island = VLANIsland(
                        vlan_id=vlan_id,
                        vlan_name=vlan_name,
                        island_id=i + 1,
                        devices=component
                    )
                    self.islands[vlan_id].append(island)
        
        return dict(self.islands)
    
    def generate_island_report(self) -> dict:
        """Generate the explicitly requested VLAN islands report."""
        islands_data = self.detect_islands()
        
        # Build the exact format requested
        report = {
            "vlans_with_islands": []
        }
        
        for vlan_id, islands in islands_data.items():
            vlan_info = self.vlan_info[vlan_id]
            vlan_report = {
                "vlan_id": vlan_id,
                "vlan_name": vlan_info['name'],
                "number_of_islands": len(islands),
                "islands": [
                    {
                        "island_id": island.island_id,
                        "devices": sorted(list(island.devices))
                    }
                    for island in islands
                ]
            }
            report["vlans_with_islands"].append(vlan_report)
        
        # Sort by VLAN ID for consistent output
        report["vlans_with_islands"].sort(key=lambda x: x["vlan_id"])
        
        return report
    
class VLANChatbot:
    def __init__(self, detector: VLANIslandDetector):
        """Initialize the AI-powered VLAN troubleshooting chatbot using Bosch Azure OpenAI."""
        self.detector = detector
        self.conversation_history = []
        self.model_name = "gpt-3.5-turbo"
        
        # Initialize Bosch Azure OpenAI client
        subscription_key = str(os.getenv("GENAIPLATFORM_FARM_SUBSCRIPTION_KEY"))
        if not subscription_key or subscription_key == "None":
            raise ValueError("GENAIPLATFORM_FARM_SUBSCRIPTION_KEY environment variable not set. Please set your Bosch Azure OpenAI subscription key.")
        base_url = str(os.getenv("AZURE_OPENAI_BASE_URL"))
        if not base_url or base_url == "None":
            raise ValueError("AZURE_OPENAI_BASE_URL environment variable not set. Please set your Azure OpenAI base URL.")

        api_version = str(os.getenv("AZURE_OPENAI_API_VERSION"))
        if not api_version or api_version == "None":
            raise ValueError("AZURE_OPENAI_API_VERSION environment variable not set. Please set your Azure OpenAI API version.")

        model_name = str(os.getenv("AZURE_OPENAI_MODEL"))
        if not model_name or model_name == "None":
            raise ValueError("AZURE_OPENAI_MODEL environment variable not set. Please set your Azure OpenAI model name.")
 
        self.client = AzureOpenAI(
            api_key=subscription_key,
            base_url=base_url,
            api_version=api_version,
        )
    
    def chat(self, user_message: str) -> str:
        """Process user message and return AI-generated response."""
        # Get current network context
        network_context = self._build_network_context()
        
        # Build conversation prompt
        system_prompt = self._build_system_prompt(network_context)
        
        try:
            # Updated API call for OpenAI v1.0+
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *self.conversation_history,
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1500,
                temperature=1
            )
            
            ai_response = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return ai_response
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."

    def _build_network_context(self) -> str:
        """Build context about the current network state for the AI."""
        report = self.detector.generate_island_report()
    
        # Calculate summary statistics
        total_vlans_with_islands = len(report['vlans_with_islands'])
        total_islands = sum(vlan['number_of_islands'] for vlan in report['vlans_with_islands'])
    
        context = f"""
Current Network Analysis Summary:
- VLANs with Islands: {total_vlans_with_islands}
- Total Islands Detected: {total_islands}

CRITICAL VLAN ISLAND ISSUES DETECTED:

"""
    
        # Group VLANs by severity (number of islands)
        critical_vlans = []  # 10+ islands
        major_vlans = []     # 3-9 islands  
        minor_vlans = []     # 2 islands
    
        for vlan_info in report['vlans_with_islands']:
            island_count = vlan_info['number_of_islands']
            if island_count >= 10:
                critical_vlans.append(vlan_info)
            elif island_count >= 3:
                major_vlans.append(vlan_info)
            else:
                minor_vlans.append(vlan_info)
    
    # Add critical VLANs (heavily fragmented)
        if critical_vlans:
            context += "🔴 CRITICAL - Heavily Fragmented VLANs:\n"
            for vlan in critical_vlans:
                context += f"  VLAN {vlan['vlan_id']} ({vlan['vlan_name']}): {vlan['number_of_islands']} islands\n"
            
                # Show key islands for heavily fragmented VLANs
                if vlan['number_of_islands'] > 15:
                    context += f"    Core island: {vlan['islands'][0]['devices']}\n"
                    context += f"    Individual isolated devices: {vlan['number_of_islands']-1} separate islands\n"
                else:
                    for i, island in enumerate(vlan['islands'][:3]):  # Show first 3 islands
                        context += f"    Island {island['island_id']}: {len(island['devices'])} devices\n"
                    if len(vlan['islands']) > 3:
                        context += f"    ... and {len(vlan['islands'])-3} more islands\n"
            context += "\n"
    
        # Add major VLANs
        if major_vlans:
            context += "🟠 MAJOR - Multi-Island VLANs:\n"
            for vlan in major_vlans:
                context += f"  VLAN {vlan['vlan_id']} ({vlan['vlan_name']}): {vlan['number_of_islands']} islands\n"
                for island in vlan['islands']:
                    devices_preview = island['devices'][:3] if len(island['devices']) > 3 else island['devices']
                    more_text = f" (+{len(island['devices'])-3} more)" if len(island['devices']) > 3 else ""
                    context += f"    Island {island['island_id']}: {devices_preview}{more_text}\n"
            context += "\n"
    
        # Add minor VLANs  
        if minor_vlans:
            context += "🟡 MINOR - Split VLANs (2 islands):\n"
            for vlan in minor_vlans:
                context += f"  VLAN {vlan['vlan_id']} ({vlan['vlan_name']}): {vlan['number_of_islands']} islands\n"
                for island in vlan['islands']:
                    context += f"    Island {island['island_id']}: {island['devices']}\n"
            context += "\n"
    
        # Add pattern analysis
        context += "PATTERN ANALYSIS:\n"
    
        # WiFi VLAN pattern
        wifi_vlans = [v for v in report['vlans_with_islands'] if 'wifi' in v['vlan_name'].lower()]
        if wifi_vlans:
            context += f"- WiFi VLANs severely fragmented: {len(wifi_vlans)} WiFi VLANs with {sum(v['number_of_islands'] for v in wifi_vlans)} total islands\n"
            context += f"  Issue: Access Points appear disconnected from WiFi controllers\n"
    
        # Security camera pattern
        security_vlans = [v for v in report['vlans_with_islands'] if 'security' in v['vlan_name'].lower() or 'camera' in v['vlan_name'].lower()]
        if security_vlans:
            context += f"- Security Camera VLANs fragmented: {len(security_vlans)} camera VLANs with islands\n"
            context += f"  Issue: Security cameras isolated from monitoring systems\n"
    
        # IoT pattern
        iot_vlans = [v for v in report['vlans_with_islands'] if 'iot' in v['vlan_name'].lower()]
        if iot_vlans:
            context += f"- IoT VLANs fragmented: {len(iot_vlans)} IoT VLANs with islands\n"
            context += f"  Issue: IoT devices cannot communicate with management systems\n"
    
        # Default VLAN issue
        default_vlans = [v for v in report['vlans_with_islands'] if v['vlan_id'] == 1 or 'default' in v['vlan_name'].lower()]
        if default_vlans:
            context += f"- Default VLAN fragmented: Critical infrastructure connectivity issue\n"
            for vlan in default_vlans:
                context += f"  DMZ island: {[d for d in vlan['islands'] if any('dmz' in str(island['devices']) for island in vlan['islands'])]}\n"
    
        return context
    
    def _build_system_prompt(self, network_context: str) -> str:
        """Build the system prompt for the AI assistant."""
        return f"""You are an expert network engineer specializing in VLAN troubleshooting and enterprise network topology analysis. 

{network_context}

Your role is to help network administrators understand and resolve VLAN island issues in enterprise networks. You should:

1. Provide clear, actionable technical guidance for Cisco/enterprise equipment
2. Explain complex networking concepts in understandable terms
3. Suggest specific configuration changes to resolve VLAN islands
4. Consider best practices for enterprise network design and security
5. Ask clarifying questions when needed to provide better assistance
6. Recognize device naming conventions (core, distribution, access switches, APs, etc.)

When recommending solutions:
- Always consider the impact on network security and performance
- Provide step-by-step CLI commands when possible (Cisco IOS syntax)
- Explain the reasoning behind your recommendations
- Consider the hierarchical network design (core/distribution/access)
- Warn about potential risks or side effects
- Consider VLAN trunking, STP, and other enterprise protocols

Key concepts to address:
- VLAN trunking configuration
- Spanning Tree Protocol implications
- Inter-VLAN routing considerations
- Access port vs trunk port configurations
- VLAN pruning and optimization

Be concise but thorough in your responses. Focus on practical solutions that can be implemented in enterprise environments.
"""