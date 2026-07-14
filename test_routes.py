"""
Test script to verify routes are registered
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app.main import app

print("="*50)
print("🔍 Routes registered in the application")
print("="*50)

for route in app.routes:
    methods = route.methods if hasattr(route, 'methods') else 'N/A'
    path = route.path if hasattr(route, 'path') else str(route)
    print(f"  {methods} {path}")

print("="*50)
print(f"Total routes: {len(app.routes)}")