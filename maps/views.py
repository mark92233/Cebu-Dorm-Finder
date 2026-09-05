from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from decouple import config
from django.core.paginator import Paginator
import json
import re
import requests
from bs4 import BeautifulSoup
# import google.genai as genai # Temporarily disabled to resolve environment issues.
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import SchoolMetadata, FacebookPost

# Configure Gemini API at the module level
# The Gemini API is temporarily disabled to resolve environment conflicts.
GEMINI_API_KEY = None

@login_required
def main_map_view(request):
    """
    Renders the main map page and passes the Geoapify API key to the template.
    """
    context = {
        'geoapify_api_key': config('GEOAPIFY_API_KEY', default='')
    }
    return render(request, 'user/maps.html', context)

@login_required
def list_gemini_models_view(request):
    """
    Temporarily disabled. Returns an empty list.
    """
    return JsonResponse({'models': [], 'message': 'Gemini features are temporarily disabled.'})

@login_required
def scraped_posts_view(request):
    """
    Displays a paginated list of all scraped Facebook posts.
    """
    post_list = FacebookPost.objects.all()
    paginator = Paginator(post_list, 15) # Show 15 posts per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'user/scraped_posts.html', context)

@login_required
@require_POST
def fetch_school_details_view(request):
    """
    On-demand data enrichment pipeline for a single school.
    """
    try:
        data = json.loads(request.body)
        school_name = data.get('school_name')
        location = data.get('location')

        if not school_name:
            return JsonResponse({'error': 'School name is required.'}, status=400)

        # --- Optimization: Check for cached data first ---
        # Before running the pipeline, check if we already have data for this school.
        cached_data = SchoolMetadata.objects.filter(school_name=school_name).first()
        if cached_data:
            print(f"[*] Cache hit for '{school_name}'. Serving from database.")
            return JsonResponse({
                'summary': cached_data.summary,
                'imageUrl': cached_data.image_url
            })

        # --- Pipeline Step 1 & 2: Search Wikipedia with fallback ---
        session = requests.Session()
        session.headers.update({'User-Agent': 'DormFinderBot/1.0 (contact: admin@dormfinder.local)'})
        
        def search_wiki(name):
            search_params = {
                "action": "opensearch",
                "search": name,
                "limit": "1",
                "namespace": "0",
                "format": "json"
            }
            try:
                response = session.get("https://en.wikipedia.org/w/api.php", params=search_params)
                response.raise_for_status()
                search_results = response.json()
                if search_results and len(search_results[3]) > 0:
                    return search_results[3][0] # Return the URL
            except requests.RequestException as e:
                print(f"Wikipedia search failed for '{name}': {e}")
            return None

        wiki_url = search_wiki(school_name)
        if not wiki_url:
            # Fallback: remove common suffixes and try again
            cleaned_name = re.sub(r'\s-\s.*$|\s\(.*\)$|\sCampus$|\sBranch$', '', school_name, flags=re.IGNORECASE).strip()
            if cleaned_name.lower() != school_name.lower():
                wiki_url = search_wiki(cleaned_name)

        # Initialize the Gemini model once if the API key is available.
        model = None
        if GEMINI_API_KEY:
            try:
                # Use the stable 'gemini-pro' model to avoid version conflicts.
                model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"Failed to initialize Gemini model: {e}")

        summary_text = None
        image_url = None

        # --- Pipeline Step 3: Scrape if found ---
        if wiki_url:
            try:
                response = session.get(wiki_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract intro text
                paragraphs = soup.find_all('p', limit=3)
                raw_text = "\n".join([p.get_text(strip=True) for p in paragraphs])

                # Extract infobox image
                infobox = soup.find('table', {'class': 'infobox'})
                if infobox:
                    img_tag = infobox.find('img')
                    if img_tag and img_tag.get('src'):
                        image_url = "https:" + img_tag.get('src')

                # --- Pipeline Step 4: Simplify with AI ---
                if raw_text and model:
                    prompt = (
                        "You are a data processing utility. Summarize the following text about a school into 2-3 concise sentences "
                        "for a student housing dashboard. Focus on location, academic identity, and key facts. "
                        "Return ONLY the raw summary sentences without any introductory text or markdown.\n\n"
                        f"Raw Text:\n{raw_text}"
                    )
                    ai_response = model.generate_content(prompt)
                    summary_text = ai_response.text.strip()
                else:
                    summary_text = raw_text # Fallback to raw text if AI fails

            except Exception as e:
                print(f"Scraping or AI summary failed for '{school_name}': {e}")

        # --- Pipeline Step 5: AI generation if not found ---
        if not summary_text and model:
            try:
                prompt = (
                    f"Generate a short, 2-3 sentence description for a school named '{school_name}' located in '{location}'. "
                    "Focus on its likely academic offerings and role in the local community. "
                    "Return ONLY the raw description without any introductory text or markdown."
                )
                ai_response = model.generate_content(prompt)
                summary_text = ai_response.text.strip()
            except Exception as e:
                print(f"AI generation failed for '{school_name}': {e}")

        # --- Pipeline Step 6: Save to Database ---
        SchoolMetadata.objects.update_or_create(
            school_name=school_name,
            defaults={
                'summary': summary_text,
                'image_url': image_url,
                'source_url': wiki_url
            }
        )

        # --- Final Step: Return data to frontend ---
        return JsonResponse({
            'summary': summary_text,
            'imageUrl': image_url
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except Exception as e:
        # Generic error handler for unexpected issues
        print(f"An unexpected error occurred in fetch_school_details_view: {e}")
        return JsonResponse({'error': 'An internal server error occurred.'}, status=500)
