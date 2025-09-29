from vlan_AI_assistant import VLANIslandDetector, VLANChatbot
import os

def console_chat_interface():
    """Simple console-based conversational interface."""
    try:
        # Initialize detector
        print("🔧 Initializing VLAN Island Detector...")
        detector = VLANIslandDetector('vlan_islands_data.json')
        
        # Initialize chatbot
        print("🤖 Initializing AI Assistant...")
        chatbot = VLANChatbot(detector)
        
        # Welcome message
        print("\n" + "="*60)
        print("🌐 VLAN ISLANDS AI ASSISTANT")
        print("="*60)
        print("Hello! I'm your AI network assistant specialized in VLAN troubleshooting.")
        print("I've analyzed your network and detected several VLAN islands.")
        print("\nYou can ask me questions like:")
        print("• 'What VLAN islands were detected?'")
        print("• 'How can I fix the WiFi VLANs?'")
        print("• 'Show me Cisco commands for VLAN 30'")
        print("• 'What are the most critical issues?'")
        print("\nType 'help' for more options or 'exit' to quit.")
        print("-" * 60)
        
        # Chat loop
        while True:
            try:
                # Get user input
                user_input = input("\n🤔 You: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye! Good luck with your network troubleshooting!")
                    break
                
                elif user_input.lower() == 'help':
                    print_help_menu()
                    continue
                
                elif user_input.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                
                elif user_input.lower() == 'report':
                    show_quick_report(detector)
                    continue
                
                elif user_input == '':
                    print("Please enter a question or type 'help' for assistance.")
                    continue
                
                # Process with AI chatbot
                print("🤖 AI Assistant: ", end="", flush=True)
                response = chatbot.chat(user_input)
                
                # Print response with typing effect (optional)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error processing your request: {e}")
                print("Please try rephrasing your question.")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("\nPlease check:")
        print("1. network.json file exists")
        print("2. OPENAI_API_KEY environment variable is set")
        print("3. All required packages are installed")

def print_help_menu():
    """Print help menu with available commands."""
    print("\n📚 HELP MENU")
    print("-" * 40)
    print("COMMANDS:")
    print("• help     - Show this menu")
    print("• report   - Show quick VLAN summary")
    print("• clear    - Clear screen")
    print("• exit     - Quit the assistant")
    print("\nSAMPLE QUESTIONS:")
    print("• What VLAN islands were detected?")
    print("• How critical are the WiFi VLAN issues?")
    print("• Show me commands to fix VLAN 30")
    print("• What's wrong with the security cameras?")
    print("• How do I resolve the Default VLAN islands?")
    print("• Explain the network topology issues")
    print("• What should I prioritize first?")

def show_quick_report(detector):
    """Show a quick summary of detected issues."""
    report = detector.generate_island_report()
    print("\n📊 QUICK VLAN ISLANDS SUMMARY")
    print("-" * 40)
    
    if report['vlans_with_islands']:
        for vlan in report['vlans_with_islands']:
            status = "🔴 CRITICAL" if vlan['number_of_islands'] >= 10 else "🟡 MODERATE"
            print(f"{status} VLAN {vlan['vlan_id']} ({vlan['vlan_name']}): {vlan['number_of_islands']} islands")
    else:
        print("✅ No VLAN islands detected!")

if __name__ == "__main__":
    console_chat_interface()