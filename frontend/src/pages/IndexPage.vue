<template>
  <q-page class="column items-center justify-evenly">

    <div v-if="!messagesPresent" class="no-messages">Nemáte žiadne správy. Skúste sa niečo opýtať.</div>
    <div class="message-container" ref="message_container"></div> <!--div zaobaľujúci sekciu správ-->

    <div class="input-evaluate-container"> <!--div zaobaľujúci vstupné pole pre správy, tlačidlo na odoslanie správ a tlačidlo na testovanie otázok-->
      <div class="input-container"> <!--div zaobaľujúci vstupné pole a tlačidlo na odosielanie-->
        <textarea class="user-input" ref="user_input" placeholder="Sem píšte..." required autofocus v-model="messageText" @keypress.enter.exact.prevent="sendMessage(true)"> <!--vstupné pole na písanie správ-->
        </textarea>
        <q-btn v-if="!isTesting && !isSending" class="send-button" round icon="send" :disable="messageText === ''" @click="sendMessage(true)" /> <!--tlačidlo na odoslanie správ-->
        <q-btn v-else class="send-button" round icon="stop" @click="cancelRequest()" /> <!--tlačidlo, ktoré sa zobrazí namiesto tlačidla odosielania správ alebo počas testovania na zastavenie týchto procesov-->
      </div>

      <q-btn v-if="!isTesting" class="evaluate-button" label="Vyhodnotiť odpovede" @click="openTestDialog()"> <!--tlačidlo na otvorenie dialógu testovania správ-->
        <q-dialog v-model="testDialog"> <!--dialógové menu testovania otázok-->
          <q-card class="evaluate-cards">
            
            <span style="font-size: 25px;">Odpovede budú testované na týchto otázkach (Zobrazené sú len otázky, ktoré nie sú vyhodnotené a môžu byť testované):</span>

            <hr style="height:1px;border:none;color:#333;background-color:#333;">

            <div v-if="questionsToEval.length === 0" style="display: flex; justify-content: center; font-size: 20px; margin: 30px">
              <span>V databáze nie sú žiadne otázky na testovanie</span>
            </div>

            <div v-else>
              <span>Počet otázok: {{ evalQuestionsLeft }}</span><br>

              <q-card-section v-for="(question, index) in questionsToEval" :key="index"> <!--vykreslenie otázok na testovanie z databázy-->
                {{ question.id }}.) {{ question.text }}
              </q-card-section>
            </div>

            <q-card-actions align="around">
              <q-btn class="test-button" @click="testDialog = false" label="Zrušiť" />
              <q-btn class="test-button" @click="openEditQuestions()" label="Upraviť otázky"/>
              <q-btn class="test-button" @click="ragasEvaluate()" label="Pokračovať" />
            </q-card-actions>

          </q-card>
        </q-dialog>
      </q-btn>

      <div v-else class="eval-questions-countdown"><span>Ostávajúce otázky: {{ evalQuestionsLeft }}</span></div> <!--ak prebieha testovanie, tak sa namiesto tlačidla "vyhodnotiť otázky" zobrazí počet ostávajúcich otázok na testovanie-->
    </div>

    <q-drawer 
        class="citation-area"
        v-model="citationsOpen"
        :width="300"
        bordered> <!--Drawer na zobrazovanie citacii k odpovediam-->
        <q-btn class="citation-close" icon="close" fab-mini @click="citationsOpen = ! citationsOpen" />
      <span style="font-size: 22px;"> Zdroj: </span>
      <span style="font-size: 28px;"> {{ citationHeading }} </span><br>
      <span> {{ citationContent }} </span>
    </q-drawer> <!--výsuvné menu na zobrazenie citovaných dokumentov-->
    
    <q-dialog v-model="editQuestions"> <!--dialóg slúžiaci na úpravu otázok v databáze-->
      <q-card class="evaluate-cards">

        <q-card-actions align="center" vertical>
          <span style="font-size: 20px;">Pridať otázku so správnou odpoveďou do testovacieho datasetu (musíte dodržať požadovaný formát z príkladu):</span>
          <q-input autogrow standout="bg-grey-4" class="add-questions-texarea" v-model="questionsToAdd" 
            placeholder=
          "Dodržte prosím formát <otázka> | <odpoveď>. Za koncom každej odpovede stlačte ENTER pre odriadkovanie.
            
          Príklad:
          Koľko je 2+2 | 2+2 je 4
          Akej farby je banán | banán je žltý 
          ..." /> <!--vstupné pole na pridávanie otázok do databázy -->
          <q-btn class="test-button" @click="addQuestion()" label="Pridať"/>
        </q-card-actions> 

        <hr style="height:1px;border:none;color:#333;background-color:#333;">

        <span style="font-size: 20px;">Otázky v databáze (aj vyhodnotené):</span>
        <div v-if="questionsAll.length === 0" style="display: flex; justify-content: center; font-size: 20px; margin: 30px">
          <span>V databáze nie sú žiadne otázky</span>
        </div>

        <div v-else>
          <span>Počet otázok: {{ questionsAll.length }}</span>

          <q-card-section v-for="(question, index) in questionsAll" :key="index">
            <div style="margin: 1%">{{ question.id }}.) {{ question.text }} 
              <span v-if="question.eval === 'evaluated'"><b>[VYHODNOTENÁ]</b>
              </span> <span v-if="question.eval === 'unanswered'"><b>[NEZODPOVEDANÁ]</b></span> 
              <q-btn fab-mini class="del-question-button" icon="delete" @click="deleteQuestion(question.id)" /></div><br><hr>
          </q-card-section> <!--vykreslenie otázok v databáze s údajom, či sú vyhodnotené alebo nezodpovedané. Otázky bez označenia neboli testované-->
        </div>

        <q-card-actions align="center">
          <q-btn class="test-button" @click="backToEvaluate()" label="Späť" /><br>
        </q-card-actions>

      </q-card>
    </q-dialog>

    <q-dialog persistent class="error-dialog" v-model="errDialog"> <!--dialóg na zobrazenie chýb-->
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
import { Message, Citation, Question } from 'src/components/models';

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
    cancelRequest() { //funkcia na zrušenie webovej požiadavky. Týka sa posielania správy jazykovému modelu a testovania.
      if (this.abortController) {
        this.abortController.abort();
        this.isSending = false;
        this.isTesting = false;
      }
    },

    async sendMessage(useHistory?: boolean) { //funkcia na vytvorenie správy a vyžiadanie odpovede jazykového modelu na správu 
      this.isSending = true; 

      if (this.messageText.trim() === '') { //ak je vstupné pole prázdne, funkcia sa nevykoná
        this.messageText = '';
        this.isSending = false;
        return;
      }

      this.messagesPresent = true;
      
      const store = useChatStore();

      const newMessage = document.createElement('div'); //vytvorenie divu, do ktorého sa vloží užívateľova správa
      newMessage.classList.add('message', 'user-message');
      const newMessageText = document.createTextNode(this.messageText);
      newMessage.appendChild(newMessageText);
      (this.$refs.message_container as HTMLDivElement).appendChild(newMessage);

      const botMessage = document.createElement('div'); //vytvorenie divu správy jazykového modelu
      botMessage.classList.add('message', 'bot-message');

      const loader = document.createElement('span');
      loader.classList.add('loader')

      botMessage.appendChild(loader); //kým sa začnú vkladať dáta jazykového modelu, tak sa ukáže načítavanie
      (this.$refs.message_container as HTMLDivElement).appendChild(botMessage);

      (this.$refs.user_input as HTMLInputElement).value = ''; //premazanie obsahu vstupného poľa
      this.messageText = '';

      this.abortController = new AbortController();

      try {
        const response = await fetch('http://127.0.0.1:5000/send-message', { //request na backend na vytvorenie odpovede jazykového modelu
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
            frequence_penalty: store.getFrequencePenalty,
            max_tokens: store.getMaxTokens,
          }),
          signal: this.abortController.signal
        });

        if (!response.ok) {
          console.log('SEND MESSAGE ERROR')
          const responseData = await response.json();
          botMessage.innerHTML = responseData.error;
          throw new Error('An error has occured on the backend.');
        }

        const botMessageContent = document.createElement('div');
        botMessage.removeChild(loader);
        botMessage.appendChild(botMessageContent);

        const reader = response.body?.getReader(); //vytvorenie premennej na čítanie dát streamovaných Azure OpenAI
        if (!reader) { throw new Error('ReadableStream not available');}
        let decoder = new TextDecoder();
      
        let citations = [] as Citation[];
        while (true) {
          const { done, value } = await reader?.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true }); //čítanie dát vrátených z backendu 
          const jsonStrings = chunk.split('/|/').filter(Boolean); //dáta sú ukončené špeciálnym znakom /|/, aby sa dali rozdeliť
          jsonStrings.forEach(jsonString => {
            const parsedChunk = JSON.parse(jsonString);

            if (parsedChunk.message) {
              botMessageContent.innerHTML += parsedChunk.message; //ak sú vrátené dáta odpoveďou jazykového modelu, tak sa vložia do obsahu divu správy jazykového modelu
            } else if (parsedChunk.context) {
              citations = parsedChunk.context.citations; //ak sú dáta citáciou, tak sú pridané do poľa citácií
            }
          });
        }

        this.currentAnswer = botMessageContent.innerHTML; //príprava údajov pre testovanie RAGAS na backende
        this.currentContexts = []
        citations.forEach(citation => {
          this.currentContexts.push(citation.content);
        })

        if (useHistory) { //tu sa zbierajú správy pre históriu do store, ak sa testuje, tak je história vypnutá
          if (store.getMessages.length > 10) { //vymazanie správ posledných dvoch správ, ak je ich viac ako 10
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
        }

        const citedDocs = botMessageContent.innerHTML?.match(/\[(doc\d\d?\d?)]/g); //regulárny výraz na nájdenie citovaných dokumentov v rámci odpovede modelu
        if (citedDocs && citedDocs.length > 0) { //pridavanie citacii po vlozeni sprav do store, aby neboli zahrnute v kontexte
          this.answerFound = true; 

          const uniqueCitedDocs = citedDocs?.filter((value, index, self) => { //filtrovanie jedinečných citácií v správe
            return self.indexOf(value) === index;
          })

          botMessageContent.innerHTML += '<br><hr>Zdroje:<br>';

          citations.forEach((citation, index) => { //vytvorenie klikateľných linkov s nadpisom a obsahom citovaného dokumentu
            if (uniqueCitedDocs?.includes(`[doc${index + 1}]`)) {
              const citationLink = document.createElement('a');
              citationLink.setAttribute('href', '#');
              citationLink.setAttribute('data-heading', citation.title);
              citationLink.setAttribute('data-content', citation.content);
              citationLink.addEventListener('click', this.citationClick);
              citationLink.textContent = `[doc${index + 1}] ${citation.filepath} časť${parseInt(citation.chunk_id) + 1}`;
              botMessageContent.appendChild(citationLink);
              botMessageContent.appendChild(document.createElement('br'));
            }
          });
        } else {
          this.answerFound = false; //ak v odpovedi nie sú citované zdroje, jazykový model nevedel vygenerovať odpoveď, lebo nenašiel nedostal potrebné dáta z indexu
        }

        this.isSending = false;

      } catch (error: unknown) { //zachytávanie chýb pri posielaní správy a ich vypísanie do tela správy
        if (error instanceof(DOMException) && error.name === 'AbortError') {
          botMessage.innerHTML = 'POSIELANIE ZRUSENE';
          this.isTesting = false;
          return;
        }
        console.log('SEND MESSAGE ERROR 2')
        let errorMessage: string;
        if (error instanceof Error) {
          errorMessage = error.message;
        } else {
          errorMessage = String(error);
        }

        botMessage.innerHTML = errorMessage;
        console.error(error);
      }
    },
    
    citationClick(event: MouseEvent) { //funkcia na otvorenie výsuvného menu s nadpisom a obsahom citácie
      event.preventDefault();
      this.citationsOpen = true;
      this.citationHeading = (event.target as HTMLElement).getAttribute('data-heading') || '';
      this.citationContent = (event.target as HTMLElement).getAttribute('data-content') || ''; 
    },

    async ragasEvaluate() { //funkcia na testovanie otázok z databázy frameworkom RAGAS
      this.testDialog = false;
      this.isTesting = true;

      let maxRetries = 6; //maximálny počet skúsení jednej otázky v prípade, že model nevygeneruje odpoveď
      let retryNum = 0;

      this.abortController = new AbortController();

      try {
        if (this.questionsToEval.length === 0) { //ak v databáze nie sú otázky, ktoré by sa dali testovať, tak testovanie neprebehne
          this.errDialogMessage = 'V databáze nie sú žiadne otázky, ktoré by sa dali testovať. Najprv do nej pridajte otázky.';
          this.errDialog = true;
          return
        }

        const store = useChatStore();
        let currentQuestionIndex = 0;

        while (currentQuestionIndex < this.questionsToEval.length) { //prechádzanie otázok na testovanie v cykle
          await new Promise(resolve => setTimeout(resolve, 20000));
          const question = this.questionsToEval[currentQuestionIndex];
          retryNum = 0;
          
          while (retryNum < maxRetries) {
            this.messageText = question.text;
            await this.sendMessage(false); //automatické poslanie správy a vyžiadanie odpovede jazykového modelu bez histórie
            
            if (!this.isTesting) {
              console.log('TESTING IS ABORTED')
              return;
            }

            if (this.currentContexts.length === 0 || !this.answerFound) { //ak na danú otázku nie sú kontexty, to znamená, že sa na ňu nenašla odpoveď, tak je poslaná znovu
              retryNum++;
              continue;
            }

            const postResponse = await fetch('http://127.0.0.1:5000/ragas-test', { //odoslanie dát na backend pre vyhodnotenie odpovede modelu RAGAsom
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                id: question.id,
                answer: this.currentAnswer,
                contexts: this.currentContexts,
                search_type: store.getType,
                top_n_documents: store.getTopNDocs,
                strictness: store.getStrictness,
                temperature: store.getTemperature,
                presence_penalty: store.getPresencePenalty,
                frequence_penalty: store.getFrequencePenalty,
              }),
              signal: this.abortController.signal
            });

            const responseData = await postResponse.json();

            if (postResponse.status === 429 && responseData.error === 'RateLimitError') { //ošetrenie chýb, ktoré môžu vzniknúť na backende
              console.log('RAGAS TEST RATE LIMIT ERROR')
              retryNum++;
              await new Promise(resolve => setTimeout(resolve, 20000));
              continue;
            } 
            else if (postResponse.status === 400 && responseData.error === 'BadRequestError') {
              console.log('RAGAS BAD REQUEST ERROR')
              retryNum++;
              await new Promise(resolve => setTimeout(resolve, 20000));
              continue;
            }
            else if (!postResponse.ok) {
              throw new Error('Failed to send data to the backend')
            }

            break;
          }

          if (retryNum === maxRetries) { //ak už sa naplnil maximálny počet opakovaní v snahe zodpovedat otázku, ale odpoveď sa aj tak nevygenerovala, tak sún search_type a nastavenia uložené do databázy, pre štatistiku nezodpovedaných otázok
            const response = await fetch('http://127.0.0.1:5000/save-unanswered-question-data', {
              method: 'POST',
              headers: {
                'Content-type': 'application/json',
              },
              body: JSON.stringify({
                id: question.id,
                search_type: store.getType,
                top_n_documents: store.getTopNDocs,
                strictness: store.getStrictness,
                temperature: store.getTemperature,
                presence_penalty: store.getPresencePenalty,
                frequence_penalty: store.getFrequencePenalty,
              })
            })

            if (!response.ok) {
              throw new Error('Failed to save unanswered question data to DB')
            }
          }
          
          this.evalQuestionsLeft--; //zníženie počtu otázok na testovanie a posunutie sa na ďalšiu
          currentQuestionIndex++;
        }

        this.isTesting = false;
      } catch (error) {
        if (error instanceof(DOMException) && error.name === 'AbortError') {
          console.log('TESTING ABORTED');
          return;
        }
        console.log('RAGAS TEST OTHER ERROR')
        console.log(error);
      }
    },

    async openTestDialog() { //funkcia na otvorenie dialógu testovania otázok
      try {
        const response = await fetch('http://127.0.0.1:5000/get-unevaluated-questions', { //požiadavka na backend o neotestované otázky
          method: 'GET',
        })

        if (!response.ok) {
          throw new Error('Failed to fetch questions from the backend');
        }

        const responseData = await response.json();
        this.questionsToEval = responseData.questions;
        this.evalQuestionsLeft = this.questionsToEval.length;

        this.testDialog = true;
      } catch (error) {
        console.log(error);
      }
    },

    async addQuestion() { //funkcia na pridanie otázky/otázok do databázy
      if (this.questionsToAdd.trim().length === 0) {
        this.errDialogMessage = 'Nezadali ste žiadne otázky a odpovede.'
        this.errDialog = true
        return;
      }
      
      const questions = this.questionsToAdd.split('\n'); //rozdelenie dvojíc otázka | odpoveď podľa newline character

      try {
        const responseAdd = await fetch('http://127.0.0.1:5000/add-questions', { //požiadavka na backend na pridanie otázok do databázy
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              questions: questions,
            }),
        })

        if (!responseAdd.ok) {
          throw new Error('Failed to add questions to DB');
        }

        const responseGet = await fetch('http://127.0.0.1:5000/get-all-questions', { //získanie otázok z databázy, aby sa aktualizoval ich zoznam v dialógovom okne pridávania otázok
          method: 'GET'
        })

        if (!responseGet.ok) {
          throw new Error('Failed to fetch questions');
        }

        const responseData = await responseGet.json();
        this.questionsAll = responseData.questions;        

      } catch (error) {
        console.log(error)
      }

      this.questionsToAdd = ''; //premazanie vstupného poľa otázok
    },

    async deleteQuestion(question: number) { //funkcia na vymazanie otázky z databázy
      try {
        const responseDel = await fetch('http://127.0.0.1:5000/del-question', { //požiadavka na backend o zmazanie otázky
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              question_id: question,
            }),
        })

        if (!responseDel.ok) {
          throw new Error('Failed to delete question from DB');
        }

        const responseGet = await fetch('http://127.0.0.1:5000/get-all-questions', { //získanie otázok z databázy, aby sa aktualizoval ich zoznam v dialógovom okne pridávania otázok
          method: 'GET'
        })

        if (!responseGet.ok) {
          throw new Error('Failed to fetch questions');
        }

        const responseData = await responseGet.json();
        this.questionsAll = responseData.questions;  
      } catch (error) {
        console.log(error)
      }
    },

    async openEditQuestions() { //funkcia na otvorenie dialógového okna pridávania otázok 
      try {
        const response = await fetch('http://127.0.0.1:5000/get-all-questions', { //získanie otázok z databázy, aby sa aktualizoval ich zoznam v dialógovom okne pridávania otázok
          method: 'GET'
        })

        if (!response.ok) {
          throw new Error('Failed to fetch questions');
        }

        const responseData = await response.json();
        this.questionsAll = responseData.questions; 
      } catch (error) {
        console.log(error);
      }

      this.testDialog = false;
      this.editQuestions = true;
    },

    async backToEvaluate() { //funkcia na získanie nevyhodnotených otázok z databázy pre dialógové okno testovania otázok
      try {
        const response = await fetch('http://127.0.0.1:5000/get-unevaluated-questions', {
          method: 'GET',
        })

        if (!response.ok) {
          throw new Error('Failed to fetch questions from the backend');
        }

        const responseData = await response.json();
        this.questionsToEval = responseData.questions;
        this.evalQuestionsLeft = this.questionsToEval.length;

        this.testDialog = true;
      } catch (error) {
        console.log(error);
      }

      this.editQuestions = false;
      this.testDialog = true;
    },
  },

  data () { //premenné, slúžiace na zobrazovanie jednotlivých komponentov a ukladanie dočasných údajov za behu aplikácie
    return {
      messageText: '', //text správy zo vstupného poľa na písanie správ
      citationsOpen: false, //premenná na otváranie/zatváranie citačného výsuvného menu
      citationHeading: '', //premenná na reaktívne vykreslenie nadpisu citácie
      citationContent: '', //premenná na reaktívne vykreslenie obsahu citácie
      messagesPresent: false, //premenná na zistenie, či sú viditeľné nejaké správy alebo nie 
      currentAnswer: '', //premenná na uloženie odpovede jazykového modelu pre funkciu ragasEvaluate()
      currentContexts: [] as string [], //premenná na uloženie kontextov pre funkciu ragasEvaluate()
      testDialog: false, //premenná na otváranie/zatváranie dialógu testovania otázok
      questionsToEval: [] as Question [], //premenná ukladajúca otázky, ktoré sú nevyhodnotené a majú byť testované
      evalQuestionsLeft: 0, //premenná na počítanie ostávajúcich otázok na testovanie
      isTesting: false, //premenná na zistenie, či prebieha testovanie alebo nie
      isSending: false, //premenná na zistenie, či je generovaná/posilaná správa
      questionsAll: [] as Question [], //premenná na uloženie všetkých otázok z databázy
      editQuestions: false, //premenná na otváranie/zatváranie dialógu úpravy otázok
      questionsToAdd: '', //premenná na uloženie otázok a odpovedí, ktoré sa majú vložiť do databázy
      errDialog: false, //premenná na otváranie/zatváranie dialógu na zobrazovanie chýb
      errDialogMessage: '', //správam, ktorú dialógové okno chýb vypíše
      answerFound: false, //premenná na zistenie, či bola otázka vygenerovaná alebo nie
      abortController: new AbortController(), //objekt na zastavovanie webových požiadaviek
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

.add-questions-texarea {
  width: 100%;
  max-height: 250px;
  overflow-y: auto;
  margin-bottom: 1%;
  padding: 0.5%;
}

.add-questions-texarea .q-field__control .q-field__native {
  color: rgb(0, 0, 0);
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
  background-color: #91b6dc;
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

.eval-questions-countdown {
  background-color: #91b6dc; 
  margin-left: 1%; 
  margin-top: 2%; 
  height: 70%; 
  border-radius: 10px; 
  padding: 1%;
  width: 190px;
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