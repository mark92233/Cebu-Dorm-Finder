import asyncio
import os
import re
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import stealth_async
from asgiref.sync import sync_to_async
from maps.models import FacebookPost

# --- Configuration ---
# Path to the saved authentication state
AUTH_STATE_PATH = os.path.join(settings.BASE_DIR, 'auth_state.json')

# Target Facebook groups (use public, unmanaged groups for better stability)
TARGET_GROUPS = {
    'CEBU RENTALS - HOUSE, CONDO, APARTMENT FOR RENT IN CEBU CITY': 'https://www.facebook.com/groups/994303254903669/',
    'Balamban Cebu Room for Rent': 'https://www.facebook.com/groups/3608514209395477/',
    'CEBU ROOMS FOR RENT, APARTMENT FOR RENT' : 'https://www.facebook.com/groups/182459758510841/',
    'CEBU RENTAL HOUSE/CONDO/COMMERCIAL UNITS': 'https://www.facebook.com/groups/511118581825001/',
    'Liloan Room for Rent': 'https://www.facebook.com/groups/943056113997974/',
    'CEBU RENTALS-BOARDING HOUSE,APARTMENTS,CONDO,HOUSE, AIRBNB,VAN,CAR ETC..' : 'https://www.facebook.com/groups/993673090964916',
    'Cebu Rentals: Apartments, Condos, Houses, Rooms' : 'https://www.facebook.com/groups/rentcebu',
    # Add more relevant public group names and URLs here
    # to be added some other time 
    
}

# --- PII Sanitization (The Privacy Sanitizer Matrix) ---
PHONE_REGEX = re.compile(r'(?:\+63|0)?[ -]?9\d{2}[ -]?\d{3}[ -]?\d{4}\b')
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')

def sanitize_text(text):
    """Strips Philippine phone numbers and emails from a block of text."""
    text = PHONE_REGEX.sub('[PHONE REMOVED]', text)
    text = EMAIL_REGEX.sub('[EMAIL REMOVED]', text)
    return text

class Command(BaseCommand):
    help = 'Launches a stealth Playwright browser to scrape housing data from Facebook groups.'

    def handle(self, *args, **options):
        if not os.path.exists(AUTH_STATE_PATH):
            self.stdout.write(self.style.ERROR(
                f"Authentication file not found at '{AUTH_STATE_PATH}'.\n"
                f"Please run 'python scripts/generate_auth_state.py' first."
            ))
            return

        asyncio.run(self.scrape())

    async def scrape(self):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Facebook scraper...'))
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--start-maximized"])
            context = await browser.new_context(
                storage_state=AUTH_STATE_PATH,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            await stealth_async(page) # Apply stealth measures

            total_saved = 0
            for group_name, group_url in TARGET_GROUPS.items():
                self.stdout.write(f"\n[*] Navigating to group: {group_name}")
                try:
                    # Step 1: Inject Session State (handled by new_context) and go to URL
                    await page.goto(group_url, wait_until='domcontentloaded', timeout=60000)
                    await page.wait_for_timeout(random.randint(3000, 5000))

                    # Step 2: Simulate Human Scrolling
                    self.stdout.write("[*] Scrolling to load posts...")
                    for _ in range(5): # Scroll 5 times to load a good number of posts
                        await page.evaluate('window.scrollBy(0, window.innerHeight * 2)')
                        await page.wait_for_timeout(random.randint(2000, 4000))

                    # Step 3: Expand Text Containers
                    self.stdout.write("[*] Expanding 'See more' links...")
                    see_more_buttons = page.locator('div[role="button"]:has-text("See more")')
                    count = await see_more_buttons.count()
                    for i in range(count):
                        try:
                            await see_more_buttons.nth(i).click(timeout=2000)
                        except TimeoutError:
                            pass # Ignore if button is not clickable
                    await page.wait_for_timeout(3000)

                    # Step 4: Extract and Sanitize
                    self.stdout.write("[*] Extracting post data...")
                    posts = await page.locator('div[role="article"]').all()
                    self.stdout.write(f"[*] Found {len(posts)} potential posts on the page.")

                    group_saved_count = 0
                    for post_locator in posts:
                        # Get the post's unique URL from the timestamp link
                        timestamp_link = post_locator.locator('a[href*="/posts/"], a[href*="/permalink/"]').first
                        if await timestamp_link.count() == 0: continue
                        
                        post_href = await timestamp_link.get_attribute('href')
                        post_url = post_href.split('?')[0]

                        # Get the full text content and sanitize it
                        post_content = await post_locator.inner_text()
                        if not post_content: continue
                        sanitized_content = sanitize_text(post_content)

                        # Save to database asynchronously
                        saved = await self.save_post_to_db(post_url, sanitized_content, group_name)
                        if saved:
                            group_saved_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f"[*] Saved {group_saved_count} new posts from {group_name}."))
                    total_saved += group_saved_count

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"An error occurred while scraping {group_name}: {e}"))
            
            await browser.close()
            self.stdout.write(self.style.SUCCESS(f"\n✅ Scraping complete. Total new posts saved: {total_saved}"))

    @sync_to_async
    def save_post_to_db(self, url, content, group):
        """
        Uses update_or_create to save a post, preventing duplicates.
        Returns True if a new object was created, False otherwise.
        """
        obj, created = FacebookPost.objects.update_or_create(
            post_url=url,
            defaults={
                'post_content': content,
                'source_group': group
            }
        )
        if created:
            self.stdout.write(f"  -> New post found and saved: {url[:50]}...")
        return created