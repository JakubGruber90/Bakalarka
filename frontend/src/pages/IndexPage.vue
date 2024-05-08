<template>
  <q-page class="column items-center justify-evenly">

    <div v-if="!messagesPresent" class="no-messages">Nemáte žiadne správy. Skúste sa niečo opýtať.</div>
    <div class="message-container" ref="message_container"></div>

    <div class="input-evaluate-container">
      <div class="input-container">
        <textarea class="user-input" ref="user_input" placeholder="Sem píšte..." required autofocus v-model="messageText" @keypress.enter.prevent="sendMessage">
        </textarea>
        <q-btn class="send-button" round icon="send" @click="sendMessage" />
      </div>

      <q-btn class="evaluate-button" label="Vyhodnotiť odpovede" @click="openTestDialog()">
        <q-dialog v-model="testDialog">
          <q-card class="evaluate-cards">
            
            <span style="font-size: 25px;">Odpovede budú testované na týchto otázkach:</span><hr>
            <div style="display: flex; justify-content: center; font-size: 20px; margin: 30px"><span v-if="questions.length === 0">V databáze nie sú žiadne otázky</span></div>
            <q-card-section v-for="(question, index) in questions" :key="index">
              {{ index+1 }}.) {{ question }}
            </q-card-section>

            <q-card-actions align="around">
              <q-btn class="test-button" @click="testDialog = false" label="Zrušiť" />
              <q-btn class="test-button" @click="editQuestions = true; testDialog = false" label="Upraviť otázky"/>
              <q-btn class="test-button" @click="ragasEvaluate()" label="Pokračovať" />
            </q-card-actions>

          </q-card>
        </q-dialog>
      </q-btn>      
    </div>

    <q-drawer 
        class="citation-area"
        v-model="citationsOpen"
        :width="300"
        bordered> 
        <q-btn class="citation-close" icon="close" fab-mini @click="citationsOpen = ! citationsOpen" />
      <span style="font-size: 22px;"> Zdroj: </span>
      <span style="font-size: 28px;"> {{ citationHeading }} </span><br>
      <span> {{ citationContent }} </span>
    </q-drawer>
    
    <q-dialog v-model="editQuestions">
      <q-card class="evaluate-cards">

        <q-card-actions align="center" vertical>
          <span style="font-size: 20px;">Pridať otázku so správnou odpoveďou do testovacieho datasetu:</span>
          <q-input outlined rounded style="width: 100%;" v-model="questionToAdd" label="Otázka"></q-input><br>
          <q-input outlined rounded style="width: 100%;" v-model="groundTruthToAdd" label="Správna Odpoveď"></q-input><br>
          <q-btn class="test-button" @click="addQuestion()" label="Pridať"/>
        </q-card-actions><hr>

        <div style="display: flex; justify-content: center; font-size: 20px; margin: 30px"><span v-if="questions.length === 0">V databáze nie sú žiadne otázky</span></div>
        <q-card-section v-for="(question, index) in questions" :key="index">
          <div style="margin: 1%">{{ index+1 }}.) {{ question }} <q-btn fab-mini class="del-question-button" icon="delete" @click="deleteQuestion(question)" /></div><br><hr>
        </q-card-section>

        <q-card-actions align="center">
          <q-btn class="test-button" @click="testDialog = true; editQuestions = false" label="Späť" /><br>
        </q-card-actions>

      </q-card>
    </q-dialog>

    <q-dialog persistent class="error-dialog" v-model="errDialog">
      <q-card>
        <q-card-section><Span>{{ errDialogMessage }}</Span></q-card-section>
        <q-card-actions align="center"><q-btn style="background-color: #91b6dc;" label="OK" @click="errDialog = false; errDialogMessage = ''" /></q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useChatStore} from 'stores/app_states';
import { Message, Citation } from 'src/components/models';

