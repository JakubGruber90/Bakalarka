import openai
import os
from flask import Flask, Response, request, jsonify, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

load_dotenv("C:/FIIT_STU/bakalarka/Implementacia/moja_appka_quasar/.env")

bot_system_message = "You are a helpful assistant." #sprava pre model, ako sa ma spravat

#premenne na pristup do openai api
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME") #nazyvane aj deployment id
openai_api_version = os.getenv("API_VERSION")

#premenne na pristup do azure ai search
search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
search_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
search_index = os.getenv("AZURE_AI_SEARCH_INDEX"), # index1 nema vektory | index2 ma vektory

client = openai.AzureOpenAI(
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key,
    api_version=openai_api_version
)

@app.route('/')
def index():
    return 'The server is running'
    
@app.route('/send-message', methods=['POST'])
def send_message():
    message_text = request.json.get('message')
    if not message_text:
        return jsonify({'error': 'Message text is empty'}), 400
    
    try:
        @stream_with_context
        def generate_response_stream():
            response = client.chat.completions.create( #poslanie requestu na azure openai api na odpoved modelu chatGPT-35-turbo s vlastnymi datami
                model = openai_model_name,
                stream=True,
                messages = [{"role": "system", "content": bot_system_message},
                            {"role": "user", "content": message_text}
                ],
                extra_body={
                    "data_sources": [
                        {
                            "type": "azure_search",
                            "parameters": {
                                "endpoint": "https://aivyhladavanie.search.windows.net", #neviem, preco nechce zobrat premennu search_endpoint?
                                "authentication": {
                                    "type": "api_key",
                                    "key": search_key
                                },
                                "index_name": "index2", #neberie premennu search_index?
                                "query_type": request.json.get('search_type'),
                                "embedding_dependency": {
                                    "type": "deployment_name",
                                    "deployment_name": "text-embedding-ada-002"
                                },
                                "fields_mapping": {
                                    "title_field": "title",
                                    "url_field": "url",
                                    "filepath_field": "filepath",
                                    "content_fields": ["content"],
                                    "vector_fields": ["contentVector"]
                                },
                            }
                        }
                    ]
                }
            )
            
            for event in response:
                if event.choices[0].delta.content is not None:
                    response_message = event.choices[0].delta.content
                    yield response_message
            
        return Response(generate_response_stream(), mimetype="application/json")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)