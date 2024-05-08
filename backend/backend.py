import openai
import os
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from flask import Flask, Response, request, jsonify, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_openai.chat_models import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from ragas.metrics import (
    context_precision,
    context_recall,
    answer_relevancy,
    faithfulness,
)
from ragas import evaluate
from datasets import Dataset

load_dotenv()

#premenne na pristup do openai api
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
openai_api_version = os.getenv("API_VERSION")
openai_embbed_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")

#premenne na pristup do azure ai search
search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
search_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
search_index = os.getenv("AZURE_AI_SEARCH_INDEX"),

bot_system_message = '''You are a helpful assistant that answers questions. Here are some rules for you to follow: 
1. Always answer in the Slovak language. 
2. Use all neccessary diacritics. 
3. Do not use english language except when it is neccessary like when explaining code or when there are english words in your input data. 
''' #sprava pre model, ako sa ma spravat

client = openai.AzureOpenAI( #pripojenie na Azure OpenAI endpoint pre vykonavanie API calls na generovanie odpovedi v chate
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key,
    api_version=openai_api_version
)

language_model = AzureChatOpenAI( #zadefinovanie, aky language model ma RAGAS pouzit
    openai_api_version= openai_api_version,
    azure_endpoint= openai_endpoint,
    model=openai_model_name,
    validate_base_url=False,
)

embbed_model = AzureOpenAIEmbeddings( #zadefinovanie, aky embedding model ma RAGAS pouzit
    openai_api_version=openai_api_version,
    azure_endpoint=openai_endpoint,
    model=openai_embbed_model,
)

app = Flask(__name__)

CORS(app)

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'ragas_test_database.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Questions(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    answer = db.Column(db.Text)
    contexts = db.relationship('Contexts', backref='questions')
    ground_truth = db.Column(db.Text)
    faithfulness = db.Column(db.Integer)
    answer_relevancy = db.Column(db.Integer)
    context_recall = db.Column(db.Integer)
    context_precision = db.Column(db.Integer)

class Contexts(db.Model):
    __tablename__ = 'contexts'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))

@app.route('/')
def index():
    return 'The server is running'
    
