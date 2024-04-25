<template>
  <q-page class="column items-center justify-evenly">

    <div class="message-container" ref="message_container"></div>

   <div class="input-container">
      <textarea class="user-input" ref="user_input" placeholder="Type here..." required autofocus v-model="messageText" @keypress.enter.prevent="sendMessage">
      </textarea>
      <q-btn class="send-button" round icon="send" @click="sendMessage" />
   </div>
    

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
          body: JSON.stringify({ message: newMessageText.nodeValue, search_type: store.getType, history: store.getMessages, own_data: store.getChatWithData })
        });

        if (!response.ok) {
          throw new Error('Failed to get response from backend.');
        }

        const botMessageText = document.createTextNode('');
        botMessage.removeChild(loader);
        botMessage.appendChild(botMessageText);

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
              botMessageText.nodeValue += parsedChunk.message;
            } else if (parsedChunk.context) {
              citations = parsedChunk.context.citations;
            }
          });
        }

        if (store.getMessages.length > 10) {
          store.deleteMessage();
          store.deleteMessage();
        }

        const userMessage: Message  = {
        text: newMessageText.nodeValue || '',
        role: 'user'
        };

        const botResponse: Message = {
          text: botMessageText.nodeValue || '',
          role: 'assistant'
        }

        store.addMessage(userMessage);
        store.addMessage(botResponse);

        if (citations.length > 0) {
          botMessageText.nodeValue += '\n\nSources:\n' //pridavanie citacii po vlozeni sprav do store, aby neboli zahrnute v kontexte

          citations.forEach((citation, index) => {
            botMessageText.nodeValue += `[doc${index + 1}] `+citation.filepath+'\n'
          });
        }

      } catch (error) {
        console.error(error);
      }
    }  
  },

  data () {
    return {
      messageText: '',
      isLoading: false
    };
  }
});
</script>

<style>
.body {
  display: flex;
  flex-direction: column;
}

.input-container {
  position: fixed;
  bottom: 0;
  width: 1250px;
  max-width: 100%;
  max-height: 25vh;
}

.user-input {
  width: 100%;
  resize: none;
  height: 125px;
  max-height: 180px;
  margin-bottom: 10px;
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
  bottom: 17%;
  right: 10px;
  height: 12%;
  background-color: #91b6dc;
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
  background-color: #f0f0f0;
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

.message-container::-webkit-scrollbar {
  width: 10px;
}

.message-container::-webkit-scrollbar-track {
  background: #f1f1f1; 
  border-radius: 10px;  
  margin-left: 5px;
}
 
.message-container::-webkit-scrollbar-thumb {
  background: #91b6dc; 
  border-radius: 10px;
  margin-left: 5px;
}

.message-container::-webkit-scrollbar-thumb:hover {
  background: #627b94; 
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