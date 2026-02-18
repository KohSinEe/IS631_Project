import requests

# Your Roboflow API key
api_key = "8wMfD8Cmze9Cgiu3zeOc"

# Roboflow workflow endpoint
workflow_url = "https://serverless.roboflow.com/fridge-buddy/workflows/rf-detr"

# Direct image URL
image_url = "https://images.pexels.com/photos/1313267/pexels-photo-1313267.jpeg"


payload = {
    "api_key": api_key,
    "inputs": {
        "image": {"type": "url", "value": image_url}
    }
}

response = requests.post(workflow_url, json=payload)

# Print JSON response
print(response.json())