export default defineComponent({
  name: 'IndexPage',

  mounted() {
    const textarea = document.querySelector('textarea');
      textarea?.addEventListener('keyup', e => {
        if (e.target instanceof HTMLTextAreaElement) {
          textarea.style.height = '129px';
          let scHeight = e.target.scrollHeight;
          textarea.style.height = `${scHeight}px`;
        }
      });
  },

  methods: {
    async sendMessage() {
      this.messagesPresent = true;

      if (this.messageText === '') {
        return;
      }

      const store = useChatStore();

      const newMessage = document.createElement('div');
      newMessage.classList.add('message', 'user-message');
      const newMessageText = document.createTextNode(this.messageText);
      newMessage.appendChild(newMessageText);
      (this.$refs.message_container as HTMLDivElement).appendChild(newMessage);

      const botMessage = document.createElement('div');
      botMessage.classList.add('message', 'bot-message');

      const loader = document.createElement('span');
      loader.classList.add('loader')

      botMessage.appendChild(loader);
      (this.$refs.message_container as HTMLDivElement).appendChild(botMessage);

      (this.$refs.user_input as HTMLInputElement).value = '';
      this.messageText = '';

      try {
        const response = await fetch('http://127.0.0.1:5000/send-message', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            message: newMessageText.nodeValue, 
            search_type: store.getType, 
            history: store.getMessages, 
            own_data: store.getChatWithData, 
            topNDocs: store.getTopNDocs, 
            strictness: store.getStrictness, 
            temperature: store.getTemperature,
            presence_penalty: store.getPresencePenalty,
            frequence_penalty: store.getFrequencePenalty
          })
        });

        if (!response.ok) {
          throw new Error('Failed to get response from backend.');
        }

        const botMessageContent = document.createElement('div');
        botMessage.removeChild(loader);
        botMessage.appendChild(botMessageContent);

        const reader = response.body?.getReader();
        if (!reader) { throw new Error('ReadableStream not available');}
        let decoder = new TextDecoder();
      
        let citations = [] as Citation[];
        while (true) {
          const { done, value } = await reader?.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const jsonStrings = chunk.split('/|/').filter(Boolean);
          jsonStrings.forEach(jsonString => {
            const parsedChunk = JSON.parse(jsonString);

            if (parsedChunk.message) {
              if (parsedChunk.message === 'The requested information is not found in the retrieved data. Please try another query or topic.') {
                botMessageContent.innerHTML = 'Požadovaná informácia sa nenachádza vo Vašich dátach. Prosím skúste ďaľšiu otázku alebo tému.'
              } else {botMessageContent.innerHTML += parsedChunk.message;}
            } else if (parsedChunk.context) {
              citations = parsedChunk.context.citations;
            }
          });
        }

        this.currentAnswer = botMessageContent.innerHTML; //priprava udajov pre testovanie RAGAS na backende
        this.currentContexts = []
        citations.forEach(citation => {
          this.currentContexts.push(citation.content);
        })

        if (store.getMessages.length > 10) {
          store.deleteMessage();
          store.deleteMessage();
        }

        const userMessage: Message  = {
        text: newMessageText.nodeValue || '',
        role: 'user'
        };

        const botResponse: Message = {
          text: botMessageContent.innerHTML || '',
          role: 'assistant'
        }

        store.addMessage(userMessage);
        store.addMessage(botResponse);

        const cited_docs = botMessageContent.innerHTML?.match(/\[(doc\d\d?\d?)]/g);
        if (cited_docs && cited_docs.length > 0) { //pridavanie citacii po vlozeni sprav do store, aby neboli zahrnute v kontexte
          const unique_cited_docs = cited_docs?.filter((value, index, self) => {
            return self.indexOf(value) === index;
          })

          botMessageContent.innerHTML += '<br><br>Zdroje:<br>';

          citations.forEach((citation, index) => {
            if (unique_cited_docs?.includes(`[doc${index + 1}]`)) {
              const citationLink = document.createElement('a');
              citationLink.setAttribute('href', '#');
              citationLink.setAttribute('data-heading', citation.title);
              citationLink.setAttribute('data-content', citation.content);
              citationLink.addEventListener('click', this.citationClick);
              citationLink.textContent = `[doc${index + 1}] ${citation.filepath} part${parseInt(citation.chunk_id) + 1}`;
              botMessageContent.appendChild(citationLink);
              botMessageContent.appendChild(document.createElement('br'));
            }
          });
        }

      } catch (error) {
        console.error(error);
      }
    },
    
    citationClick(event: MouseEvent) {
      event.preventDefault();
      this.citationsOpen = true;
      this.citationHeading = (event.target as HTMLElement).getAttribute('data-heading') || '';
      this.citationContent = (event.target as HTMLElement).getAttribute('data-content') || ''; 
    },

    async ragasEvaluate() {
      try {
        const response = await fetch('http://127.0.0.1:5000/get-questions', {
          method: 'GET',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch questions from the backend');
        }

        const responseData = await response.json(); 

        if (!Array.isArray(responseData.questions)) {
          throw new Error('Questions data is not an array');
        }

        const questions: string[] = responseData.questions;

        if (questions.length === 0) { //ak v databaze nie su ziadne otazky, tak testovanie neprebehne
          this.errDialogMessage = 'V databáze nie sú žiadne otázky, ktoré by sa dali testovať. Najprv do nej pridajte otázky.';
          this.errDialog = true;
          return
        }

        for (const question of questions) {
          this.messageText = question;
          await this.sendMessage(); 

          const postResponse = await fetch('http://127.0.0.1:5000/ragas-test', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              question: question,
              answer: this.currentAnswer,
              contexts: this.currentContexts,
            }),
          });

          if (!postResponse.ok) {
            throw new Error('Failed to send data to the backend');
          }
        }
      } catch (error) {
        console.log(error);
      }
    },

    async openTestDialog() {
      try {
        const response = await fetch('http://127.0.0.1:5000/get-questions', {
          method: 'GET',
        })

        if (!response.ok) {
          throw new Error('Failed to fetch questions from the backend');
        }

        const responseData = await response.json();
        this.questions = responseData.questions;

        this.testDialog = true;
      } catch (error) {
        console.log(error);
      }
    },

    async addQuestion() {
      if (this.questionToAdd.trim().length === 0 || this.groundTruthToAdd.trim().length === 0) {
        this.errDialogMessage = 'Pole pre otázku alebo odpoveď je prázdne. Pre pridanie musíte zadať oboje.'
        this.errDialog = true
        return;
      }
      
      try {
        const responseAdd = await fetch('http://127.0.0.1:5000/add-question', { //volanie endpointu na pridanie otazky do DB
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              question: this.questionToAdd,
              ground_truth: this.groundTruthToAdd,
            }),
        })

        if (!responseAdd.ok) {
          throw new Error('Failed to add question to DB');
        }

        const responseGet = await fetch('http://127.0.0.1:5000/get-questions', { //ziskanie otazok z DB, aby sa aktualizoval ich zoznam v UI
          method: 'GET'
        })

        if (!responseGet.ok) {
          throw new Error('Failed to fetch questions');
        }

        const responseData = await responseGet.json();
        this.questions = responseData.questions;        

      } catch (error) {
        console.log(error)
      }

      this.questionToAdd = '';
      this.groundTruthToAdd = '';
    },

    async deleteQuestion(question: string) {
      try {
        const responseDel = await fetch('http://127.0.0.1:5000/del-question', { //volanie endpointu na odstranenie otazky z DB
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              question: question,
            }),
        })

        if (!responseDel.ok) {
          throw new Error('Failed to delete question from DB');
        }

        const responseGet = await fetch('http://127.0.0.1:5000/get-questions', { //ziskanie otazok z DB, aby sa aktualizoval ich zoznam v UI
          method: 'GET'
        })

        if (!responseGet.ok) {
          throw new Error('Failed to fetch questions');
        }

        const responseData = await responseGet.json();
        this.questions = responseData.questions;  
      } catch (error) {
        console.log(error)
      }
    },
  },

  data () {
    return {
      messageText: '',
      citationsOpen: false,
      citationHeading: '',
      citationContent: '',
      messagesPresent: false,
      currentAnswer: '',
      currentContexts: [] as string [],
      testDialog: false,
      questions: '',
      editQuestions: false,
      questionToAdd: '',
      groundTruthToAdd: '',
      errDialog: false,
      errDialogMessage: '',
    };
  }
});
</script>

