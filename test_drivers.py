#!/usr/bin/env python3
"""
Test script for data source drivers.
Tests the Wayback Machine driver (FREE, no API key needed).
"""
import asyncio
import sys
from pathlib import Path

# Add sbv-pipeline to path
sys.path.insert(0, str(Path(__file__).parent / "sbv-pipeline"))

from src.drivers import DriverManager
from src.config import settings


async def test_wayback():
    """Test Wayback Machine driver."""
    print("=" * 70)
    print("🧪 Testing Wayback Machine Driver (FREE)")
    print("=" * 70)
    print()
    
    # Initialize driver manager
    config = settings.get_driver_config()
    manager = DriverManager(config=config)
    
    # Show available drivers
    print("📋 Available Drivers:")
    for driver in manager.list_drivers():
        status_icon = "✅" if driver['is_enabled'] else "⏸️"
        key_icon = "🔑" if driver['requires_api_key'] and not driver['has_api_key'] else ""
        print(f"   {status_icon} {driver['display_name']}: {driver['status']} {key_icon}")
    print()
    
    # Test companies
    test_companies = [
        {"name": "Intel Corp", "homepage": "https://www.intel.com"},
        {"name": "Tesla", "homepage": "https://www.tesla.com"},
        {"name": "OpenAI", "homepage": "https://openai.com"}
    ]
    
    for company in test_companies:
        print(f"🔍 Analyzing: {company['name']}")
        print(f"   Homepage: {company['homepage']}")
        print()
        
        try:
            # Run Wayback driver
            result = await manager.run_single(
                driver_name="wayback",
                company_name=company['name'],
                homepage=company['homepage']
            )
            
            if result.status.value == "completed":
                data = result.data
                print(f"   ✅ Success!")
                print(f"   📊 Results:")
                print(f"      • Available in archive: {data.get('available', False)}")
                if data.get('available'):
                    print(f"      • Total snapshots: {data.get('total_snapshots', 0)}")
                    print(f"      • Company age: {data.get('company_age_years', 'N/A')} years")
                    print(f"      • First snapshot: {data.get('first_snapshot', {}).get('date', 'N/A')}")
                    print(f"      • Latest snapshot: {data.get('latest_snapshot', {}).get('date', 'N/A')}")
                    if data.get('first_snapshot_url'):
                        print(f"      • View oldest: {data['first_snapshot_url']}")
                else:
                    print(f"      • Message: {data.get('message', 'Not found')}")
                print(f"   ⏱️  Duration: {result.duration_seconds:.2f}s")
            elif result.status.value == "missing_api_key":
                print(f"   🔑 Skipped: {result.error}")
            elif result.status.value == "disabled":
                print(f"   ⏸️  Disabled")
            else:
                print(f"   ❌ Failed: {result.error}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    print("=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)


async def test_all_drivers():
    """Test all enabled drivers in parallel."""
    print("=" * 70)
    print("🧪 Testing ALL Enabled Drivers (Parallel)")
    print("=" * 70)
    print()
    
    config = settings.get_driver_config()
    manager = DriverManager(config=config)
    
    company_name = "Tesla"
    homepage = "https://www.tesla.com"
    
    print(f"🔍 Analyzing: {company_name}")
    print(f"   Running all enabled drivers in parallel...")
    print()
    
    # Run all enabled drivers
    results = await manager.run_all(company_name, homepage)
    
    print(f"📊 Results from {len(results)} sources:")
    print()
    
    for driver_name, result in results.items():
        status_icon = "✅" if result.status.value == "completed" else "❌"
        print(f"   {status_icon} {driver_name.upper()}:")
        print(f"      Status: {result.status.value}")
        if result.status.value == "completed":
            print(f"      Duration: {result.duration_seconds:.2f}s")
            print(f"      Data keys: {list(result.data.keys())}")
        elif result.error:
            print(f"      Error: {result.error}")
        print()
    
    # Show aggregate progress
    print(f"📈 Overall Progress: {manager.get_aggregate_progress():.1f}%")
    print()
    
    print("=" * 70)


async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test data source drivers")
    parser.add_argument("--all", action="store_true", help="Test all enabled drivers")
    parser.add_argument("--wayback", action="store_true", help="Test Wayback only (default)")
    args = parser.parse_args()
    
    if args.all:
        await test_all_drivers()
    else:
        await test_wayback()


if __name__ == "__main__":
    asyncio.run(main())

