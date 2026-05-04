#!/usr/bin/env python
"""
MikroTik Connection Test Script
Run: python test_mikrotik.py <host> <user> <password> [port]
"""
import sys
from librouteros import connect
import ssl

def test_connection(host, user, password, port=8728, use_ssl=False):
    print(f"\n{'='*60}")
    print(f"Testing MikroTik Connection")
    print(f"{'='*60}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password)}")
    print(f"SSL: {use_ssl}")
    print(f"{'='*60}\n")
    
    # Test 1: TCP connection (like telnet)
    import socket
    print("1. Testing TCP connection (telnet-style)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print("   ✓ TCP connection successful")
        else:
            print(f"   ✗ TCP connection failed (code: {result})")
            return False
    except Exception as e:
        print(f"   ✗ TCP error: {e}")
        return False
    
    # Test 2: MikroTik API (no SSL)
    print("\n2. Testing MikroTik API (no SSL)...")
    try:
        conn = connect(host=host, port=port, username=user, password=password)
        print("   ✓ API connection successful!")
        
        # Try to get something
        try:
            users = conn.path('ip', 'hotspot', 'user')
            user_list = list(users)
            print(f"   ✓ Found {len(user_list)} hotspot users")
        except Exception as e:
            print(f"   ⚠ Connection OK, but API query failed: {e}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"   ✗ API error: {type(e).__name__}: {e}")
    
    # Test 3: MikroTik API (with SSL, port 8729)
    if port != 8729:
        print("\n3. Testing MikroTik API (SSL on port 8729)...")
        try:
            conn = connect(
                host=host, 
                port=8729, 
                username=user, 
                password=password,
                ssl_wrapper=ssl.create_default_context
            )
            print("   ✓ SSL API connection successful!")
            conn.close()
            return True
        except Exception as e:
            print(f"   ✗ SSL API error: {type(e).__name__}: {e}")
    
    return False

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python test_mikrotik.py <host> <user> <password> [port]")
        print("Example: python test_mikrotik.py 10.10.12.1 apiuser apipass 8728")
        sys.exit(1)
    
    host = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
    port = int(sys.argv[4]) if len(sys.argv) > 4 else 8728
    
    success = test_connection(host, user, password, port)
    print(f"\n{'='*60}")
    print(f"Result: {'✓ SUCCESS' if success else '✗ FAILED'}")
    print(f"{'='*60}\n")