<style>
.body {
  display: flex;
  flex-direction: column;
}

.evaluate-cards {
  overflow-y: auto;
  padding: 10px;
  min-width: 80vw;
  max-width: 90vw;
  max-height: 80vh;
}

.del-question-button {
  position: absolute;
  right: 0;
  background-color: #91b6dc;
}

.test-button {
  width: 30%;
  background-color: #91b6dc;
}

.no-messages {
  font-size: 20px;
  color: #627b94;
}

.citation-area {
  padding: 10px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

::-webkit-scrollbar {
  width: 10px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1; 
  border-radius: 10px;  
  margin-left: 5px;
}
 
::-webkit-scrollbar-thumb {
  background: #91b6dc; 
  border-radius: 10px;
  margin-left: 5px;
}

::-webkit-scrollbar-thumb:hover {
  background: #627b94; 
}

.citation-close {
  align-self: flex-end;
}

.input-evaluate-container {
  position: fixed;
  bottom: 0;
  margin-bottom: 1%;
  display: flex;
  flex-direction: row;
}

.input-container {
  width: 1200px;
  max-width: 100%;
  max-height: 25vh;
}

.user-input {
  width: 100%;
  resize: none;
  height: 125px;
  max-height: 180px;
  border-radius: 10px;
  padding: 10px;
  outline: none;
  font-size: 15px;
  border-color: black;
}

.user-input:is(:focus, :valid) {
  border-color: #34597e;
  border-width: 2px;
  padding: 9px;
}

.user-input::-webkit-scrollbar {
  display: none;
}

.send-button {
  margin: 5px;
  position: absolute;
  bottom: 15%;
  right: 15%;
  height: 12%;
  background-color: #91b6dc;
}

.evaluate-button {
  margin-left: 1%;
  margin-top: 2%;
  background-color: #91b6dc;
  height: 70%;
}

.message-container {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  position: fixed;
  bottom: 12vh;
  min-width: 65vw;  
  max-width: 65vw;
  min-height: 75vh;
  max-height: 75vh;
  overflow-y: auto;
  padding-bottom: 30px;
  padding-top: 18px;
  margin-bottom: 2%;
}

.message {
  background-color: #dddddd;
  border-radius: 10px;
  padding: 10px;
  margin: 10px;
  width: 50%;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.user-message {
  background-color: #91b6dc;
  align-self: flex-end;
  right: 0;
}

.bot-message {
  align-self: flex-start;
  left: 0;
}

.loader {
  margin-left: 30px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: #fff;
  box-shadow: 32px 0 #fff, -32px 0 #fff;
  position: absolute;
  animation: flash 0.5s ease-out infinite alternate;
}

@keyframes flash {
  0%, 100% {
    background-color: #91b6dc; /* First color */
    box-shadow: 32px 0 #91b6dc, -32px 0 #91b6dc;
  }
  33% {
    background-color: #1c3146; /* Second color */
    box-shadow: 32px 0 #1c3146, -32px 0 #34597e; 
  }
  66% {
    background-color: #34597e; /* Third color */
    box-shadow: 32px 0 #34597e, -32px 0 #1c3146;
  }
}
</style>