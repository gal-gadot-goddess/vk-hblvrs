"""
Velocity Russian - Unified Social Media Upload Script
Uploads generated reels to all connected social media platforms
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add upload directory to Python path
upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

# Import individual uploaders
upload_to_facebook = None
upload_to_instagram = None
upload_to_youtube = None
upload_to_vk = None

try:
    from upload_facebook import upload_to_facebook as fb_upload
    upload_to_facebook = fb_upload
except ImportError as e:
    print(f"[!] Facebook upload module not available: {e}")

try:
    from upload_instagram import upload_to_instagram as ig_upload
    upload_to_instagram = ig_upload
except ImportError as e:
    print(f"[!] Instagram upload module not available: {e}")

try:
    from upload_to_youtube import upload_to_youtube as yt_upload
    upload_to_youtube = yt_upload
except ImportError as e:
    print(f"[!] YouTube upload module not available: {e}")

try:
    from upload_vk import upload_to_vk as vk_upload
    upload_to_vk = vk_upload
except ImportError as e:
    print(f"[!] VK upload module not available: {e}")


def get_latest_reel():
    """Find the most recently generated reel"""
    video_dir = Path("output/video")

    if not video_dir.exists():
        print("❌ No output/video directory found")
        return None

    reels = list(video_dir.glob("*/final_reel.mp4"))

    if not reels:
        print("❌ No reels found in output/video directory")
        return None

    latest = max(reels, key=lambda p: p.stat().st_mtime)

    metadata_file = latest.parent / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    return {
        "video_path": str(latest),
        "metadata": metadata,
        "category": metadata.get("category_russian", "Russian Learning"),
        "phrases": metadata.get("phrases", [])
    }


def generate_caption(phrases, category, platform="vk"):
    """Generate social media caption - Russian-first for VK audience"""

    caption_lines = [
        f"🇷🇺 Испанский с Habla Verse! 🇪🇸",
        f"",
        f"📚 Тема: {category}",
        f"",
        f"🎯 Учим испанский легко! Сегодняшние фразы:",
        f""
    ]

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    for i, phrase in enumerate(phrases[:5]):
        emoji = emojis[i] if i < len(emojis) else f"{i+1}."
        caption_lines.append(f"{emoji} {phrase['english']}")
        caption_lines.append(f"   📍 {phrase['russian']}")
        caption_lines.append(f"   🔊 {phrase.get('spanish_cyrillic', '')}")
        caption_lines.append("")

    caption_lines.extend([
        f"💡 Совет: Повторяйте каждую фразу вслух 3 раза!",
        f"👍 Поставьте лайк, если было полезно!",
        f"💬 Напишите свой любимый перевод в комментариях!",
        f"🔔 Подпишитесь на ежедневные уроки испанского!",
        f"",
        f"📖 Как читать:",
        f"   Транскрипция кириллицей помогает произносить правильно!",
        f"",
    ])

    hashtags = [
        "#испанский",
        "#учимиспанский",
        "#испанскийдляначинающих",
        "#hablaverse",
        "#испанскийонлайн",
        "#разговорныйиспанский",
        "#испанскийязык",
        "#урокииспанского",
        "#español",
        "#полиглот"
    ]

    caption_lines.extend(hashtags)
    return "\n".join(caption_lines)


def upload_to_all_platforms(video_path, caption, category, phrases=None):
    """Upload to all configured social media platforms with comprehensive summary"""

    results = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "video": video_path,
        "uploads": {},
        "platforms_attempted": [],
        "platforms_successful": [],
        "platforms_skipped": [],
        "platforms_failed": []
    }

    print("\n" + "="*80)
    print("🚀 HABLA VERSE - MULTI-PLATFORM UPLOAD")
    print("="*80)
    print(f"Video: {video_path}")
    print(f"Category: {category}")
    print(f"Caption length: {len(caption)} characters")
    print("="*80)

    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return results

    platforms = [
        ("facebook", upload_to_facebook, "📘 Facebook"),
        ("instagram", upload_to_instagram, "📸 Instagram"),
        ("youtube", upload_to_youtube, "📺 YouTube"),
        ("vk", upload_to_vk, "🇷🇺 VK"),
    ]

    for platform_name, upload_func, display_name in platforms:
        print(f"\n{display_name} UPLOAD...")
        results["platforms_attempted"].append(platform_name)

        if upload_func:
            try:
                upload_result = None

                if platform_name == "facebook":
                    upload_result = upload_func(
                        video_path=video_path,
                        description=caption,
                        title=f"Russian: {category}"
                    )
                elif platform_name == "instagram":
                    upload_result = upload_func(
                        video_path=video_path,
                        caption=caption,
                        is_story=False
                    )
                elif platform_name == "youtube":
                    # Generate Russian metadata for YouTube with phrases
                    num_phrases = len(phrases) if phrases else 5
                    from upload_to_youtube import generate_video_metadata
                    yt_title, yt_description, yt_tags = generate_video_metadata(category, num_phrases, phrases)

                    upload_result = upload_func(
                        video_path=video_path,
                        title=yt_title,
                        description=yt_description,
                        tags=yt_tags,
                        category_id='27'  # Education
                    )
                elif platform_name == "vk":
                    upload_result = upload_func(
                        video_path=video_path,
                        description=caption,
                        title=f"Russian: {category}"
                    )

                if upload_result:
                    results["uploads"][platform_name] = upload_result
                    results["platforms_successful"].append(platform_name)
                    print(f"✅ {display_name} upload successful")
                else:
                    results["uploads"][platform_name] = {"status": "failed", "error": "Upload function returned None"}
                    results["platforms_failed"].append(platform_name)
                    print(f"❌ {display_name} upload failed: No result returned")

            except Exception as e:
                error_msg = str(e)
                results["uploads"][platform_name] = {"status": "failed", "error": error_msg}
                results["platforms_failed"].append(platform_name)
                print(f"❌ {display_name} upload failed: {error_msg}")
        else:
            print(f"⚠️  {display_name} upload skipped (module not available)")
            results["uploads"][platform_name] = {"status": "skipped", "reason": "Module not available"}
            results["platforms_skipped"].append(platform_name)

    # ===== BEAUTIFUL SUMMARY =====
    print("\n" + "="*80)
    print("📊 UPLOAD SUMMARY")
    print("="*80)

    total_attempted = len(results["platforms_attempted"])
    successful_count = len(results["platforms_successful"])
    failed_count = len(results["platforms_failed"])
    skipped_count = len(results["platforms_skipped"])

    print(f"\n📈 Overall Status:")
    print(f"   ├─ Total Platforms: {total_attempted}")
    print(f"   ├─ ✅ Successful: {successful_count}")
    print(f"   ├─ ❌ Failed: {failed_count}")
    print(f"   └─ ⚠️  Skipped: {skipped_count}")

    if total_attempted > 0:
        success_rate = (successful_count / total_attempted) * 100
        print(f"\n🎯 Success Rate: {success_rate:.0f}%")

    if results["platforms_successful"]:
        print(f"\n✅ SUCCESSFUL UPLOADS ({len(results['platforms_successful'])}):")
        for platform in results["platforms_successful"]:
            platform_data = results["uploads"].get(platform, {})
            video_id = platform_data.get("video_id", "N/A")
            print(f"   ✅ {platform.upper()}: Success (Video ID: {video_id})")

    if results["platforms_failed"]:
        print(f"\n❌ FAILED UPLOADS ({len(results['platforms_failed'])}):")
        for platform in results["platforms_failed"]:
            platform_data = results["uploads"].get(platform, {})
            error = platform_data.get("error", "Unknown error")
            print(f"   ❌ {platform.upper()}: Failed - {error[:80]}...")

    if results["platforms_skipped"]:
        print(f"\n⚠️  SKIPPED PLATFORMS ({len(results['platforms_skipped'])}):")
        skipped_list = ", ".join([p.upper() for p in results["platforms_skipped"]])
        print(f"   ⚠️  {skipped_list}")
        print(f"   💡 Add credentials to enable these platforms")

    print("\n" + "="*80)

    results_file = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved: {results_file}")
    print("="*80)

    return results


def main():
    """Main upload workflow"""

    print("\n" + "="*80)
    print("🇷🇺 HABLA VERSE - AUTOMATED UPLOAD 🇪🇸")
    print("="*80)

    reel = get_latest_reel()

    if not reel:
        print("\n❌ No reel found! Run facebook_reels_automation.py first.")
        sys.exit(1)

    print(f"\n✅ Found latest reel:")
    print(f"   Category: {reel['category']}")
    print(f"   Video: {reel['video_path']}")
    print(f"   Phrases: {len(reel['phrases'])}")

    caption = generate_caption(reel['phrases'], reel['category'], platform="vk")
    print(f"\n📝 Generated caption ({len(caption)} chars):")
    print("-"*80)
    print(caption[:500] + "..." if len(caption) > 500 else caption)
    print("-"*80)

    results = upload_to_all_platforms(
        reel['video_path'],
        caption,
        reel['category'],
        reel['phrases']
    )

    results["phrases"] = reel['phrases']

    successful = len(results.get("platforms_successful", []))
    failed = len(results.get("platforms_failed", []))
    skipped = len(results.get("platforms_skipped", []))

    if successful > 0:
        print(f"\n✅ Upload complete! {successful} platform(s) successful.")
        if skipped > 0:
            print(f"💡 {skipped} platform(s) skipped - add credentials to enable them")
        sys.exit(0)
    elif failed > 0:
        print(f"\n⚠️  All attempted uploads failed ({failed} failed, {skipped} skipped).")
        print("💡 Check the error messages above and verify your credentials")
        sys.exit(1)
    else:
        print(f"\n⚠️  All uploads skipped ({skipped} skipped).")
        print("💡 Add credentials in GitHub Secrets to enable uploads")
        sys.exit(1)


if __name__ == "__main__":
    main()
