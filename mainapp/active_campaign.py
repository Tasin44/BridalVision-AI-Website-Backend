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

    url = f"{api_url}/api/3/contact/sync"
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
            print(f"ActiveCampaign: contact synced → {email}")
            
            contact_data = response.json()
            contact_id = contact_data.get("contact", {}).get("id")
            
            if contact_id:
                # 1. Look for the 'Virtual' tag to get its ID
                tag_name = "Virtual"
                tag_id = None
                tag_search_url = f"{api_url}/api/3/tags?search={tag_name}"
                tag_resp = requests.get(tag_search_url, headers=headers, timeout=10)
                
                if tag_resp.status_code == 200:
                    tags = tag_resp.json().get("tags", [])
                    for t in tags:
                        if t.get("tag", "").lower() == tag_name.lower():
                            tag_id = t.get("id")
                            break
                
                # 2. If tag doesn't exist, create it
                if not tag_id:
                    create_tag_url = f"{api_url}/api/3/tags"
                    create_tag_payload = {
                        "tag": {
                            "tag": tag_name,
                            "tagType": "contact",
                            "description": "Added via Virtual Fitting Room"
                        }
                    }
                    create_tag_resp = requests.post(create_tag_url, json=create_tag_payload, headers=headers, timeout=10)
                    if create_tag_resp.status_code in (200, 201):
                        tag_id = create_tag_resp.json().get("tag", {}).get("id")
                
                # 3. Add the tag to the contact
                if tag_id:
                    contact_tag_url = f"{api_url}/api/3/contactTags"
                    contact_tag_payload = {
                        "contactTag": {
                            "contact": contact_id,
                            "tag": tag_id
                        }
                    }
                    requests.post(contact_tag_url, json=contact_tag_payload, headers=headers, timeout=10)
                    print(f"ActiveCampaign: applied tag 'Virtual' to → {email}")

            return True
        else:
            print(f"ActiveCampaign: failed [{response.status_code}] → {response.text}")
            return False
    except Exception as e:
        print(f"ActiveCampaign: exception → {e}")
        return False