@app.route('/send-message', methods=['POST'])
def send_message():
    search_type = request.json.get('search_type')
    use_own_data = request.json.get('own_data')
    topNDocs = request.json.get('topNDocs')
    strict = request.json.get('strictness')
    tempr = request.json.get('temperature')
    pres_pen = request.json.get('presence_penalty')
    freq_pen = request.json.get('frequence_penalty')
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
      
    try:
        @stream_with_context
        def generate_response_stream_with_data():    
            response = client.chat.completions.create( #poslanie requestu na azure openai api na odpoved modelu chatGPT-35-turbo s vlastnymi datami
                model = openai_model_name,
                stream=True,
                messages = message_list,
                temperature = tempr,
                presence_penalty = pres_pen,
                frequency_penalty = freq_pen,
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
                                "in_scope": use_own_data,
                                "top_n_documents": topNDocs, 
                                "strictness": strict, 
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
                
            for chunk in response:
                print('\nEVENT:\n', chunk)
                if chunk.choices[0].delta.content is not None:
                    response_message = chunk.choices[0].delta.content
                    yield json.dumps({'message': response_message})+'/|/'
                        
                try:
                    if chunk.choices[0].delta.content is None and chunk.choices[0].delta.context is not None:
                        citations = chunk.choices[0].delta.context                
                        yield json.dumps({'context': citations})+'/|/'
                except Exception as err:
                    print('\nERROR GETTING CITATIONS: ', err, '\n')
                                    
        return Response(generate_response_stream_with_data(), mimetype="application/json")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ragas-test', methods=['POST'])
def ragas_test():
    try:
        @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(6), retry=retry_if_exception_type(openai.RateLimitError))
        def save_data_to_db():
            question_text = request.json.get('question')
            question = db.session.query(Questions).filter(Questions.text == question_text).first()
                
            answer = request.json.get('answer')
            contexts = request.json.get('contexts')
            ground_truth = question.ground_truth
                            
            data_samples = {
                'question': [question_text],
                'answer': [answer],
                'contexts': [contexts], 
                'ground_truth': [ground_truth]
            }
                
            dataset = Dataset.from_dict(data_samples)
            result = evaluate(
                dataset,
                llm= language_model,
                embeddings= embbed_model,
                metrics = [
                    faithfulness, #meria vecný súlad vygenerovanej odpovede s daným kontextom. Vygenerovaná odpoveď sa považuje za vernú, ak všetky tvrdenia, ktoré sú v odpovedi uvedené, možno odvodiť z daného kontextu. Na výpočet sa najprv identifikuje množina tvrdení z vygenerovanej odpovede. Potom sa každé z týchto tvrdení porovná s daným kontextom, aby sa určilo, či sa dá z daného kontextu odvodiť, alebo nie.
                    answer_relevancy, #Metrika hodnotenia, Relevancia odpovede, sa zameriava na posúdenie toho, do akej miery je vygenerovaná odpoveď relevantná k danej otázke. Nižšie skóre sa prideľuje odpovediam, ktoré sú neúplné alebo obsahujú nadbytočné informácie, a vyššie skóre znamená lepšiu relevantnosť. Odpoveď sa považuje za relevantnú, ak priamo a vhodne reaguje na pôvodnú otázku. Dôležité je, že pri posudzovaní relevantnosti odpovede neberieme do úvahy fakticitu, ale penalizujeme prípady, keď odpoveď nie je úplná alebo obsahuje nadbytočné údaje. Na výpočet tohto skóre je LLM vyzvaný, aby viackrát vygeneroval vhodnú otázku pre vygenerovanú odpoveď, a meria sa priemerná kosínusová podobnosť medzi týmito vygenerovanými otázkami a pôvodnou otázkou. Základnou myšlienkou je, že ak vygenerovaná odpoveď presne odpovedá na pôvodnú otázku, LLM by mal byť schopný z odpovede vygenerovať otázky, ktoré sú v súlade s pôvodnou otázkou.
                    context_recall, #Spätná väzba kontextu meria, do akej miery sa načítaný kontext zhoduje s anotovanou odpoveďou. Na odhad vyvolania kontextu zo základnej pravdivej odpovede sa každá veta v základnej pravdivej odpovedi analyzuje s cieľom určiť, či ju možno priradiť k vyhľadanému kontextu alebo nie. V ideálnom prípade by sa všetky vety v základnej pravdivej odpovedi mali priradiť k vyhľadanému kontextu.
                    context_precision, #Presnosť kontextu je metrika, ktorá hodnotí, či sú všetky základné pravdivé relevantné položky prítomné v kontextoch zaradené vyššie alebo nie. V ideálnom prípade sa všetky relevantné časti musia objaviť na najvyšších priečkach.
                ]
            )
                
            question.answer = answer
            question.faithfulness = result['faithfulness']
            question.answer_relevancy = result['answer_relevancy']
            question.context_recall = result['context_recall']
            question.context_precision = result['context_precision']
                
            contexts_json = json.dumps(contexts)
            new_context = Contexts(text=contexts_json, question_id=question.id)
            db.session.add(new_context)
                
            db.session.commit()
            
        save_data_to_db()
            
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print('Error saving data to DB: ', e)

@app.route('/get-questions', methods=['GET'])
def get_questions():
    try:
        questions_rows = db.session.query(Questions.text).all()
        questions_text = [row.text for row in questions_rows]
    except Exception as e:
        print('Error getting questions from DB: ', e)
        
    return jsonify({'questions': questions_text})

@app.route('/add-question', methods=['POST'])
def add_question():
    try:
        question_text = request.json.get('question')
        ground_truth_text = request.json.get('ground_truth')
        
        question_to_add = Questions(text=question_text, ground_truth=ground_truth_text)
        db.session.add(question_to_add)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print('Error adding question to DB: ', e)
    
    return jsonify({'success': True})
        
@app.route('/del-question', methods=['POST'])
def del_question():
    try:
        question_to_del_text = request.json.get('question')
        question_to_del = db.session.query(Questions).filter(Questions.text == question_to_del_text).first()
        contexts_to_del = db.session.query(Contexts).filter(Contexts.question_id == question_to_del.id).all()
        
        db.session.delete(question_to_del)
        if contexts_to_del:
            db.session.delete(contexts_to_del)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print('Error deleting question from DB: ', e)
    
    return jsonify({'success': True})
    
            
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)