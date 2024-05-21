import openai
import os
import json
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

#premenné na prístup k jazykovemu modelu cez azure openai api 
openai_endpoint_llm = os.getenv("AZURE_OPENAI_ENDPOINT_LLM")
openai_api_key_llm = os.getenv("AZURE_OPENAI_API_KEY_LLM")
openai_model_name_llm = os.getenv("AZURE_OPENAI_MODEL_NAME_LLM")

#premenné na prístup k modelu vytvárajúcemu vektory cez azure openai api 
openai_endpoint_em = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
openai_api_key_em = os.getenv("AZURE_OPENAI_EMBEDDING_KEY")
openai_embed_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")
openai_embed_resource = os.getenv("AZURE_OPENAI_EMBEDDING_RESOURCE")

openai_api_version = os.getenv("API_VERSION")

#premenne na pristup do azure ai search
search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
search_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
search_index = os.getenv("AZURE_AI_SEARCH_INDEX"),

#systémová správa pre jazykový model, kde sú inštrukcie, ako sa má správať
bot_system_message = '''Si užitočný asistent, ktorý odpovedá na otázky. Tu je niekoľko pravidiel, ktoré musíš dodržiavať: 
1. Odpovedaj na otázky v slovenskom jazyku. 
2. Používaj všetky potrebné diakritické znamienka v slovenskom jazyku.
3. Iný jazyk môžeš použiť len vtedy, ak je to nutné na správne odpovedanie na otázku, napríklad pri prekladaní.
''' 

#pripojenie na Azure OpenAI endpoint pre vykonavanie API volaní na generovanie odpovede v chate
llm_client = openai.AzureOpenAI( 
    azure_endpoint=openai_endpoint_llm,
    api_key=openai_api_key_llm,
    api_version=openai_api_version
)

#zadefinovanie, aký language model má RAGAS použiť pri testovaní
language_model = AzureChatOpenAI( 
    openai_api_version= openai_api_version,
    azure_endpoint= openai_endpoint_llm,
    api_key= openai_api_key_llm,
    model=openai_model_name_llm,
    validate_base_url=False,
)

#zadefinovanie, aký model vytvárajúci vektory má RAGAS použiť pri testovaní
embbed_model = AzureOpenAIEmbeddings( 
    openai_api_version=openai_api_version,
    azure_endpoint=openai_endpoint_em,
    api_key= openai_api_key_em,
    model=openai_embed_model,
)

app = Flask(__name__)

CORS(app) #nastavenie Cross Origin Resource sharingu pre aplikáciu, aby mohla posielať požiadavky aj mimo svojej domény

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'test.db')) #definovanie cesty k databázovému súboru
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}' #pripojenie sa na databázu

db = SQLAlchemy(app) #zadefinovanie ORM SQLAlchemy
migrate = Migrate(app, db) #zadefinovanie migrácií

#zadefinovanie štruktúry tabuľky otázok v databáze pre účel migrácií
class Questions(db.Model): 
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    search_type = db.Column(db.Text)
    text = db.Column(db.Text)
    answer = db.Column(db.Text)
    contexts = db.relationship('Contexts', backref='questions')
    ground_truth = db.Column(db.Text)
    faithfulness = db.Column(db.Integer)
    answer_relevancy = db.Column(db.Integer)
    context_recall = db.Column(db.Integer)
    context_precision = db.Column(db.Integer)
    top_n_documents = db.Column(db.Integer)
    strictness = db.Column(db.Integer)
    temperature = db.Column(db.Integer)
    presence_penalty = db.Column(db.Integer)
    frequence_penalty = db.Column(db.Integer)

#zadefinovanie štruktúry tabuľky kontextov v databáze pre účel migrácií
class Contexts(db.Model):
    __tablename__ = 'contexts'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))

@app.route('/') #koncový bod na otestovanie, či je server spustený
def index():
    return 'The server is running'

