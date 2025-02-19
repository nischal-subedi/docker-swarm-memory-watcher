import requests

TEAMS_WEBHOOK_URL = "https://example.com/webhook"

def send_notification(service_name: str, server_ip: str) -> None:
    card = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": "Memory Threshold Exceeded",
        "themeColor": "FF0000",
        "title": "High Memory Alert",
        "sections": [
            {
                "activityTitle": f"Service {service_name} has just now exceeded memory threshold",
                "activitySubtitle": f"Server IP is: {server_ip}",
                "text": "Memory usage exceeded the defined threshold. The service is now being reset."
            }
        ]
    }

    try:
      response = requests.post(TEAMS_WEBHOOK_URL, json=card)
      response.raise_for_status()
    except requests.RequestException as err:
      print(f"Error sending notification: {err}")