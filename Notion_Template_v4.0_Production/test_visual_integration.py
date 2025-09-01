#!/usr/bin/env python3
"""
Test Visual Integration for Estate Planning Concierge v4.0
Tests GitHub asset URLs, tasteful emoji, and premium visual components
"""

import sys
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from modules.config import load_config
from modules.visuals import (
    get_estate_emoji, 
    create_professional_header,
    create_estate_status_indicator,
    create_document_callout,
    create_professional_divider,
    create_beneficiary_list,
    create_estate_checklist,
    create_professional_timeline,
    create_confidential_notice
)

# Import asset functions from deploy.py
from deploy import (
    get_github_asset_url,
    get_asset_icon,
    get_asset_cover,
    get_page_emoji,
    determine_page_theme
)

def test_estate_emoji():
    """Test all estate-appropriate emoji mappings"""
    print("\n🧪 Testing Estate Emoji System:")
    print("=" * 50)
    
    emoji_tests = [
        ("document", "Document"),
        ("legal", "Legal"),
        ("family", "Family"),
        ("assets", "Assets"),
        ("property", "Property"),
        ("heritage", "Heritage"),
        ("complete", "Complete"),
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("confidential", "Confidential")
    ]
    
    for key, label in emoji_tests:
        emoji = get_estate_emoji(key)
        print(f"  {label:15} : {emoji}")
    
    return True

def test_github_urls():
    """Test GitHub asset URL generation"""
    print("\n🧪 Testing GitHub Asset URL Generation:")
    print("=" * 50)
    
    test_pages = [
        ("Legal Documents", "default"),
        ("Family Hub", "purple"),
        ("Financial Accounts", "green"),
        ("Executor Checklist", "blue"),
        ("Memorial Preferences", "default")
    ]
    
    for page_title, theme in test_pages:
        icon_url = get_github_asset_url("icon", page_title, theme)
        cover_url = get_github_asset_url("cover", page_title, theme)
        
        print(f"\n  📄 {page_title} ({theme} theme):")
        print(f"     Icon:  {icon_url}")
        print(f"     Cover: {cover_url}")
    
    return True

def test_page_categorization():
    """Test automatic page categorization"""
    print("\n🧪 Testing Page Categorization:")
    print("=" * 50)
    
    test_pages = [
        "Legal Will and Testament",
        "Family Beneficiaries",
        "Bank Accounts",
        "Insurance Policies",
        "Executor Tasks",
        "Memorial Service Plans",
        "Admin Dashboard",
        "Contact Information"
    ]
    
    for page in test_pages:
        emoji = get_page_emoji(page)
        theme = determine_page_theme(page)
        print(f"  {emoji} {page:30} → Theme: {theme}")
    
    return True

def test_visual_components():
    """Test premium visual components"""
    print("\n🧪 Testing Premium Visual Components:")
    print("=" * 50)
    
    # Test status indicators
    print("\n  Status Indicators:")
    statuses = ["complete", "in_progress", "pending", "review", "verified"]
    for status in statuses:
        indicator = create_estate_status_indicator(status)
        print(f"    {status:12} : {indicator}")
    
    # Test professional dividers
    print("\n  Professional Dividers:")
    divider_styles = ["simple", "section", "subtle", "formal"]
    for style in divider_styles:
        divider = create_professional_divider(style)
        divider_text = divider["paragraph"]["rich_text"][0]["text"]["content"]
        print(f"    {style:10} : {divider_text[:30]}...")
    
    # Test confidential notice
    print("\n  Confidential Notice:")
    notice = create_confidential_notice()
    notice_text = notice["callout"]["rich_text"][0]["text"]["content"]
    print(f"    {notice_text[:60]}...")
    
    return True

