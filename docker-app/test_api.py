#!/usr/bin/env python3
"""Test script for Crosshatch API."""

import requests
import sys
from pathlib import Path


def test_health(base_url="http://localhost:5000"):
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{base_url}/health")

    if response.status_code == 200:
        print("✓ Health check passed")
        print(f"  Response: {response.json()}")
        return True
    else:
        print(f"✗ Health check failed: {response.status_code}")
        return False


def test_crosshatch(image_path, output_path, style="horizontal",
                   base_url="http://localhost:5000"):
    """Test crosshatch endpoint."""
    print(f"\nTesting crosshatch with image: {image_path}")
    print(f"  Style: {style}")

    if not Path(image_path).exists():
        print(f"✗ Error: Image not found: {image_path}")
        return False

    # Prepare request
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'style': style, 'max_dimension': '1200'}

        response = requests.post(
            f"{base_url}/api/crosshatch",
            files=files,
            data=data,
            timeout=120  # 2 minute timeout
        )

    if response.status_code == 200:
        # Save output
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✓ Crosshatch created successfully")
        print(f"  Output saved to: {output_path}")
        return True
    else:
        print(f"✗ Request failed: {response.status_code}")
        try:
            print(f"  Error: {response.json()}")
        except:
            print(f"  Response: {response.text}")
        return False


def main():
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path> [output_path] [style]")
        print("\nExample:")
        print("  python test_api.py portrait.jpg output.jpg horizontal")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "test_output.jpg"
    style = sys.argv[3] if len(sys.argv) > 3 else "horizontal"

    print("="*60)
    print("Crosshatch API Test")
    print("="*60)

    # Test health
    if not test_health():
        print("\n✗ Health check failed. Is the API running?")
        sys.exit(1)

    # Test crosshatch
    success = test_crosshatch(image_path, output_path, style)

    print("\n" + "="*60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
