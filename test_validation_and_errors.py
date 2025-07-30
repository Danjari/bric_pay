#!/usr/bin/env python3
"""
Comprehensive Test Script for Task 6: Input Validation and Error Handling
Tests all validation rules, error handling, and edge cases
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v1"

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")
    print()

def test_health_check():
    """Test basic health check"""
    print("Testing Health Check...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200
        print_test_result("Health Check", success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_test_result("Health Check", False, f"Error: {e}")
        return False

def test_validation_rules():
    """Test validation rules endpoint"""
    print("Testing Validation Rules...")
    
    try:
        response = requests.get(f"{API_BASE}/validation-rules")
        success = response.status_code == 200
        
        if success:
            data = response.json()
            rules = data.get('validation_rules', {})
            rule_count = len(rules)
            print_test_result("Validation Rules", success, f"Retrieved {rule_count} rule sets")
        else:
            print_test_result("Validation Rules", success, f"Status: {response.status_code}")
        
        return success
    except Exception as e:
        print_test_result("Validation Rules", False, f"Error: {e}")
        return False

def test_phone_validation():
    """Test phone number validation"""
    print("Testing Phone Number Validation...")
    
    test_cases = [
        {"phone": "+1234567890", "expected": True, "description": "Valid US number"},
        {"phone": "+44123456789", "expected": True, "description": "Valid UK number"},
        {"phone": "1234567890", "expected": False, "description": "Missing country code"},
        {"phone": "+123456789", "expected": False, "description": "Too short"},
        {"phone": "+123456789012345", "expected": False, "description": "Too long"},
        {"phone": "+0000000000", "expected": False, "description": "All zeros"},
        {"phone": "+1111111111", "expected": False, "description": "All ones"},
        {"phone": "+1abc123456", "expected": False, "description": "Contains letters"},
        {"phone": "", "expected": False, "description": "Empty string"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/validate-phone",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"phone": test_case["phone"]})
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get('is_valid', False)
                success = is_valid == test_case["expected"]
                
                if success:
                    success_count += 1
                else:
                    print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {is_valid}")
            else:
                print(f"   ❌ {test_case['description']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Phone Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_password_validation():
    """Test password strength validation"""
    print("Testing Password Validation...")
    
    test_cases = [
        {"password": "SecurePass123!", "expected": True, "description": "Strong password"},
        {"password": "weak", "expected": False, "description": "Too short"},
        {"password": "nouppercase123!", "expected": False, "description": "No uppercase"},
        {"password": "NOLOWERCASE123!", "expected": False, "description": "No lowercase"},
        {"password": "NoDigits!", "expected": False, "description": "No digits"},
        {"password": "NoSpecial123", "expected": False, "description": "No special chars"},
        {"password": "password123!", "expected": False, "description": "Common word"},
        {"password": "123456789!", "expected": False, "description": "Sequential numbers"},
        {"password": "MySecurePass123!", "expected": True, "description": "Very strong password"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/validate-password",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"password": test_case["password"]})
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get('is_valid', False)
                success = is_valid == test_case["expected"]
                
                if success:
                    success_count += 1
                else:
                    print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {is_valid}")
            else:
                print(f"   ❌ {test_case['description']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Password Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_account_validation():
    """Test account number validation"""
    print("Testing Account Number Validation...")
    
    test_cases = [
        {"account_number": "1234567890", "expected": True, "description": "Valid 10-digit"},
        {"account_number": "12345678", "expected": True, "description": "Valid 8-digit"},
        {"account_number": "123456789012", "expected": True, "description": "Valid 12-digit"},
        {"account_number": "0123456789", "expected": False, "description": "Leading zero"},
        {"account_number": "1234567", "expected": False, "description": "Too short"},
        {"account_number": "1234567890123", "expected": False, "description": "Too long"},
        {"account_number": "123456789a", "expected": False, "description": "Contains letters"},
        {"account_number": "", "expected": False, "description": "Empty string"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/validate-account",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"account_number": test_case["account_number"]})
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get('is_valid', False)
                success = is_valid == test_case["expected"]
                
                if success:
                    success_count += 1
                else:
                    print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {is_valid}")
            else:
                print(f"   ❌ {test_case['description']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Account Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_amount_validation():
    """Test amount validation"""
    print("Testing Amount Validation...")
    
    test_cases = [
        {"amount": 100.50, "expected": True, "description": "Valid amount"},
        {"amount": 0.01, "expected": True, "description": "Minimum amount"},
        {"amount": 1000000, "expected": True, "description": "Maximum amount"},
        {"amount": 0, "expected": False, "description": "Zero amount"},
        {"amount": -100, "expected": False, "description": "Negative amount"},
        {"amount": 1000001, "expected": False, "description": "Above maximum"},
        {"amount": 0.001, "expected": False, "description": "Below minimum"},
        {"amount": "invalid", "expected": False, "description": "Invalid string"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/validate-amount",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"amount": test_case["amount"]})
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get('is_valid', False)
                success = is_valid == test_case["expected"]
                
                if success:
                    success_count += 1
                else:
                    print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {is_valid}")
            else:
                print(f"   ❌ {test_case['description']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Amount Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_field_validation():
    """Test generic field validation"""
    print("Testing Generic Field Validation...")
    
    test_cases = [
        {"field_name": "phone", "value": "+1234567890", "expected": True, "description": "Phone field"},
        {"field_name": "password", "value": "SecurePass123!", "expected": True, "description": "Password field"},
        {"field_name": "account_number", "value": "1234567890", "expected": True, "description": "Account field"},
        {"field_name": "name", "value": "John Doe", "expected": True, "description": "Name field"},
        {"field_name": "amount", "value": "100.50", "expected": True, "description": "Amount field"},
        {"field_name": "unknown", "value": "test", "expected": True, "description": "Unknown field"},
        {"field_name": "test", "value": "", "expected": False, "description": "Empty value"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/validate-field",
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "field_name": test_case["field_name"],
                    "value": test_case["value"]
                })
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get('is_valid', False)
                success = is_valid == test_case["expected"]
                
                if success:
                    success_count += 1
                else:
                    print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {is_valid}")
            else:
                print(f"   ❌ {test_case['description']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Field Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_account_creation_validation():
    """Test account creation with various validation scenarios"""
    print("Testing Account Creation Validation...")
    
    test_cases = [
        {
            "data": {
                "name": "John",
                "surname": "Doe",
                "phone": "+1234567890",
                "password": "SecurePass123!",
                "date_of_birth": "1990-01-01",
                "place_of_birth": "New York"
            },
            "expected": 201,
            "description": "Valid account creation"
        },
        {
            "data": {
                "name": "J",
                "surname": "Doe",
                "phone": "+1234567890",
                "password": "SecurePass123!",
                "date_of_birth": "1990-01-01",
                "place_of_birth": "New York"
            },
            "expected": 400,
            "description": "Name too short"
        },
        {
            "data": {
                "name": "John",
                "surname": "Doe",
                "phone": "1234567890",
                "password": "SecurePass123!",
                "date_of_birth": "1990-01-01",
                "place_of_birth": "New York"
            },
            "expected": 400,
            "description": "Invalid phone format"
        },
        {
            "data": {
                "name": "John",
                "surname": "Doe",
                "phone": "+1234567890",
                "password": "weak",
                "date_of_birth": "1990-01-01",
                "place_of_birth": "New York"
            },
            "expected": 400,
            "description": "Weak password"
        },
        {
            "data": {
                "name": "John",
                "surname": "Doe",
                "phone": "+1234567890",
                "password": "SecurePass123!",
                "date_of_birth": "2030-01-01",
                "place_of_birth": "New York"
            },
            "expected": 400,
            "description": "Future date of birth"
        },
        {
            "data": {
                "name": "John",
                "surname": "Doe",
                "phone": "+1234567890",
                "password": "SecurePass123!",
                "date_of_birth": "2010-01-01",
                "place_of_birth": "New York"
            },
            "expected": 400,
            "description": "Under 18 years old"
        },
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases):
        try:
            # Add timestamp to phone to avoid conflicts
            import time
            test_data = test_case["data"].copy()
            test_data["phone"] = f"{test_data['phone']}_{int(time.time() * 1000) % 10000}"
            
            response = requests.post(
                f"{API_BASE}/create-account",
                headers={"Content-Type": "application/json"},
                data=json.dumps(test_data)
            )
            
            success = response.status_code == test_case["expected"]
            
            if success:
                success_count += 1
            else:
                print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {response.status_code}")
                if response.status_code != test_case["expected"]:
                    try:
                        error_data = response.json()
                        print(f"      Error: {error_data.get('error', 'Unknown error')}")
                    except:
                        pass
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Account Creation Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_deposit_validation():
    """Test deposit validation"""
    print("Testing Deposit Validation...")
    
    # First create a test account
    test_account = None
    try:
        account_data = {
            "name": "Test",
            "surname": "User",
            "phone": f"+1234567890_{int(time.time() * 1000) % 10000}",
            "password": "SecurePass123!",
            "date_of_birth": "1990-01-01",
            "place_of_birth": "Test City"
        }
        
        response = requests.post(
            f"{API_BASE}/create-account",
            headers={"Content-Type": "application/json"},
            data=json.dumps(account_data)
        )
        
        if response.status_code == 201:
            account_info = response.json()
            test_account = account_info.get('account_number')
            print(f"   Created test account: {test_account}")
        else:
            print("   Failed to create test account")
            return False
            
    except Exception as e:
        print(f"   Error creating test account: {e}")
        return False
    
    if not test_account:
        print("   No test account available")
        return False
    
    test_cases = [
        {"account_number": test_account, "amount": 100.50, "expected": 200, "description": "Valid deposit"},
        {"account_number": "9999999999", "amount": 100.50, "expected": 404, "description": "Non-existent account"},
        {"account_number": test_account, "amount": 0, "expected": 400, "description": "Zero amount"},
        {"account_number": test_account, "amount": -100, "expected": 400, "description": "Negative amount"},
        {"account_number": test_account, "amount": 1000001, "expected": 400, "description": "Above maximum"},
        {"account_number": test_account, "amount": 0.001, "expected": 400, "description": "Below minimum"},
        {"account_number": "invalid", "amount": 100, "expected": 400, "description": "Invalid account number"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/deposit",
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "account_number": test_case["account_number"],
                    "amount": test_case["amount"]
                })
            )
            
            success = response.status_code == test_case["expected"]
            
            if success:
                success_count += 1
            else:
                print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Deposit Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_transfer_validation():
    """Test transfer validation"""
    print("Testing Transfer Validation...")
    
    # Create two test accounts
    test_accounts = []
    try:
        for i in range(2):
            account_data = {
                "name": f"Test{i}",
                "surname": "User",
                "phone": f"+123456789{i}_{int(time.time() * 1000) % 10000}",
                "password": "SecurePass123!",
                "date_of_birth": "1990-01-01",
                "place_of_birth": "Test City"
            }
            
            response = requests.post(
                f"{API_BASE}/create-account",
                headers={"Content-Type": "application/json"},
                data=json.dumps(account_data)
            )
            
            if response.status_code == 201:
                account_info = response.json()
                test_accounts.append(account_info.get('account_number'))
                print(f"   Created test account {i+1}: {test_accounts[-1]}")
            else:
                print(f"   Failed to create test account {i+1}")
                return False
                
    except Exception as e:
        print(f"   Error creating test accounts: {e}")
        return False
    
    if len(test_accounts) != 2:
        print("   Not enough test accounts available")
        return False
    
    # Deposit some funds to the first account
    try:
        response = requests.post(
            f"{API_BASE}/deposit",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "account_number": test_accounts[0],
                "amount": 1000.00
            })
        )
        
        if response.status_code != 200:
            print("   Failed to deposit funds to test account")
            return False
            
    except Exception as e:
        print(f"   Error depositing funds: {e}")
        return False
    
    test_cases = [
        {"from_account": test_accounts[0], "to_account": test_accounts[1], "amount": 100.50, "expected": 200, "description": "Valid transfer"},
        {"from_account": "9999999999", "to_account": test_accounts[1], "amount": 100.50, "expected": 400, "description": "Non-existent source account"},
        {"from_account": test_accounts[0], "to_account": "9999999999", "amount": 100.50, "expected": 400, "description": "Non-existent destination account"},
        {"from_account": test_accounts[0], "to_account": test_accounts[1], "amount": 0, "expected": 400, "description": "Zero amount"},
        {"from_account": test_accounts[0], "to_account": test_accounts[1], "amount": -100, "expected": 400, "description": "Negative amount"},
        {"from_account": test_accounts[0], "to_account": test_accounts[1], "amount": 1000001, "expected": 400, "description": "Above maximum"},
        {"from_account": test_accounts[0], "to_account": test_accounts[1], "amount": 0.001, "expected": 400, "description": "Below minimum"},
        {"from_account": test_accounts[0], "to_account": test_accounts[0], "amount": 100, "expected": 400, "description": "Same account transfer"},
        {"from_account": test_accounts[0], "to_account": test_accounts[1], "amount": 2000, "expected": 400, "description": "Insufficient balance"},
        {"from_account": "invalid", "to_account": test_accounts[1], "amount": 100, "expected": 400, "description": "Invalid source account"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/transfer",
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "from_account": test_case["from_account"],
                    "to_account": test_case["to_account"],
                    "amount": test_case["amount"]
                })
            )
            
            success = response.status_code == test_case["expected"]
            
            if success:
                success_count += 1
            else:
                print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Transfer Validation", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_error_handling():
    """Test error handling scenarios"""
    print("Testing Error Handling...")
    
    test_cases = [
        {"endpoint": "/create-account", "method": "POST", "data": None, "expected": 400, "description": "Missing request body"},
        {"endpoint": "/create-account", "method": "POST", "data": {}, "expected": 400, "description": "Empty request body"},
        {"endpoint": "/deposit", "method": "POST", "data": None, "expected": 400, "description": "Missing deposit data"},
        {"endpoint": "/transfer", "method": "POST", "data": None, "expected": 400, "description": "Missing transfer data"},
        {"endpoint": "/validate-phone", "method": "POST", "data": None, "expected": 400, "description": "Missing phone data"},
        {"endpoint": "/validate-password", "method": "POST", "data": None, "expected": 400, "description": "Missing password data"},
        {"endpoint": "/validate-account", "method": "POST", "data": None, "expected": 400, "description": "Missing account data"},
        {"endpoint": "/validate-amount", "method": "POST", "data": None, "expected": 400, "description": "Missing amount data"},
        {"endpoint": "/validate-field", "method": "POST", "data": None, "expected": 400, "description": "Missing field data"},
        {"endpoint": "/account/9999999999", "method": "GET", "data": None, "expected": 400, "description": "Non-existent account"},
        {"endpoint": "/account/9999999999/balance", "method": "GET", "data": None, "expected": 400, "description": "Non-existent account balance"},
        {"endpoint": "/account/9999999999/transactions", "method": "GET", "data": None, "expected": 400, "description": "Non-existent account transactions"},
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        try:
            if test_case["method"] == "POST":
                response = requests.post(
                    f"{API_BASE}{test_case['endpoint']}",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(test_case["data"]) if test_case["data"] is not None else None
                )
            else:
                response = requests.get(f"{API_BASE}{test_case['endpoint']}")
            
            success = response.status_code == test_case["expected"]
            
            if success:
                success_count += 1
            else:
                print(f"   ❌ {test_case['description']}: Expected {test_case['expected']}, got {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['description']}: Error {e}")
    
    print_test_result("Error Handling", success_count == len(test_cases), f"{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def main():
    """Run all validation and error handling tests"""
    print("=" * 60)
    print("TASK 6: INPUT VALIDATION AND ERROR HANDLING TESTS")
    print("=" * 60)
    print()
    
    # Test results tracking
    test_results = []
    
    # Run all tests
    tests = [
        ("Health Check", test_health_check),
        ("Validation Rules", test_validation_rules),
        ("Phone Validation", test_phone_validation),
        ("Password Validation", test_password_validation),
        ("Account Validation", test_account_validation),
        ("Amount Validation", test_amount_validation),
        ("Field Validation", test_field_validation),
        ("Account Creation Validation", test_account_creation_validation),
        ("Deposit Validation", test_deposit_validation),
        ("Transfer Validation", test_transfer_validation),
        ("Error Handling", test_error_handling),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Test failed with exception: {e}")
            test_results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation and error handling tests passed!")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 