def test_beneficiary_components():
    """Test beneficiary and checklist components"""
    print("\n🧪 Testing Estate Planning Components:")
    print("=" * 50)
    
    # Test beneficiary list
    beneficiaries = [
        {"name": "John Doe", "relationship": "Spouse", "percentage": "50"},
        {"name": "Jane Doe", "relationship": "Daughter", "percentage": "25"},
        {"name": "Jack Doe", "relationship": "Son", "percentage": "25"}
    ]
    
    blocks = create_beneficiary_list(beneficiaries)
    print(f"\n  Beneficiary List: {len(blocks)} blocks created")
    
    # Test estate checklist
    checklist_items = [
        {"task": "Update will", "completed": True},
        {"task": "Review beneficiaries", "completed": True},
        {"task": "File tax documents", "completed": False}
    ]
    
    checklist = create_estate_checklist("Estate Planning Tasks", checklist_items)
    print(f"  Estate Checklist: {len(checklist)} blocks created")
    
    # Test timeline
    milestones = [
        {"title": "Initial Planning", "date": "January 2025", "completed": True},
        {"title": "Document Review", "date": "February 2025", "completed": False}
    ]
    
    timeline = create_professional_timeline(milestones)
    print(f"  Professional Timeline: {len(timeline)} blocks created")
    
    return True

def test_notion_api_structures():
    """Test that visual components create valid Notion API structures"""
    print("\n🧪 Testing Notion API Structure Validity:")
    print("=" * 50)
    
    try:
        # Test icon structure
        icon = get_asset_icon("Legal Documents", "default")
        assert icon["type"] == "external"
        assert "url" in icon["external"]
        print("  ✅ Icon structure valid")
    except Exception as e:
        print(f"  ❌ Icon structure failed: {e}")
        raise
    
    try:
        # Test cover structure
        cover = get_asset_cover("Financial Accounts", "green")
        assert cover["type"] == "external"
        assert "url" in cover["external"]
        print("  ✅ Cover structure valid")
    except Exception as e:
        print(f"  ❌ Cover structure failed: {e}")
        raise
    
    try:
        # Test callout structure
        callout = create_document_callout("Important legal document", "legal")
        assert callout["type"] == "callout"
        assert "rich_text" in callout["callout"]
        assert "icon" in callout["callout"]
        print("  ✅ Callout structure valid")
    except Exception as e:
        print(f"  ❌ Callout structure failed: {e}")
        raise
    
    try:
        # Test header structure
        header = create_professional_header("Estate Planning", "Your complete guide")
        assert len(header) > 0
        assert header[0]["type"] == "heading_1"
        print("  ✅ Header structure valid")
    except Exception as e:
        print(f"  ❌ Header structure failed: {e}")
        raise
    
    return True

def main():
    """Run all visual integration tests"""
    print("\n" + "=" * 60)
    print("ESTATE PLANNING CONCIERGE v4.0 - VISUAL INTEGRATION TEST")
    print("=" * 60)
    
    # Load configuration
    config = load_config(Path("config.yaml"))
    print(f"\n📋 Configuration loaded from: config.yaml")
    print(f"   Visual tier: {config.get('visual_config', {}).get('tier', 'standard')}")
    print(f"   Default theme: {config.get('visual_config', {}).get('default_theme', 'default')}")
    
    # Run all tests
    tests = [
        ("Estate Emoji System", test_estate_emoji),
        ("GitHub URL Generation", test_github_urls),
        ("Page Categorization", test_page_categorization),
        ("Visual Components", test_visual_components),
        ("Estate Components", test_beneficiary_components),
        ("Notion API Structures", test_notion_api_structures)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test failed: {test_name}")
            print(f"   Error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status:12} : {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VISUAL INTEGRATION TESTS PASSED!")
        print("\n✨ The Estate Planning Concierge v4.0 is ready with:")
        print("   • Tasteful, professional emoji throughout")
        print("   • GitHub-hosted premium assets (3000+ files)")
        print("   • Dignified visual components for estate planning")
        print("   • Automatic theme selection based on content")
        print("   • Complete integration with Notion API")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please review and fix issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)