@stream_with_context #dekorátor funkcie, potrebný na streamovanie odpovede jazykového modelu po jednotlivých vygenerovaných tokenoch

#funkcia na vyžiadanie odpovede jazykového modelu cez azure openai api 
def generate_response_stream_without_data(message_list, tempr, pres_pen, freq_pen, max_tokens): 

                #poslanie requestu na azure openai api na odpoveď modelu chatGPT bez vlastných dát
                response = llm_client.chat.completions.create( 
                    model = openai_model_name_llm,
                    stream=True,
                    messages = message_list,
                    max_tokens = max_tokens,
                    temperature = tempr,
                    presence_penalty = pres_pen,
                    frequency_penalty = freq_pen,
                )
                    
                for chunk in response:
                    #print('\nEVENT:\n', chunk)
                    try:
                        if chunk.choices[0].delta.content is not None: 
                            response_message = chunk.choices[0].delta.content
                            yield json.dumps({'message': response_message})+'/|/' #odpvoveď sa po vygenerovaných častiach posiela na frontend
                    except Exception as e:
                        print('ERROR GETTING CONTENT FROM CHUNK: ', e)
                        
@stream_with_context #dekorátor funkcie, potrebný na streamovanie odpovede jazykového modelu po jednotlivých vygenerovaných tokenoch

#funkcia na vyžiadanie odpovede modelu cez azure openai api
def generate_response_stream_with_data(message_list, tempr, pres_pen, freq_pen, search_type, topNDocs, strict, max_tokens): 
    formated_embedding_endpoint = f'https://{openai_embed_resource}.openai.azure.com/openai/deployments/{openai_embed_model}/embeddings'
    
    #poslanie requestu na azure openai api na odpoveď modelu chatGPT s vlastnými dátami            
    response = llm_client.chat.completions.create( 
        model = openai_model_name_llm,
        stream=True, 
        messages = message_list,
        max_tokens= max_tokens,
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
                            "endpoint": formated_embedding_endpoint, 
                            "authentication": {
                                "type": "api_key",
                                "key": openai_api_key_em
                            },
                            "type": "endpoint",
                        },
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
                    
    for chunk in response: #posielanie vygenerovanej odpovede po častiach na frontend, ak nastane chyba, pošle sa chybová hláška
            try:
                if chunk.choices[0].delta.content is not None:
                    response_message = chunk.choices[0].delta.content
                    yield json.dumps({'message': response_message}) + '/|/' #possielanie odpovede na frontend
                if chunk.choices[0].delta.content is None and chunk.choices[0].delta.context is not None:
                    citations = chunk.choices[0].delta.context 
                    yield json.dumps({'context': citations}) + '/|/' #posielanie kontextu vyhľadaného v indexe na frontend
            except openai.RateLimitError as e:
                print('\nRATE LIMIT ERROR IN STREAMING RESPONSE WITH DATA:', e)
                yield json.dumps({'error': 'RateLimitError'}) + '/|/'
            except openai.BadRequestError as e:
                print('\nBAD REQUEST ERROR IN STREAMING RESPONSE WITH DATA:', e)
                yield json.dumps({'error': 'BadRequestError'}) + '/|/'
            except Exception as e:
                print('ERROR IN STREAMING RESPONSE WITH DATA:', str(e))
                yield json.dumps({'error': str(e)}) + '/|/'

