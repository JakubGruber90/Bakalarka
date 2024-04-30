import openai
import os
import json
from flask import Flask, Response, request, jsonify, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

load_dotenv()

bot_system_message = "You are a helpful assistant that answers questions." #sprava pre model, ako sa ma spravat

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
    search_type = request.json.get('search_type')
    
    user_query = request.json.get('message')
    if not user_query:
        return jsonify({'error': 'Message text is empty'}), 400
    
    message_history = request.json.get('history')
    if len(message_history) > 0:
        message_list = []
        
        message_list.append({"role": "system", "content": bot_system_message})
        
        for message in message_history:
            message_text = message.get('text')
            message_role = message.get('role')
            
            message_dict = {"role": message_role, "content": message_text}
            message_list.append(message_dict)
            
        message_list.append({"role": "user", "content": user_query})
    else:
        message_list = []
        
        message_list.append({"role": "system", "content": bot_system_message})
        message_list.append({"role": "user", "content": user_query})
    
    if request.json.get('own_data'):  
        try:
            @stream_with_context
            def generate_response_stream_with_data():
                
                if (search_endpoint[0] == 'https://aivyhladavanie.search.windows.net'):
                    print('\nSUCCESS\n')
                else:
                    print('\nWRONK: ', search_endpoint, type(search_endpoint), '\n')
                    print('\GUT: ', 'https://aivyhladavanie.search.windows.net', type('https://aivyhladavanie.search.windows.net'), '\n')
                    
                response = client.chat.completions.create( #poslanie requestu na azure openai api na odpoved modelu chatGPT-35-turbo s vlastnymi datami
                    model = openai_model_name,
                    stream=True,
                    messages = message_list,
                    extra_body={
                        "data_sources": [
                            {
                                "type": "azure_search",
                                "parameters": {
                                    "endpoint": search_endpoint[0],
                                    "authentication": {
                                        "type": "api_key",
                                        "key": search_key
                                    },
                                    "index_name": search_index[0],
                                    "query_type": search_type,
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
                    print('\nEVENT:\n', event)
                    if event.choices[0].delta.content is not None:
                        response_message = event.choices[0].delta.content
                        yield json.dumps({'message': response_message})+'/|/'
                        
                    try:
                        if event.choices[0].delta.content is None and event.choices[0].delta.context is not None:
                            citations = event.choices[0].delta.context                
                            yield json.dumps({'context': citations})+'/|/'
                    except Exception as err:
                        print('\nERROR GETTING CITATIONS: ', err, '\n')
                                    
            return Response(generate_response_stream_with_data(), mimetype="application/json")

        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            @stream_with_context
            def generate_response_stream_no_data():
                response = client.chat.completions.create(
                    model = openai_model_name,
                    stream=True,
                    messages = message_list,
                )
                
                for event in response:
                    print('\nEVENT:\n', event, '\n')
                    try:
                        if event.choices[0].delta.content is not None:
                            response_message = event.choices[0].delta.content
                            yield json.dumps({'message': response_message})+'/|/'
                    except Exception as err:
                        print('ERROR WITH CHUNK ON NO OWN DATA QUERY: ', err)
                        
                        
                                    
            return Response(generate_response_stream_no_data(), mimetype="application/json")

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)