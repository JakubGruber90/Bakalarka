import os

from langchain_openai.chat_models import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings

from dotenv import load_dotenv

from ragas.metrics import (
    context_precision,
    context_recall,
    answer_relevancy,
    faithfulness, #rozbije otazku na podotazky a kontoroluje, ci sa odpoved na ne nachadza v kontexte
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

language_model = AzureChatOpenAI(
    openai_api_version= openai_api_version,
    azure_endpoint= openai_endpoint,
    model=openai_model_name,
    validate_base_url=False,
)

embbed_model = AzureOpenAIEmbeddings(
    openai_api_version=openai_api_version,
    azure_endpoint=openai_endpoint,
    model=openai_embbed_model,
)

data_samples = {
    'question': ['Koľko majú na Slovensku Slovenské elektrárne reaktorových blokov a kde sa tieto bloky nachádzajú?'],
    
    'answer': ['Slovenské elektrárne majú na Slovensku päť reaktorových blokov, dva v AE Bohunice a tri v AE Mochovce [doc1].]'],
    
    'contexts': [['<h1>Atómové elektrárne na Slovensku</h1>\nAtómové elektrárne sa na Slovensku využívajú už pol storočia a patria medzi nízkouhlíkové technológie, to znamená, že pri ich prevádzke sa do ovzdušia nevypúšťajú skleníkové plyny. Sú základnými piliermi energetickej siete na Slovensku.\nPäť reaktorových blokov - dva v AE Bohunice a ďalšie tri v AE Mochovce, dodáva takmer dve tretiny elektriny spotrebovanej na Slovensku.\nVšetky prevádzkované bloky majú tlakovodné reaktory VVER 440 s vysokou úrovňou bezpečnosti, ktorú zaisťuje robustný projekt s 1,5 m hrubou železobetónovou obálkou, tzv. kontejnmentom, veľké objemy vody na chladenie a trojnásobne zálohované pasívne a aktívne bezpečnostné systémy (3 x 100%) a spĺňajú najprísnejšie medzinárodné požiadavky na jadrovú bezpečnosť.\nNa všetkých blokoch sú zrealizované aj najnovšie opatrenia na zvládnutie tzv. ťažkých havárií.\n<h2>Ako funguje atómová elekráreň</h2>\nPrincíp výroby elektriny z jadrovej energie je podobný ako v klasickej tepelnej elektrárni. Rozdiel je len v zdroji tepla. V tepelnej elektrárni je zdrojom tepla fosílne palivo (uhlie, plyn), ktorých spaľovaním vzniká aj veľké množstvo skleníkových plynov, zatiaľ čo v jadrovej elektrárni je to jadrové palivo (prírodný alebo obohatený urán).\nV tlakovodných reaktoroch je palivo v podobe palivových kaziet umiestnené v tlakovej nádobe reaktora, do ktorej prúdi chemicky upravená voda. Táto preteká kanálikmi v palivových kazetách a odvádza teplo, ktoré vzniká pri štiepnej reakcii. Voda z reaktora vystupuje s teplotou asi 297℃ (pri reaktore typu VVER) a prechádza horúcou vetvou primárneho potrubia do tepelného výmenníka - parogenerátora. V parogenerátore preteká zväzkom trubiek a odovzdáva teplo vode, ktorá je privádzaná zo sekundárneho okruhu s teplotou 222℃. Ochladená voda primárneho okruhu sa vracia späť do aktívnej zóny reaktora. Voda sekundárneho okruhu sa v parogenerátore odparuje a cez parný kolektor sa para odvádza na lopatky turbíny', '<h2>Naše vodné elektrárne</h2>\nSumárny inštalovaný výkon vodných elektrární v portfóliu Slovenských elektrární je 1 653 MW, čo je približne 40 % z celkového inštalovaného výkonu Slovenských elektrární. Z toho je v prietočných vodných elektrárňach inštalovaných 736,6 MW a v prečerpávacích vodných elektrárňach 916,4 MW (Čierny Váh 734,4 MW, Liptovská Mara 98 MW, Dobšiná 24 MW a Ružín 60 MW). K tomu do 10. marca 2015 Slovenské elektrárne prevádzkovali VE Gabčíkovo s celkovým inštalovaným výkonom 746,54 MW a od tohto dňa prevádzku prevzal Vodohospodársky podnik, š.p.\nPodiel vodných elektrární na ročnej výrobe elektrickej energie Slovenských elektrární, a.s., dosahuje v priemere asi 11 %.\nNa výrobu elektrickej energie využívajú VE hydroenergetický potenciál našich tokov, ktorý je trvalo sa obnovujúcim, a preto nevyčerpateľným primárnym energetickým zdrojom - na rozdiel od všetkých druhov fosílnych palív. Vodné elektrárne - svojou prevádzkovou pružnosťou s možnosťou rýchlych zmien výkonov - sú schopné pokrývať prudko sa meniace požiadavky na výkon v špičkovej časti denného diagramu zaťaženia a tým sú vhodné aj na pokrývanie havarijných stavov v elektrizačnej sústave.\n<h2>Prečo sú nenahraditeľné?</h2>\nVodné elektrárne pri veľkých akumulačných nádržiach (napr. Orava, Liptovská Mara, Nosice, Kráľová) a prečerpávacie vodné elektrárne (napr. Čierny Váh, Liptovská Mara, Ružín, Dobšiná) vytvárajú zásobu vody na riešenie nerovnomernosti spotreby elektrickej energie v rámci dňa a tým pomáhajú presne dodržať obchodný plán dodávky elektrickej energie.\nVodné elektrárne sú vhodné ako regulačné alebo záložné zdroje v elektrizačnej sústave a sú vhodné aj z pohľadu využitia prvotných zdrojov energie, ktoré sa nachádzajú na našom území', '<h1>Firemné údaje Základné údaje</h1>\n<h2>Obchodné meno</h2>\nSlovenské elektrárne - energetické služby, s.r.o. Právna forma Spoločnosť s ručením obmedzeným, zapísaná v Obchodnom registri Mestského súdu Bratislava III, oddiel: Sro, Vložka č .: 56534/B\nDátum vzniku 4. 12. 2008\nSídlo\nPribinova 40, 811 09 Bratislava, Slovenská republika\nIČO\n44 553 412\nIČ DPH\nSK2022762621\nHlavný predmet podnikania\ndodávka elektriny, dodávka plynu, rozvod tepla, poskytovanie podpornej energetickej\nslužby\nÚdaje súvisiace s podnikaním\nElektroenergetika\npovolenie č. 2009E 0352 EIC 24X-SE-PREDAJ-H Bankové spojenie Tatra Banka, a.s. Číslo účtu 2626225307/1100 IBAN SK35 1100 0000 0026 26225307 BIC TATRSKBX']],
    
    'ground_truth': ['Päť reaktorových blokov - dva v AE Bohunice a ďalšie tri v AE Mochovce, dodáva takmer dve tretiny elektriny spotrebovanej na Slovensku.']
}

dataset = Dataset.from_dict(data_samples)

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

print(result) 

#Takyto je output:
# {'faithfulness': 1.0000, 'answer_relevancy': 0.9876, 'context_recall': 0.5000, 'context_precision': 1.0000}