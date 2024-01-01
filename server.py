from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

def create_aws_services_and_pricing_prompt(data):
    try:
        with open('prompt.txt', 'r') as file:
            file_contents = file.read()

        prompt = file_contents
        for requirement in data.get("requirements", []):
            prompt += f"- {requirement}\n"

        additional_features = data.get("additionalFeatures", {}).get("details", "")
        if additional_features:
            prompt += f"\nAdditional Features: {additional_features}\n"

        prompt += "\nPlease provide suggestions on the specific AWS services that would be suitable for these requirements, along with an estimation of their costs."
        return prompt
    except Exception as e:
        raise Exception(f"Error in create_aws_services_and_pricing_prompt: {str(e)}")

def generate_content_with_api(prompt):
    try:
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        api_key = "AIzaSyBivWqCDftV_7k7kUjyzI1fkkAriD1-KGE"  # Replace with your actual API key

        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}

        response = requests.post(f"{api_url}?key={api_key}", json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed with status code {response.status_code}")
    except Exception as e:
        raise Exception(f"Error in generate_content_with_api: {str(e)}")

def text_to_json(text):
    try:
        data = {}
        current_section = None

        for line in text.split('\n'):
            line = line.strip()
            if line.endswith(":"):
                current_section = line[:-1].lstrip("0123456789. ").strip()
                data[current_section] = {}
            elif current_section is not None:
                if ":" in line:
                    key, value = line.split(':', 1)
                    data[current_section][key.strip()] = value.strip()
                else:
                    if line:
                        if 'description' not in data[current_section]:
                            data[current_section]['description'] = []
                        data[current_section]['description'].append(line.lstrip("- ").strip())

        data = {k: v for k, v in data.items() if v}
        return json.dumps(data, indent=4)
    except Exception as e:
        raise Exception(f"Error in text_to_json: {str(e)}")

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            raise ValueError("No file part")

        file = request.files['file']
        if file.filename == '':
            raise ValueError("No selected file")

        data = json.load(file)
        prompt = create_aws_services_and_pricing_prompt(data)
        response = generate_content_with_api(prompt)
        model_response = response['candidates'][0]['content']['parts'][0]['text']
        formatted_response = model_response.replace('*', '').strip()
        json_output = text_to_json(formatted_response)

        return json_output
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