@app.route('/send-message', methods=['POST']) #koncový bod na posielanie správy
def send_message():
    try:
        search_type = request.json.get('search_type') #vybranie jednotlivých parametrov z requestu
        use_own_data = request.json.get('own_data')
        topNDocs = request.json.get('topNDocs')
        strict = request.json.get('strictness')
        tempr = request.json.get('temperature')
        pres_pen = request.json.get('presence_penalty')
        freq_pen = request.json.get('frequence_penalty')
        max_tokens = request.json.get('max_tokens')
        user_query = request.json.get('message')
        if not user_query:
            return jsonify({'error': 'Message text is empty'}), 400
        
        message_history = request.json.get('history') 
        if len(message_history) > 0: #ak história existuje, tak modelu bude poslaný system message, história a užívateľova správa
            message_list = []
            
            message_list.append({"role": "system", "content": bot_system_message})
            
            for message in message_history:
                message_text = message.get('text')
                message_role = message.get('role')
                
                message_dict = {"role": message_role, "content": message_text}
                message_list.append(message_dict)
                
            message_list.append({"role": "user", "content": user_query})
        else: #inak história nie je a modelu sa pošle len system message a užívateľova požiadavka
            message_list = []
            
            message_list.append({"role": "system", "content": bot_system_message})
            message_list.append({"role": "user", "content": user_query})
            
        if use_own_data: #podľa toho, aký je mód konverzácie sa zavolá príslušná funkcia na vyžiadanie odpovede modelu
            return Response(generate_response_stream_with_data(
                message_list, tempr, pres_pen, freq_pen, search_type, topNDocs, strict, max_tokens), mimetype="application/json")
        else:
            return Response(generate_response_stream_without_data(
                message_list, tempr, pres_pen, freq_pen, max_tokens), mimetype="application/json")
            
    except openai.RateLimitError as e:
        print('\nRATE LIMIT ERROR OCCURRED\n', e)
        return jsonify({'error': 'RateLimitError'}), 429
    except openai.BadRequestError as e:
        print('\nBAD REQUEST ERROR SEND MESSAGE\n', e)
        return jsonify({'error': 'BadRequestError'}), 400
    except Exception as e:
        print('UNEXPECTED ERROR OCCURRED:', str(e))
        return jsonify({'error': str(e)}), 500
      
@app.route('/ragas-test', methods=['POST']) #koncový bod na testovanie rámcom RAGAS
def ragas_test():
    try:
       
        question_id = request.json.get('id')
        question = db.session.query(Questions).filter(Questions.id == question_id).first() #vyhľadanie konkrétnej otázky podľa id v databáze 
                
        question_text = question.text #uloženie hodnôt textu otázky, odpovede, kontextov a nastavení do premenných 
        answer = request.json.get('answer')
        contexts = request.json.get('contexts')
        search_type = request.json.get('search_type')
        top_n_docs = request.json.get('top_n_documents')
        strictness = request.json.get('strictness')
        temperature = request.json.get('temperature')
        presence_penalty = request.json.get('presence_penalty')
        frequence_penalty = request.json.get('frequence_penalty')
        ground_truth = question.ground_truth
        
        #vytvorenie vstupu pre ragas v podobe polí otázok, odpovedí, kontextov a správnych odpovedí                  
        data_samples = { 
            'question': [question_text],
            'answer': [answer],
            'contexts': [contexts], 
            'ground_truth': [ground_truth]
        }
                
        dataset = Dataset.from_dict(data_samples) #RAGAS vyźaduje ako vstup dataset v podobe tabuľky
        
        #funkcia, ktorá vyhodnotí zvolené metriky pre daný set dát
        result = evaluate( 
            dataset,
            llm= language_model,
            embeddings= embbed_model,
            metrics = [
                faithfulness, 
                answer_relevancy, 
                context_recall, 
                context_precision, 
            ]
        )
                
        question.answer = answer #uloženie jednotlivých hodnôt do stĺpcov v databáze 
        question.faithfulness = result['faithfulness']
        question.answer_relevancy = result['answer_relevancy']
        question.context_recall = result['context_recall']
        question.context_precision = result['context_precision']
        question.search_type = search_type
        question.top_n_documents = top_n_docs
        question.strictness = strictness
        question.temperature = temperature
        question.presence_penalty = presence_penalty
        question.frequence_penalty = frequence_penalty
            
        new_contexts = []
        for context in contexts: #uloženie kontextov odpovede do databázy
            new_contexts.append(Contexts(text=context, question_id=question.id))
                
        db.session.add_all(new_contexts)
        db.session.commit() #potvrdenie danej transakcie v databaźe, aby sa zmeny naozaj uložili
            
            
        return jsonify({'success': True})
    
    except openai.RateLimitError as e:
        print('WE RATE LIMIT ERRORIN')
        return jsonify({'error': 'RateLimitError'}), 429
    except openai.BadRequestError as e:
        print('\nBAD REQUEST ERROR RAGAS TEST\n')
        return jsonify({'error': 'BadRequestError'}), 400
    except Exception as e:
        db.session.rollback() #ak dôjde k nejakej chybe, zmeny v databáze sa vezmú späť
        print('Error saving data to DB: ', e)
        return jsonify({'error': 'UnknownError', 'message': str(e)}), 500

