import { defineStore } from 'pinia';
import { Message } from 'src/components/models';

export const useChatStore = defineStore('chatStore', {
  state: () => {
    return {
      type: 'simple',
      messages: [] as Message[],
      chat_with_data: true
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
    },

    changeChatWithData(newValue: boolean) {
      this.chat_with_data = newValue;
    }
  },

  getters: {
    getType: (state) => state.type,

    getMessages: (state) => state.messages,

    getChatWithData: (state) => state.chat_with_data
  }
});