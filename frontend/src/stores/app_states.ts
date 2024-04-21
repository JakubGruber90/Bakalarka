import { defineStore } from 'pinia';

export const useSearchTypeStore = defineStore('searchType', {
  state: () => {
    return {type: 'simple'};
  },

  actions: {
    changeType(new_type: 'simple' | 'vector' | 'vector_simple_hybrid') {
      this.type = new_type
    }
  },

  getters: {
    getType: (state) => state.type
  }
});