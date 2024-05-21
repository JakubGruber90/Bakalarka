import { defineStore } from 'pinia';
import { Message } from 'src/components/models';

export const useChatStore = defineStore('chatStore', { //store na ukladanie stavov premenných pre zdieľanie medzi IndexPage a MainLayout
  state: () => {
    return {
      search_type: 'simple', //typ vyhľadávania
      messages: [] as Message[], //pole správ na udržiavanie histórie konverzácie
      chat_with_data: true, //nastavenia chattovania s vlastnými dátami
      top_n_documents: 5, //top n vrátených dokumentov z indexu
      strictness: 3, //striktnosť pri vyhľadávaní dokumentov v indexe
      temperature: 1, //teplota pri generovaní odpovede
      presence_penalty: 0, //penalizácia novo vytvorených tokenov podľa toho, či sa už nachádzajú vo vygenerovanej odpovedi
      frequence_penalty: 0, //penalizácia často opakovaných tokenov
      max_tokens: 3000, //maximálny počet tokenov, ktorý model môže v rámci odpovede vygenerovať
    };
  },

  actions: { //metódy meniace stav premenných
    changeType(new_type: 'simple' | 'vector' | 'vector_simple_hybrid') {
      this.search_type = new_type
    },

    addMessage(message: Message) {
      this.messages.push(message);
    },

    deleteMessage() {
      this.messages.shift()
    },

    deleteAllMessages() {
      this.messages = [];
    },

    changeChatWithData(newValue: boolean) {
      this.chat_with_data = newValue;
    },

    changeTopNDocs(newValue: number) {
      this.top_n_documents = newValue;
    },

    changeStrictness(newValue: number) {
      this.strictness = newValue;
    },

    changeTemperature(newValue: number) {
      this.temperature = newValue;
    },

    changePresencePenalty(newValue: number) {
      this.presence_penalty = newValue;
    },

    changeFrequencePenalty(newValue: number) {
      this.frequence_penalty = newValue;
    },

    changeMaxTokens(newValue: number) {
      this.max_tokens = newValue;
    }
  },

  getters: { //metódy vracajúce hodnoty premenných
    getType: (state) => state.search_type,

    getMessages: (state) => state.messages,

    getChatWithData: (state) => state.chat_with_data,

    getTopNDocs: (state) => state.top_n_documents,

    getStrictness: (state) => state.strictness,

    getTemperature: (state) => state.temperature,

    getPresencePenalty: (state) => state.presence_penalty,

    getFrequencePenalty: (state) => state.frequence_penalty,

    getMaxTokens: (state) => state.max_tokens,
  }
});