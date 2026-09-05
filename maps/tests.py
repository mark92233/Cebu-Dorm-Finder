from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import json
from .models import SchoolMetadata

User = get_user_model()

class FetchSchoolDetailsViewTest(TestCase):

    def setUp(self):
        """Set up a test user and client, and log the user in."""
        self.user = User.objects.create_user(email='testuser@example.com', password='password123')
        self.client.login(email='testuser@example.com', password='password123')
        self.url = reverse('maps:fetch_school_details')

    @patch('maps.views.genai.GenerativeModel')
    @patch('maps.views.requests.Session.get')
    def test_successful_pipeline_with_wiki_and_ai_summary(self, mock_requests_get, mock_genai_model):
        """
        Tests the full successful pipeline: Wikipedia search finds a page, it's scraped,
        Gemini summarizes it, and the result is saved and returned.
        """
        # --- Mock Configuration ---
        mock_requests_get.side_effect = [
            MagicMock(status_code=200, json=lambda: ["UV", [], [], ["https://en.wikipedia.org/wiki/University_of_the_Visayas"]]),
            MagicMock(status_code=200, text='<html><body><table class="infobox"><img src="//upload.wikimedia.org/logo.png"></table><p>Raw scraped text.</p></body></html>')
        ]
        mock_ai_response = MagicMock()
        mock_ai_response.text = "A concise AI-generated summary."
        mock_genai_model.return_value.generate_content.return_value = mock_ai_response

        # --- Test Execution ---
        payload = {'school_name': 'University of the Visayas', 'location': 'Cebu City'}
        response = self.client.post(self.url, data=json.dumps(payload), content_type='application/json')

        # --- Assertions ---
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['summary'], "A concise AI-generated summary.")
        self.assertEqual(response_data['imageUrl'], "https://upload.wikimedia.org/logo.png")

        # Verify data was saved to the database
        self.assertTrue(SchoolMetadata.objects.filter(school_name='University of the Visayas').exists())
        school_meta = SchoolMetadata.objects.get(school_name='University of the Visayas')
        self.assertEqual(school_meta.summary, "A concise AI-generated summary.")

# Create your tests here.