@app.route('/get-all-questions', methods=['GET']) #koncový bod na získanie všetkých otázok z databázy
def get_all_questions():
    try:
        questions_rows = db.session.query(Questions).all() #uloženie otázok z databázy do premennej cez SQLAlchemy ORM
        
        questions = []
        
        for row in questions_rows:
            is_evaluated = ''
            
            #rozhodovanie o stave otázky, teda či je vyhodnotená, nevyhodnotená alebo nezodpovedaná
            if ((row.answer == None and row.faithfulness == None and row.answer_relevancy == None and row.context_recall == None and row.context_precision == None) and (row.search_type == None and row.top_n_documents == None and row.strictness == None and row.temperature == None and row.presence_penalty == None and row.frequence_penalty == None)):
                
                is_evaluated = 'unevaluated' #ak otázka nemá v databáze uložené metriky ani typ vyhľadávania a nastavenia generovania a vyhľadávania, znamená to, že ešte nebola vyhodnotená RAGASom
                
            elif ((row.answer == None and row.faithfulness == None and row.answer_relevancy == None and row.context_recall == None and row.context_precision == None) and (row.search_type != None and row.top_n_documents != None and row.strictness != None and row.temperature != None and row.presence_penalty != None and row.frequence_penalty != None)):
                
                is_evaluated = 'unanswered' #ak otázka nemá v databáze uložené metriky, ale má uložený typ vyhľadávania a astavenia generovania a vyhľadávania, znamená to, že model na ňu nevedel odpovedať 
                
            else:
                is_evaluated = 'evaluated' #ak má otázka aj uložené metriky aj typ vyhľadávania a nastavenia, tak je vyhodnotená
            
            question_dict = {
                'id': row.id,
                'text': row.text,
                'eval': is_evaluated
            }
            
            questions.append(question_dict)
                
    except Exception as e:
        print('Error getting questions from DB: ', e)
    
    return jsonify({'questions': questions})

@app.route('/get-evaluated-questions', methods=['GET']) #koncový bod na získanie vyhodnotených otázok z databázy
def get_evaluated_questions():
    try:
        #vyfiltrovanie takých otázok z databázy, ktoré majú uložené hodnoty vyrátaných metrík
        questions_rows = db.session.query(Questions).\
            filter(Questions.answer.isnot(None)).\
            filter(Questions.faithfulness.isnot(None)).\
            filter(Questions.answer_relevancy.isnot(None)).\
            filter(Questions.context_recall.isnot(None)).\
            filter(Questions.context_precision.isnot(None)).all()  
        
        questions = []
        
        for row in questions_rows: #zostavenie slovníkov otázok aby sa z nich na frontende dali vyberať jednotlivé parametre
            question_dict = {
                'id': row.id,
                'text': row.text,
                'answer': row.answer,
                'ground_truth': row.ground_truth,
                'faithfulness': row.faithfulness,
                'answer_relevancy': row.answer_relevancy,
                'context_recall': row.context_recall,
                'context_precision': row.context_precision,
                'search_type': row.search_type,
            }
            
            questions.append(question_dict)
                
    except Exception as e:
        print('Error getting questions from DB: ', e)
        
    return jsonify({'questions': questions})

