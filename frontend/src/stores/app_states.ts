import { defineStore } from 'pinia';
import { Message } from 'src/components/models';

export const useChatStore = defineStore('chatStore', {
  state: () => {
    return {
      search_type: 'simple',
      messages: [] as Message[],
      chat_with_data: true,
      top_n_documents: 5,
      strictness: 3,
      temperature: 1,
      presence_penalty: 0,
      frequence_penalty: 0,
    };
  },

  actions: {
    changeType(new_type: 'simple' | 'vector' | 'vector_simple_hybrid') {
      this.search_type = new_type
    },

    addMessage(message: Message) {
      this.messages.push(message);
    },

    deleteMessage() {
      this.messages.shift()
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
    }
  },

  getters: {
    getType: (state) => state.search_type,

    getMessages: (state) => state.messages,

    getChatWithData: (state) => state.chat_with_data,

    getTopNDocs: (state) => state.top_n_documents,

    getStrictness: (state) => state.strictness,

    getTemperature: (state) => state.temperature,

    getPresencePenalty: (state) => state.presence_penalty,

    getFrequencePenalty: (state) => state.frequence_penalty
  }
});