import os
import vk_api
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

VK_APP_ID = "6287487"
REFRESH_URL = f"https://oauth.vk.com/authorize?client_id={VK_APP_ID}&scope=video,wall,offline&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token"

def check_token_validity():
    access_token = os.getenv('VK_ACCESS_TOKEN')
    if not access_token or access_token == "***":
        return False, "missing"
    try:
        vk = vk_api.VkApi(token=access_token)
        api = vk.get_api()
        api.users.get()
        return True, "valid"
    except vk_api.exceptions.ApiError as e:
        if "invalid" in str(e).lower() or "expired" in str(e).lower():
            return False, "expired"
        return False, str(e)
    except Exception as e:
        return False, str(e)

def print_refresh_instructions():
    print("\n" + "="*70)
    print("VK TOKEN NEEDS REFRESH")
    print("="*70)
    print("VK tokens now expire in 24 hours.")
    print("To get a new token:")
    print(f"1. Visit:\n   {REFRESH_URL}")
    print("2. Log in and click 'Allow'")
    print("3. Copy the token from the address bar")
    print("4. Update VK_ACCESS_TOKEN in .env file")
    print("="*70 + "\n")

def get_refresh_url():
    return REFRESH_URL

def upload_to_vk(video_path, description="", title=""):
    access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    user_id = os.getenv('VK_USER_ID')

    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else ("PLACEHOLDER (***)" if s == "***" else "MISSING")
    print(f"[vk] User ID: {user_id or 'auto-detect'}")
    print(f"[vk] Group ID: {group_id or 'not set (using profile)'}")
    print(f"[vk] Access Token: {mask(access_token)}")

    if not access_token or access_token == "***":
        print("[vk] Access token is missing or a placeholder. Skipping VK upload.")
        return {'status': 'skipped', 'reason': 'missing_credentials'}

    try:
        print("Starting VK session...")
        vk_session = vk_api.VkApi(token=access_token)
        vk = vk_session.get_api()
        upload = vk_api.VkUpload(vk_session)
    except Exception as e:
        print(f"Failed to initialize VK session: {e}")
        return {'status': 'failed', 'error': str(e)}

    if not user_id:
        try:
            user_info = vk.users.get()[0]
            user_id = str(user_info['id'])
            print(f"Auto-detected user ID: {user_id}")
        except Exception as e:
            print(f"Could not auto-detect user ID: {e}")
            print("   Set VK_USER_ID in .env to skip this step")

    message = description if description else "Learn Russian with Velocity Russian!"
    if not message.strip():
        message = "New Russian lesson!"

    try:
        print("\nUploading video to VK...")
        print("This may take a few minutes depending on video size...")

        is_group = bool(group_id and group_id != "***")
        video_kwargs = {
            'video_file': str(video_path),
            'name': title or 'Russian Language Lesson',
            'description': description[:220] if description else '',
        }
        if is_group:
            group_id_clean = str(group_id).lstrip('-')
            group_id_int = int(group_id_clean)
            video_kwargs['group_id'] = group_id_int

        video = upload.video(**video_kwargs)

        print(f"Video uploaded successfully!")
        print(f"Video ID: {video['video_id']}")
        print(f"Owner ID: {video['owner_id']}")

        print("\nPosting to wall...")

        attachment = f"video{video['owner_id']}_{video['video_id']}"

        if is_group:
            post_result = vk.wall.post(
                owner_id=-group_id_int,
                from_group=1,
                message=message,
                attachments=attachment
            )
            post_id = post_result['post_id']
            post_url = f"https://vk.com/wall-{group_id_int}_{post_id}"
            print(f"Posted to community wall!")
        else:
            post_result = vk.wall.post(
                owner_id=user_id,
                message=message,
                attachments=attachment
            )
            post_id = post_result['post_id']
            post_url = f"https://vk.com/wall{user_id}_{post_id}"
            print(f"Posted to personal profile!")

        print(f"Post ID: {post_id}")
        print(f"View post: {post_url}")

        result = {
            'success': True,
            'video_id': video['video_id'],
            'owner_id': video['owner_id'],
            'post_id': post_id,
            'post_url': post_url,
            'message': 'Video uploaded and posted to VK successfully'
        }

        print(f"\nVK Upload Complete!")
        return result

    except vk_api.exceptions.ApiError as e:
        error_msg = f"VK API Error: {e}"

        if "invalid" in str(e).lower():
            print(f"\nToken is invalid or expired.")
            print_refresh_instructions()
        elif "Access denied" in str(e):
            print(f"\n{error_msg}")
            print("\nSolution:")
            print("   Your token doesn't have the required permissions.")
            print("   You need a token with 'video', 'wall', and 'offline' permissions.")

        raise Exception(error_msg)

    except FileNotFoundError:
        raise Exception(f"Video file not found: {video_path}")

    except Exception as e:
        raise Exception(f"Failed to upload to VK: {e}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python upload_vk.py <video_path> [description] [title]")
        sys.exit(1)

    video_path = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else "Learn Russian with Velocity Russian!"
    title = sys.argv[3] if len(sys.argv) > 3 else "Russian Lesson"

    try:
        result = upload_to_vk(video_path, description, title)
        print(f"\nSuccess!")
        print(f"Post URL: {result['post_url']}")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
