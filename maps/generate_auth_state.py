import asyncio
from playwright.async_api import async_playwright
import os

# --- Configuration ---
# The path where the authentication state will be saved.
# We place it in the project's root directory.
AUTH_STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'auth_state.json')
# The initial URL to visit.
LOGIN_URL = 'https://www.facebook.com'

async def main():
    """
    Launches a browser window for the user to manually log in.
    After successful login and navigation, it saves the session state.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"[*] Navigating to {LOGIN_URL}...")
        await page.goto(LOGIN_URL)

        print("\n" + "="*50)
        print("IMPORTANT: Please log in to your 'burner' Facebook account manually in the browser window.")
        print("Once you are logged in and see your news feed, you can close this script by pressing Ctrl+C in this terminal.")
        print("DO NOT close the browser window yourself.")
        print("="*50 + "\n")

        try:
            # A long timeout to give the user plenty of time to log in.
            await page.wait_for_timeout(300000) # 5 minutes
        except asyncio.CancelledError:
            print("\n[*] Proceeding to save state...")
        finally:
            print(f"[*] Saving authentication state to: {AUTH_STATE_PATH}")
            await context.storage_state(path=AUTH_STATE_PATH)
            await browser.close()
            print("[*] Authentication state saved successfully. You can now run the scraper.")

if __name__ == '__main__':
    if os.path.exists(AUTH_STATE_PATH) and input(f"[?] Auth file exists. Overwrite? (y/n): ").lower() != 'y':
        exit("[*] Exiting.")
    asyncio.run(main())