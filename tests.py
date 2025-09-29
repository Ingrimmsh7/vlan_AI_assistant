import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import networkx as nx
from vlan_AI_assistant import VLANIslandDetector, VLANChatbot

class TestVLANIslandDetector(unittest.TestCase):
    """Test cases for VLAN Island Detection functionality."""
    
    def setUp(self):
        """Set up test data and temporary files."""
        self.test_network_simple = {
            "devices": [
                {"id": "sw-01", "type": "switch", "role": "core"},
                {"id": "sw-02", "type": "switch", "role": "access"},
                {"id": "sw-03", "type": "switch", "role": "access"},
                {"id": "sw-04", "type": "switch", "role": "access"}
            ],
            "links": [
                {"source": "sw-01", "target": "sw-02", "type": "ethernet"},
                # Intentionally missing link between sw-02 and sw-03 to create island
                {"source": "sw-03", "target": "sw-04", "type": "ethernet"}
            ],
            "vlans": [
                {
                    "id": 100,
                    "name": "Test-VLAN",
                    "description": "Test VLAN for islands",
                    "devices": ["sw-01", "sw-02", "sw-03", "sw-04"]
                }
            ]
        }
        
        self.test_network_complex = {
            "devices": [
                {"id": "core-01", "type": "switch", "role": "core"},
                {"id": "core-02", "type": "switch", "role": "core"},
                {"id": "dist-01", "type": "switch", "role": "distribution"},
                {"id": "acc-01", "type": "switch", "role": "access"},
                {"id": "acc-02", "type": "switch", "role": "access"},
                {"id": "ap-01", "type": "access_point", "role": "wireless"},
                {"id": "ap-02", "type": "access_point", "role": "wireless"},
                {"id": "ap-03", "type": "access_point", "role": "wireless"}
            ],
            "links": [
                {"source": "core-01", "target": "core-02", "type": "ethernet"},
                {"source": "core-01", "target": "dist-01", "type": "ethernet"},
                {"source": "dist-01", "target": "acc-01", "type": "ethernet"},
                {"source": "acc-01", "target": "ap-01", "type": "ethernet"},
                # Gap here - ap-02 and ap-03 not connected to create islands
            ],
            "vlans": [
                {
                    "id": 1,
                    "name": "Default",
                    "description": "Default VLAN",
                    "devices": ["core-01", "core-02", "dist-01", "acc-01", "acc-02"]
                },
                {
                    "id": 30,
                    "name": "WiFi-Corporate",
                    "description": "Corporate WiFi VLAN",
                    "devices": ["core-01", "core-02", "ap-01", "ap-02", "ap-03"]
                }
            ]
        }
        
        # Create temporary files
        self.temp_dir = tempfile.mkdtemp()
        self.simple_network_file = os.path.join(self.temp_dir, "simple_network.json")
        self.complex_network_file = os.path.join(self.temp_dir, "complex_network.json")
        
        with open(self.simple_network_file, 'w') as f:
            json.dump(self.test_network_simple, f)
        
        with open(self.complex_network_file, 'w') as f:
            json.dump(self.test_network_complex, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_network_data_valid(self):
        """Test loading valid network data."""
        detector = VLANIslandDetector(self.simple_network_file)
        self.assertEqual(len(detector.network_data['devices']), 4)
        self.assertEqual(len(detector.network_data['vlans']), 1)
    
    def test_load_network_data_invalid_file(self):
        """Test loading non-existent file raises correct exception."""
        with self.assertRaises(FileNotFoundError):
            VLANIslandDetector("non_existent_file.json")
    
    def test_load_network_data_invalid_json(self):
        """Test loading invalid JSON raises correct exception."""
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("invalid json content {")
        
        with self.assertRaises(ValueError):
            VLANIslandDetector(invalid_file)
    
    def test_physical_graph_construction(self):
        """Test physical network graph is built correctly."""
        detector = VLANIslandDetector(self.simple_network_file)
        
        # Check nodes
        self.assertEqual(len(detector.physical_graph.nodes), 4)
        self.assertIn("sw-01", detector.physical_graph.nodes)
        self.assertIn("sw-04", detector.physical_graph.nodes)
        
        # Check edges
        self.assertEqual(len(detector.physical_graph.edges), 2)
        self.assertTrue(detector.physical_graph.has_edge("sw-01", "sw-02"))
        self.assertTrue(detector.physical_graph.has_edge("sw-03", "sw-04"))
        self.assertFalse(detector.physical_graph.has_edge("sw-02", "sw-03"))
    
    def test_vlan_graph_construction(self):
        """Test VLAN-specific graphs are built correctly."""
        detector = VLANIslandDetector(self.simple_network_file)
        
        # Check VLAN graph exists
        self.assertIn(100, detector.vlan_graphs)
        vlan_graph = detector.vlan_graphs[100]
        
        # Check VLAN graph has correct devices
        self.assertEqual(len(vlan_graph.nodes), 4)
        
        # Check VLAN graph has correct edges (only where physical connections exist)
        self.assertTrue(vlan_graph.has_edge("sw-01", "sw-02"))
        self.assertTrue(vlan_graph.has_edge("sw-03", "sw-04"))
        self.assertFalse(vlan_graph.has_edge("sw-02", "sw-03"))  # No physical connection
    
    def test_simple_island_detection(self):
        """Test detection of islands in simple network."""
        detector = VLANIslandDetector(self.simple_network_file)
        islands = detector.detect_islands()
        
        # Should detect islands in VLAN 100
        self.assertIn(100, islands)
        self.assertEqual(len(islands[100]), 2)  # Two islands
        
        # Check island composition
        island_devices = [set(island.devices) for island in islands[100]]
        expected_islands = [{"sw-01", "sw-02"}, {"sw-03", "sw-04"}]
        
        for expected in expected_islands:
            self.assertIn(expected, island_devices)
    
    def test_complex_island_detection(self):
        """Test detection of islands in complex network."""
        detector = VLANIslandDetector(self.complex_network_file)
        islands = detector.detect_islands()
        
        # VLAN 1 should have islands (acc-02 is isolated)
        self.assertIn(1, islands)
        
        # VLAN 30 should have severe fragmentation (APs not connected)
        self.assertIn(30, islands)
        wifi_islands = islands[30]
        self.assertGreaterEqual(len(wifi_islands), 3)  # At least 3 islands
    
    def test_no_islands_scenario(self):
        """Test scenario where no islands exist."""
        # Create fully connected network
        connected_network = {
            "devices": [
                {"id": "sw-01", "type": "switch"},
                {"id": "sw-02", "type": "switch"},
                {"id": "sw-03", "type": "switch"}
            ],
            "links": [
                {"source": "sw-01", "target": "sw-02", "type": "ethernet"},
                {"source": "sw-02", "target": "sw-03", "type": "ethernet"}
            ],
            "vlans": [
                {
                    "id": 10,
                    "name": "Connected-VLAN",
                    "devices": ["sw-01", "sw-02", "sw-03"]
                }
            ]
        }
        
        connected_file = os.path.join(self.temp_dir, "connected.json")
        with open(connected_file, 'w') as f:
            json.dump(connected_network, f)
        
        detector = VLANIslandDetector(connected_file)
        islands = detector.detect_islands()
        
        # Should detect no islands
        self.assertEqual(len(islands), 0)
    
    def test_single_device_vlan(self):
        """Test VLAN with single device (should not be considered an island)."""
        single_device_network = {
            "devices": [{"id": "sw-01", "type": "switch"}],
            "links": [],
            "vlans": [
                {
                    "id": 99,
                    "name": "Single-Device-VLAN",
                    "devices": ["sw-01"]
                }
            ]
        }
        
        single_file = os.path.join(self.temp_dir, "single.json")
        with open(single_file, 'w') as f:
            json.dump(single_device_network, f)
        
        detector = VLANIslandDetector(single_file)
        islands = detector.detect_islands()
        
        # Single device VLANs should not be considered islands
        self.assertEqual(len(islands), 0)
    
    def test_generate_island_report_structure(self):
        """Test the structure of generated island report."""
        detector = VLANIslandDetector(self.simple_network_file)
        report = detector.generate_island_report()
        
        # Check report structure
        self.assertIn("vlans_with_islands", report)
        self.assertIsInstance(report["vlans_with_islands"], list)
        
        # Check VLAN entry structure
        if report["vlans_with_islands"]:
            vlan_entry = report["vlans_with_islands"][0]
            required_fields = ["vlan_id", "vlan_name", "number_of_islands", "islands"]
            for field in required_fields:
                self.assertIn(field, vlan_entry)
            
            # Check island structure
            if vlan_entry["islands"]:
                island = vlan_entry["islands"][0]
                self.assertIn("island_id", island)
                self.assertIn("devices", island)
                self.assertIsInstance(island["devices"], list)

    def test_vlan_info_storage(self):
        """Test VLAN metadata is stored correctly."""
        detector = VLANIslandDetector(self.simple_network_file)
        
        # Check VLAN info is stored
        self.assertIn(100, detector.vlan_info)
        vlan_info = detector.vlan_info[100]
        
        self.assertEqual(vlan_info['name'], "Test-VLAN")
        self.assertEqual(vlan_info['description'], "Test VLAN for islands")
        self.assertIn("sw-01", vlan_info['devices'])

class TestVLANChatbot(unittest.TestCase):
    """Test cases for VLAN Chatbot functionality."""
    
    def setUp(self):
        """Set up test chatbot with mock detector."""
        # Create a simple test network
        self.test_network = {
            "devices": [
                {"id": "sw-01", "type": "switch", "role": "core"},
                {"id": "sw-02", "type": "switch", "role": "access"}
            ],
            "links": [],  # No links = islands
            "vlans": [
                {
                    "id": 100,
                    "name": "Test-VLAN",
                    "description": "Test VLAN",
                    "devices": ["sw-01", "sw-02"]
                }
            ]
        }
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_network.json")
        
        with open(self.test_file, 'w') as f:
            json.dump(self.test_network, f)
        
        self.detector = VLANIslandDetector(self.test_file)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch.dict(os.environ, {'AZURE_OPENAI_BASE_URL': 'test-url'})
    @patch.dict(os.environ, {'AZURE_OPENAI_API_VERSION': 'test-version'})
    @patch.dict(os.environ, {'AZURE_OPENAI_MODEL': 'test-model'})
    @patch('vlan_AI_assistant.AzureOpenAI')
    def test_chatbot_initialization(self, mock_openai):
        """Test chatbot initializes correctly with API key."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        chatbot = VLANChatbot(self.detector)
        self.assertEqual(chatbot.detector, self.detector)
        self.assertEqual(len(chatbot.conversation_history), 0)
    
    def test_chatbot_initialization_no_api_key(self):
        """Test chatbot fails gracefully without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                VLANChatbot(self.detector)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('vlan_AI_assistant.AzureOpenAI')
    def test_build_network_context(self, mock_openai):
        """Test network context building."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        chatbot = VLANChatbot(self.detector)
        context = chatbot._build_network_context()
        
        # Check context contains expected information
        self.assertIn("Network Analysis", context)
        self.assertIn("VLAN", context)
        self.assertIn("islands", context.lower())
    
    @patch.dict(os.environ, {'GENAIPLATFORM_FARM_SUBSCRIPTION_KEY': 'test-key'})
    @patch('vlan_AI_assistant.AzureOpenAI')
    def test_chat_success(self, mock_openai):
        """Test successful chat interaction."""
        # Setup mock client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
    
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is the AI response"
        mock_client.chat.completions.create.return_value = mock_response
    
        # Create chatbot
        chatbot = VLANChatbot(self.detector)
    
        # Mock the private methods
        with patch.object(chatbot, '_build_network_context', return_value="Mock network context"):
            with patch.object(chatbot, '_build_system_prompt', return_value="Mock system prompt"):
                # Execute
                result = chatbot.chat("What are the VLAN issues?")
            
                # Assert
                self.assertEqual(result, "This is the AI response")
                self.assertEqual(len(chatbot.conversation_history), 2)
                self.assertEqual(chatbot.conversation_history[0]["role"], "user")
                self.assertEqual(chatbot.conversation_history[0]["content"], "What are the VLAN issues?")
                self.assertEqual(chatbot.conversation_history[1]["role"], "assistant")
                self.assertEqual(chatbot.conversation_history[1]["content"], "This is the AI response")

    @patch.dict(os.environ, {'GENAIPLATFORM_FARM_SUBSCRIPTION_KEY': 'test-key'})
    @patch('vlan_AI_assistant.AzureOpenAI')
    def test_chat_api_exception(self, mock_openai):
        """Test chat method handles API exceptions gracefully."""
        # Setup mock client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
    
        # Create chatbot
        chatbot = VLANChatbot(self.detector)
    
        with patch.object(chatbot, '_build_network_context', return_value="Mock network context"):
            with patch.object(chatbot, '_build_system_prompt', return_value="Mock system prompt"):
                result = chatbot.chat("Test message")
            
                self.assertIn("I apologize, but I encountered an error: API Error", result)

    @patch.dict(os.environ, {'GENAIPLATFORM_FARM_SUBSCRIPTION_KEY': 'test-key'})
    @patch('vlan_AI_assistant.AzureOpenAI')
    def test_conversation_history_limit(self, mock_openai):
        """Test that conversation history is limited to 20 messages."""
        # Setup mock client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
    
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI response"
        mock_client.chat.completions.create.return_value = mock_response
    
        # Create chatbot
        chatbot = VLANChatbot(self.detector)
    
        with patch.object(chatbot, '_build_network_context', return_value="Mock network context"):
            with patch.object(chatbot, '_build_system_prompt', return_value="Mock system prompt"):
                # Add 25 messages (should trim to 20)
                for i in range(13):  # 13 * 2 = 26 messages total
                    chatbot.chat(f"Message {i}")
            
                self.assertEqual(len(chatbot.conversation_history), 20)
    
class TestIntegration(unittest.TestCase):
    """Integration tests for complete system functionality."""
    
    def setUp(self):
        """Set up integration test environment."""
        # Create a realistic test network with known island patterns
        self.realistic_network = {
            "devices": [
                {"id": "core-sw-01", "type": "switch", "role": "core", "location": "datacenter"},
                {"id": "core-sw-02", "type": "switch", "role": "core", "location": "datacenter"},
                {"id": "dist-sw-01", "type": "switch", "role": "distribution", "location": "building-a"},
                {"id": "acc-sw-01", "type": "switch", "role": "access", "location": "building-a-floor1"},
                {"id": "acc-sw-02", "type": "switch", "role": "access", "location": "building-a-floor2"},
                {"id": "ap-01", "type": "access_point", "role": "wireless", "location": "building-a-floor1"},
                {"id": "ap-02", "type": "access_point", "role": "wireless", "location": "building-a-floor2"},
                {"id": "camera-01", "type": "camera", "role": "security", "location": "building-a-floor1"}
            ],
            "links": [
                {"source": "core-sw-01", "target": "core-sw-02", "type": "ethernet", "speed": "10G"},
                {"source": "core-sw-01", "target": "dist-sw-01", "type": "ethernet", "speed": "10G"},
                {"source": "dist-sw-01", "target": "acc-sw-01", "type": "ethernet", "speed": "1G"},
                {"source": "acc-sw-01", "target": "ap-01", "type": "ethernet", "speed": "1G"},
                {"source": "acc-sw-01", "target": "camera-01", "type": "ethernet", "speed": "100M"},
                # Missing: acc-sw-02, ap-02 connections to create islands
            ],
            "vlans": [
                {
                    "id": 1,
                    "name": "Default",
                    "description": "Default management VLAN",
                    "devices": ["core-sw-01", "core-sw-02", "dist-sw-01", "acc-sw-01", "acc-sw-02"]
                },
                {
                    "id": 30,
                    "name": "WiFi-Corporate",
                    "description": "Corporate WiFi network",
                    "devices": ["core-sw-01", "core-sw-02", "ap-01", "ap-02"]
                },
                {
                    "id": 400,
                    "name": "Security-Cameras",
                    "description": "Security camera network",
                    "devices": ["core-sw-01", "dist-sw-01", "camera-01"]
                }
            ]
        }
        
        self.temp_dir = tempfile.mkdtemp()
        self.integration_file = os.path.join(self.temp_dir, "integration_network.json")
        
        with open(self.integration_file, 'w') as f:
            json.dump(self.realistic_network, f)
    
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_island_detection(self):
        """Test complete end-to-end island detection workflow."""
        # Initialize detector
        detector = VLANIslandDetector(self.integration_file)
        
        # Detect islands
        islands = detector.detect_islands()
        
        # Verify expected islands are detected
        self.assertGreater(len(islands), 0, "Should detect islands in test network")
        
        # Check Default VLAN has islands (acc-sw-02 isolated)
        self.assertIn(1, islands, "Default VLAN should have islands")
        
        # Check WiFi VLAN has islands (ap-02 isolated) 
        self.assertIn(30, islands, "WiFi VLAN should have islands")
        
        # Generate reports
        json_report = detector.generate_island_report()
        
        # Verify report completeness
        self.assertIn("vlans_with_islands", json_report)
    
    def test_realistic_network_patterns(self):
        """Test detection of realistic enterprise network patterns."""
        detector = VLANIslandDetector(self.integration_file)
        islands = detector.detect_islands()
        
        # Analyze detected patterns
        for vlan_id, vlan_islands in islands.items():
            vlan_info = detector.vlan_info[vlan_id]
            
            # Each VLAN should have meaningful island information
            self.assertGreater(len(vlan_islands), 0)
            
            for island in vlan_islands:
                # Each island should have at least one device
                self.assertGreater(len(island.devices), 0)
                
                # Island devices should be valid
                for device in island.devices:
                    self.assertIn(device, vlan_info['devices'])
    
    def test_performance_with_larger_network(self):
        """Test performance with a larger network simulation."""
        import time
        
        # Generate larger network
        large_network = self._generate_large_network(100)  # 100 devices
        
        large_file = os.path.join(self.temp_dir, "large_network.json")
        with open(large_file, 'w') as f:
            json.dump(large_network, f)
        
        # Measure detection time
        start_time = time.time()
        detector = VLANIslandDetector(large_file)
        islands = detector.detect_islands()
        detection_time = time.time() - start_time
        
        # Performance should be reasonable (< 5 seconds for 100 devices)
        self.assertLess(detection_time, 5.0, "Detection should complete within 5 seconds")
        
        # Should still detect islands correctly
        self.assertIsInstance(islands, dict)
    
    def _generate_large_network(self, num_devices):
        """Generate a large test network with predictable island patterns."""
        devices = []
        links = []
        vlans = []
        
        # Generate devices
        for i in range(num_devices):
            devices.append({
                "id": f"device-{i:03d}",
                "type": "switch",
                "role": "access" if i > 10 else "core"
            })
        
        # Generate links (create some gaps for islands)
        for i in range(0, num_devices - 1):
            if i % 10 != 7:  # Skip every 8th connection to create islands
                links.append({
                    "source": f"device-{i:03d}",
                    "target": f"device-{i+1:03d}",
                    "type": "ethernet"
                })
        
        # Generate VLANs with different device distributions
        for vlan_id in [100, 200, 300]:
            vlan_devices = [f"device-{i:03d}" for i in range(0, num_devices, 3)]  # Every 3rd device
            vlans.append({
                "id": vlan_id,
                "name": f"VLAN-{vlan_id}",
                "description": f"Test VLAN {vlan_id}",
                "devices": vlan_devices
            })
        
        return {
            "devices": devices,
            "links": links,
            "vlans": vlans
        }

def run_test_suite():
    """Run the complete test suite with detailed output."""
    print("="*70)
    print("VLAN ISLANDS DETECTION - TEST SUITE")
    print("="*70)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [TestVLANIslandDetector, TestVLANChatbot, TestIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")
    

if __name__ == "__main__":
    success = run_test_suite()
    exit(0 if success else 1)