@app.route('/get-unevaluated-questions', methods=['GET']) #koncový bod na získanie nevyhodnotených otázok
def get_unevaluated_questions():
    try:
        #vyfiltrovanie otázok, ktoré nemajú uložené žiadne údaje okrem textu otázky a správnej odpovede = boli len vložené do databázy a neboli vyhodnotené
        questions_rows = db.session.query(Questions).\
            filter(Questions.answer.is_(None)).\
            filter(Questions.faithfulness.is_(None)).\
            filter(Questions.answer_relevancy.is_(None)).\
            filter(Questions.context_recall.is_(None)).\
            filter(Questions.context_precision.is_(None)).\
            filter(Questions.search_type.is_(None)).\
            filter(Questions.top_n_documents.is_(None)).\
            filter(Questions.strictness.is_(None)).\
            filter(Questions.temperature.is_(None)).\
            filter(Questions.presence_penalty.is_(None)).\
            filter(Questions.frequence_penalty.is_(None)).all()
                
        questions = []
        for row in questions_rows:
            question_dict = {
                'id': row.id,
                'text': row.text
            }
            
            questions.append(question_dict)
            
    except Exception as e:
        print('Error getting questions from DB: ', e)
        
    return jsonify({'questions': questions})

@app.route('/add-questions', methods=['POST']) #koncový bod na pridanie otázok do databázy
def add_questions():
    try:
        questionsArr = request.json.get('questions')
        
        for value in questionsArr: #ošetrenie zéeho rozdelenia otázky (v zadaných otázkach môžu byť \n navyše)
            if value == '':
                continue
            
            question_truth_pair = value.split(' | ') #rozdelenie dvojice otázka odpoveď na jednotlivé časti
            question_to_add = Questions(text=question_truth_pair[0], ground_truth=question_truth_pair[1])
            
            db.session.add(question_to_add) #pridanie do databázy
        
        db.session.commit() #uloženie transakcie
        
    except Exception as e:
        db.session.rollback()
        print('Error adding question to DB: ', e)
    
    return jsonify({'success': True})
        
@app.route('/del-question', methods=['POST']) #koncový bod na vymazanie otázky z databázy
def del_question():
    try:
        question_id = request.json.get('question_id') 
        question_to_del = db.session.query(Questions).filter(Questions.id == question_id).first() #nájdenie otázky v databáze pomocou id
        contexts_to_del = db.session.query(Contexts).filter(Contexts.question_id == question_to_del.id).all() #nájdenie kontextov k danej otázke pomocou id danej otázky
        
        db.session.delete(question_to_del) #vymazanie otázky z databázy
        if contexts_to_del: #postupné mazanie kontextov
            for context in contexts_to_del:
                db.session.delete(context)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print('Error deleting question from DB: ', e)
    
    return jsonify({'success': True})
    
@app.route('/save-unanswered-question-data', methods=['POST']) #koncový bod na uloženie dát nezodpovedanej otázky do databázy
def save_unanswered_question_data():
    try:
        question_id = request.json.get('id')
        question = db.session.query(Questions).filter(Questions.id == question_id).first() #vyhľadanie danej otázky podľa id
        
        search_type = request.json.get('search_type') #uloženie parametrov requestu do premenných
        top_n_docs = request.json.get('top_n_documents')
        strictness = request.json.get('strictness')
        temperature = request.json.get('temperature')
        presence_penalty = request.json.get('presence_penalty')
        frequence_penalty = request.json.get('frequence_penalty')
        
        question.search_type = search_type #zapísanie hodnôt jednotlivých premenných do ich stĺpca danej otázky
        question.top_n_documents = top_n_docs
        question.strictness = strictness
        question.temperature = temperature
        question.presence_penalty = presence_penalty
        question.frequence_penalty = frequence_penalty
        
        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        print('Error saving unanswered question data to DB: ', e)
    
    return jsonify({'success': True})
            
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)