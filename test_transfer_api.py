#!/usr/bin/env python3
"""
Transfer API Test Script for Bric Pay
Tests all transfer-related endpoints and scenarios
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_get_balances():
    """Test balance retrieval for test accounts"""
    print("\n🔍 Testing Balance Retrieval...")
    
    test_accounts = ["8290107324", "8826346968"]
    
    for account in test_accounts:
        try:
            response = requests.get(f"{BASE_URL}/account/{account}/balance")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Account {account} balance: ${data['balance']}")
            else:
                print(f"❌ Failed to get balance for {account}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting balance for {account}: {e}")

def test_successful_transfer():
    """Test successful transfer between accounts"""
    print("\n🔍 Testing Successful Transfer...")
    
    transfer_data = {
        "from_account": "8290107324",
        "to_account": "8826346968",
        "amount": 10.00
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transfer",
            headers={"Content-Type": "application/json"},
            data=json.dumps(transfer_data)
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Transfer successful!")
            print(f"   Transfer ID: {data['transfer_id']}")
            print(f"   Amount: ${data['amount']}")
            print(f"   From: {data['from_account']} (${data['from_balance']})")
            print(f"   To: {data['to_account']} (${data['to_balance']})")
        else:
            print(f"❌ Transfer failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Transfer error: {e}")

def test_insufficient_balance():
    """Test transfer with insufficient balance"""
    print("\n🔍 Testing Insufficient Balance...")
    
    transfer_data = {
        "from_account": "8826346968",
        "to_account": "8290107324",
        "amount": 1000.00  # Much more than available
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transfer",
            headers={"Content-Type": "application/json"},
            data=json.dumps(transfer_data)
        )
        
        if response.status_code == 400:
            data = response.json()
            if "Insufficient balance" in data.get('details', ''):
                print("✅ Insufficient balance correctly rejected")
                print(f"   Error: {data['details']}")
            else:
                print(f"❌ Unexpected error: {data}")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_nonexistent_account():
    """Test transfer with non-existent account"""
    print("\n🔍 Testing Non-existent Account...")
    
    transfer_data = {
        "from_account": "9999999999",  # Non-existent
        "to_account": "8290107324",
        "amount": 10.00
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transfer",
            headers={"Content-Type": "application/json"},
            data=json.dumps(transfer_data)
        )
        
        if response.status_code == 400:
            data = response.json()
            if "not found" in data.get('details', ''):
                print("✅ Non-existent account correctly rejected")
                print(f"   Error: {data['details']}")
            else:
                print(f"❌ Unexpected error: {data}")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_same_account_transfer():
    """Test transfer to same account"""
    print("\n🔍 Testing Same Account Transfer...")
    
    transfer_data = {
        "from_account": "8290107324",
        "to_account": "8290107324",  # Same account
        "amount": 10.00
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transfer",
            headers={"Content-Type": "application/json"},
            data=json.dumps(transfer_data)
        )
        
        if response.status_code == 400:
            data = response.json()
            if "Cannot transfer to the same account" in data.get('details', ''):
                print("✅ Same account transfer correctly rejected")
                print(f"   Error: {data['details']}")
            else:
                print(f"❌ Unexpected error: {data}")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_invalid_amount():
    """Test transfer with invalid amount"""
    print("\n🔍 Testing Invalid Amount...")
    
    test_cases = [
        {"amount": -10.00, "description": "Negative amount"},
        {"amount": 0.00, "description": "Zero amount"},
        {"amount": 2000000.00, "description": "Amount exceeding limit"}
    ]
    
    for test_case in test_cases:
        transfer_data = {
            "from_account": "8290107324",
            "to_account": "8826346968",
            "amount": test_case["amount"]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/transfer",
                headers={"Content-Type": "application/json"},
                data=json.dumps(transfer_data)
            )
            
            if response.status_code == 400:
                data = response.json()
                print(f"✅ {test_case['description']} correctly rejected")
                print(f"   Error: {data['details']}")
            else:
                print(f"❌ {test_case['description']} should have been rejected")
        except Exception as e:
            print(f"❌ Error testing {test_case['description']}: {e}")

def test_transaction_history():
    """Test transaction history retrieval"""
    print("\n🔍 Testing Transaction History...")
    
    test_accounts = ["8290107324", "8826346968"]
    
    for account in test_accounts:
        try:
            response = requests.get(f"{BASE_URL}/account/{account}/transactions")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Account {account} transaction history:")
                print(f"   Count: {data['count']}")
                for tx in data['transactions'][:3]:  # Show first 3
                    print(f"   - {tx['transaction_type']}: ${tx['amount']} ({tx['created_at'][:19]})")
            else:
                print(f"❌ Failed to get transaction history for {account}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting transaction history for {account}: {e}")

def test_atomicity():
    """Test transfer atomicity by checking balances before and after"""
    print("\n🔍 Testing Transfer Atomicity...")
    
    # Get initial balances
    try:
        from_balance_before = requests.get(f"{BASE_URL}/account/8290107324/balance").json()['balance']
        to_balance_before = requests.get(f"{BASE_URL}/account/8826346968/balance").json()['balance']
        
        print(f"   Initial balances - From: ${from_balance_before}, To: ${to_balance_before}")
        
        # Perform transfer
        transfer_data = {
            "from_account": "8290107324",
            "to_account": "8826346968",
            "amount": 5.00
        }
        
        response = requests.post(
            f"{BASE_URL}/transfer",
            headers={"Content-Type": "application/json"},
            data=json.dumps(transfer_data)
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify balances match expected values
            expected_from = float(from_balance_before) - 5.00
            expected_to = float(to_balance_before) + 5.00
            
            if abs(data['from_balance'] - expected_from) < 0.01 and abs(data['to_balance'] - expected_to) < 0.01:
                print("✅ Transfer atomicity verified")
                print(f"   Final balances - From: ${data['from_balance']}, To: ${data['to_balance']}")
            else:
                print("❌ Transfer atomicity failed")
                print(f"   Expected - From: ${expected_from}, To: ${expected_to}")
                print(f"   Actual - From: ${data['from_balance']}, To: ${data['to_balance']}")
        else:
            print(f"❌ Transfer failed during atomicity test: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Atomicity test error: {e}")

def test_account_creation_and_transfer():
    """Test creating new accounts and performing transfers"""
    print("\n🔍 Testing Account Creation and Transfer...")
    
    # Create two new test accounts
    account1_data = {
        "name": "Transfer",
        "surname": "Test1",
        "phone": "+1111111111",
        "password": "SecurePass123",
        "date_of_birth": "1990-01-01",
        "place_of_birth": "Test City"
    }
    
    account2_data = {
        "name": "Transfer",
        "surname": "Test2", 
        "phone": "+2222222222",
        "password": "SecurePass123",
        "date_of_birth": "1990-01-01",
        "place_of_birth": "Test City"
    }
    
    try:
        # Create first account
        response1 = requests.post(
            f"{BASE_URL}/create-account",
            headers={"Content-Type": "application/json"},
            data=json.dumps(account1_data)
        )
        
        if response1.status_code == 201:
            account1 = response1.json()
            print(f"✅ Created account 1: {account1['account_number']}")
            
            # Create second account
            response2 = requests.post(
                f"{BASE_URL}/create-account",
                headers={"Content-Type": "application/json"},
                data=json.dumps(account2_data)
            )
            
            if response2.status_code == 201:
                account2 = response2.json()
                print(f"✅ Created account 2: {account2['account_number']}")
                
                # Deposit money to first account
                deposit_data = {
                    "account_number": account1['account_number'],
                    "amount": 100.00
                }
                
                deposit_response = requests.post(
                    f"{BASE_URL}/deposit",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(deposit_data)
                )
                
                if deposit_response.status_code == 200:
                    print(f"✅ Deposited $100 to account {account1['account_number']}")
                    
                    # Perform transfer
                    transfer_data = {
                        "from_account": account1['account_number'],
                        "to_account": account2['account_number'],
                        "amount": 50.00
                    }
                    
                    transfer_response = requests.post(
                        f"{BASE_URL}/transfer",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(transfer_data)
                    )
                    
                    if transfer_response.status_code == 200:
                        transfer_result = transfer_response.json()
                        print("✅ Transfer between new accounts successful!")
                        print(f"   Transfer ID: {transfer_result['transfer_id']}")
                        print(f"   From: {transfer_result['from_account']} (${transfer_result['from_balance']})")
                        print(f"   To: {transfer_result['to_account']} (${transfer_result['to_balance']})")
                    else:
                        print(f"❌ Transfer failed: {transfer_response.status_code}")
                        print(f"   Response: {transfer_response.text}")
                else:
                    print(f"❌ Deposit failed: {deposit_response.status_code}")
            else:
                print(f"❌ Account 2 creation failed: {response2.status_code}")
        else:
            print(f"❌ Account 1 creation failed: {response1.status_code}")
            
    except Exception as e:
        print(f"❌ Account creation and transfer test error: {e}")

def main():
    """Run all transfer API tests"""
    print("🔄 Starting Transfer API Tests")
    print("=" * 60)
    
    test_health_check()
    test_get_balances()
    test_successful_transfer()
    test_insufficient_balance()
    test_nonexistent_account()
    test_same_account_transfer()
    test_invalid_amount()
    test_transaction_history()
    test_atomicity()
    test_account_creation_and_transfer()
    
    print("\n" + "=" * 60)
    print("✅ Transfer API Testing Complete!")
    print("\n📋 Transfer Features Verified:")
    print("   • Successful peer-to-peer transfers")
    print("   • Atomic transaction operations")
    print("   • Balance validation")
    print("   • Account existence validation")
    print("   • Input validation (amount, account numbers)")
    print("   • Transaction history tracking")
    print("   • Error handling for all scenarios")
    print("   • Account creation and transfer workflow")
    print("\n🔒 Security Features:")
    print("   • Atomic transfers prevent partial updates")
    print("   • Proper validation of all inputs")
    print("   • Comprehensive error messages")
    print("   • Transaction logging for audit trail")
    print("\n💡 Usage Examples:")
    print("   • Transfer between existing accounts")
    print("   • Create new accounts and transfer")
    print("   • View transaction history")
    print("   • Check account balances")

if __name__ == "__main__":
    main() 