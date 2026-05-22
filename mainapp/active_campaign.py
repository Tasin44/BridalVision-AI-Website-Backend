import requests
from django.conf import settings


def add_contact_to_active_campaign(email: str) -> bool:
    """
    Adds an email to ActiveCampaign contacts.
    Returns True on success, False on failure.
    Fails silently — never breaks the main email flow.
    """
    api_url = getattr(settings, 'ACTIVE_CAMPAIGN_API_URL', '').rstrip('/')
    api_key = getattr(settings, 'ACTIVE_CAMPAIGN_API_KEY', '')

    if not api_url or not api_key:
        print("ActiveCampaign: API URL or key not configured.")
        return False

    url = f"{api_url}/api/3/contacts"
    headers = {
        "Api-Token": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contact": {
            "email": email,
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            print(f"ActiveCampaign: contact added → {email}")
            return True
        else:
            print(f"ActiveCampaign: failed [{response.status_code}] → {response.text}")
            return False
    except Exception as e:
        print(f"ActiveCampaign: exception → {e}")
        return False