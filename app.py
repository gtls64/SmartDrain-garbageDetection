import base64
import requests
import cv2
import json
import re

# Variables
api_key = "add your openAI API key here"
image_path = "captured.jpg"  # Path to the captured image
brightness = 100
contrast = 2
ifttt_key = 'add your ifttt key here'  # IFTTT key
ifttt_event_url = f'add your ifttt event url here'
event_name = 'post_tweet'  # event name IFTTT

# Function to capture a photo from the webcam and save it as 'captured.jpg'
def capture_photo(brightness=1.0, contrast=1.0):
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Could not open webcam")
        return None

    ret, frame = cap.read()

    if ret:
        # Apply brightness and contrast adjustments
        adjusted_frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)

        # Save the adjusted image as 'captured.jpg'
        cv2.imwrite('captured.jpg', adjusted_frame)
        print("Photo captured and saved as 'captured.jpg'")
    else:
        print("Failed to capture photo")

    cap.release()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to send the image to the OpenAI API and receive the response
def send_image_to_api(base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an image-recognizing assistant. When an image of a box is uploaded, you must do the following:\n\n1. Check Box Fill Level: Determine if the box is filled to the top. If the box is filled over 80% to the top, say \"YES\". If not, say \"NO\".\n\n2. Identify Contents: Identify the items inside the box.\n\n \n3.estimate the money you can get by recycling the things in the box (aluminiam can - 10c AUD, plastic bottle - 10c AUD) 4. Format the Response: Add a \">\" after the first answer (\"YES\" or \"NO\") and list the identified items.\n\nFinally, give an estimated fill percentage. Finally put all together like this {\"YES or NO\",\"Things in the box\",\"Fill percentage (only the number)\",\"amount can be earned in AUD (just the number (ex : 1.20))\"}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()

# Function to parse the response and save it as a JSON file
def parse_and_save_json(result_content):
    # Use regex to properly split the string based on the format {"status","description","confidence"}
    matches = re.findall(r'\"(.*?)\"', result_content)

    # Ensure there are exactly three items (status, description, confidence)
    if len(matches) == 4:
        # Creating a dictionary to hold the JSON structure
        json_data = {
            "filled": matches[0],       # "YES" or "NO"
            "things": matches[1],  # Things in the box
            "percentage": matches[2],    # Fill percentage
            "reward": matches[3]
        }

        # Writing the dictionary to a JSON file
        with open('response_data.json', 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

        print("JSON file 'response_data.json' has been created with the response content.")
    else:
        print("Error: The response content does not have the expected format.")

# Function to send a tweet via IFTTT
def send_tweet_via_ifttt(event, tweet_content):
    # Data to send with the request
    data = {
        'value1': tweet_content
    }

    # Send the request
    response = requests.post(ifttt_event_url, json=data)

    if response.status_code == 200:
        print('Tweet sent successfully!')
    else:
        print(f'Failed to send tweet: {response.status_code}')

# Main function
def main():
    capture_photo(brightness, contrast)

    base64_image = encode_image(image_path)

    api_response = send_image_to_api(base64_image)

    print(api_response)

    # Extract the content
    result_content = api_response['choices'][0]['message']['content']

    # Print the content
    print("Response Content: ", result_content)
    parse_and_save_json(result_content)

    # Read JSON file and extract data for the tweet
    with open('response_data.json') as json_file:
        json_data = json.load(json_file)

    # Compose the tweet content using data from the JSON file
    tweet = f"{json_data.get('percentage')}% of the Smart Drain No 1 is filled with {json_data.get('things')}. And you might get {json_data.get('reward')} AUD by recycing the things in the drain."

    # Trigger the IFTTT event with the composed tweet
    send_tweet_via_ifttt(event_name, tweet)
    print(tweet)

# Run the main function
if __name__ == "__main__":
    main()
