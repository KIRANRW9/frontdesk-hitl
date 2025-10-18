"""
Frontdesk AI Agent - With Knowledge Base Integration
"""

import requests
import time
from datetime import datetime

# Backend API URL
BACKEND_URL = "http://localhost:8000"

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def search_backend_knowledge(question):
    """Search backend knowledge base"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/knowledge",
            params={"query": question},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('found'):
                return data['entry']['answer']
        
        return None
    except Exception as e:
        print(f"Error checking knowledge base: {e}")
        return None

def create_help_request(question, caller_name, caller_phone):
    """Send help request to backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/requests",
            json={
                "question": question,
                "caller_name": caller_name,
                "caller_phone": caller_phone,
                "call_id": f"sim_{int(time.time())}"
            },
            timeout=5
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"\n✅ Help request created: {data['id']}")
            print(f"📱 Supervisor has been notified")
            return True
        else:
            print(f"\n❌ Failed to create request: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error creating help request: {e}")
        return False

def simulate_call():
    """Simulate a customer call"""
    print("\n" + "="*60)
    print("📞 NEW CALL RECEIVED")
    print("="*60)
    
    # Get caller info
    caller_name = input("Caller name: ").strip()
    if not caller_name:
        caller_name = "Anonymous Caller"
    
    caller_phone = input("Caller phone (e.g., +1-555-0100): ").strip()
    if not caller_phone:
        caller_phone = "+1-555-0100"
    
    print(f"\n🤖 AI Agent: Hello {caller_name}! Thank you for calling Glamour Salon & Spa. How can I help you today?")
    
    # Question loop
    while True:
        print("\n" + "-"*60)
        question = input(f"{caller_name}: ").strip()
        
        if not question:
            continue
            
        if question.lower() in ['bye', 'goodbye', 'exit', 'end', 'quit']:
            print(f"\n🤖 AI Agent: Thank you for calling! Have a great day!")
            break
        
        # FIRST: Check backend knowledge base
        print("🔍 Checking knowledge base...")
        answer = search_backend_knowledge(question)
        
        if answer:
            print(f"✅ Found in knowledge base!")
            print(f"\n🤖 AI Agent: {answer}")
        else:
            print("❌ Not found in knowledge base - escalating to supervisor")
            print(f"\n🤖 AI Agent: That's a great question! Let me check with my supervisor and I'll get back to you shortly.")
            
            # Create help request
            if check_backend():
                success = create_help_request(question, caller_name, caller_phone)
                if success:
                    print(f"🤖 AI Agent: We'll text you at {caller_phone} with the answer within the hour. Is there anything else I can help with?")
            else:
                print("⚠️  Backend is not running. Start the backend first!")
                print("🤖 AI Agent: I apologize, I'm having technical difficulties. Could you please call back in a few minutes?")

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🏢 FRONTDESK AI AGENT - WITH KNOWLEDGE BASE")
    print("="*60)
    
    # Check backend connection
    if check_backend():
        print("✅ Backend connected: http://localhost:8000")
        
        # Get knowledge base count
        try:
            response = requests.get(f"{BACKEND_URL}/api/knowledge", timeout=3)
            if response.status_code == 200:
                data = response.json()
                kb_count = len(data.get('entries', []))
                print(f"📚 Knowledge base has {kb_count} entries")
        except:
            pass
    else:
        print("⚠️  Backend NOT running!")
        print("   Start backend first: cd backend && python app.py")
    
    print("\nType 'bye' to end a call")
    print("Type 'new' to start a new call")
    print("Type 'exit' to quit the agent")
    print("="*60)
    
    while True:
        print("\n")
        choice = input("Enter 'new' for new call, or 'exit' to quit: ").strip().lower()
        
        if choice == 'exit':
            print("\n👋 Agent shutting down...")
            break
        elif choice == 'new':
            simulate_call()
        else:
            print("Invalid option. Type 'new' or 'exit'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
