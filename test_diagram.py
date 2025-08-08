#!/usr/bin/env python3
"""Test script for class diagram generation."""

import asyncio
import os
from dotenv import load_dotenv
from src.class_diagram_generator import ClassDiagramGenerator

load_dotenv()

async def test_diagram_generation():
    """Test the class diagram generation with a sample repository."""
    generator = ClassDiagramGenerator()
    
    # Sample repository info
    sample_repo = {
        "name": "FastAPI",
        "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
        "language": "Python",
        "url": "https://github.com/tiangolo/fastapi"
    }
    
    print("Testing class diagram generation...")
    diagram_path = await generator.generate_diagram(sample_repo)
    
    if diagram_path:
        print(f"✅ Diagram generated successfully: {diagram_path}")
        return True
    else:
        print("❌ Failed to generate diagram")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_diagram_generation())
    exit(0 if success else 1)
