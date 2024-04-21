import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv("C:/FIIT_STU/bakalarka/Implementacia/moja_appka_quasar/.env")

client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
  api_version = os.getenv("API_VERSION"),
  azure_endpoint =os.getenv("AZURE_OPENAI_ENDPOINT") 
)

response = client.embeddings.create(
    input = "Your text string goes here",
    model= "text-embedding-ada-002"
)

embedding = response.data[0].embedding

print(embedding)