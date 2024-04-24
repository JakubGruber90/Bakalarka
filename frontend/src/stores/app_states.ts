import { defineStore } from 'pinia';
import { Message } from 'src/components/models';

export const useChatStore = defineStore('chatStore', {
  state: () => {
    return {
      type: 'simple',
      messages: [] as Message[]
    };
  },

  actions: {
    changeType(new_type: 'simple' | 'vector' | 'vector_simple_hybrid') {
      this.type = new_type
    },

    addMessage(message: Message) {
      this.messages.push(message);
    },

    deleteMessage() {
      this.messages.shift()
    }
  },

  getters: {
    getType: (state) => state.type,

    getMessages: (state) => state.messages
  }
});