<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>

        <q-toolbar-title>
          ChatGPT RAG chat
        </q-toolbar-title>

        <q-toggle
        class="chatdata-toggle"
        v-model="chat_with_data"
        label="Chat with own data">
          <q-tooltip class="tooltip">
            Toggle between chatting with own data and without, default is own data enabled
            </q-tooltip>
        </q-toggle>

        <q-btn-dropdown
          auto-close
          v-model:label=selected_type
          class="search-type-button">
           
          <q-list>

            <q-item clickable v-close-popup v-for="item in search_types" :key="item.label" @click="selectSearchType(item.label)">
              <q-item-section>
                {{ item.label }}
              </q-item-section>
            </q-item>

          </q-list>

          <q-tooltip class="tooltip">
              Types of search for data retrieval
          </q-tooltip>

        </q-btn-dropdown>

      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script lang="ts">
import { defineComponent, watch } from 'vue';
import { useChatStore } from 'stores/app_states';

export default defineComponent({
  name: 'MainLayout',

  data () {
    return {
      search_types: [
        {label: 'Fulltext'},
        {label: 'Vector'},
        {label: 'Hybrid'}
      ],
      selected_type: 'Fulltext',
      chat_with_data: true,
    }
  },

  mounted() {
    const store = useChatStore();

    watch(() => this.chat_with_data, (newValue) => {
      store.changeChatWithData(newValue)
    })
  },

  methods: {
    selectSearchType (selection: string) {
      this.selected_type = selection;
      const store = useChatStore();

      switch (this.selected_type) {
        case 'Fulltext':
          store.changeType('simple');
          break;
        case 'Vector':
          store.changeType('vector');
          break;
        case 'Hybrid':
          store.changeType('vector_simple_hybrid');
          break;
      }
    }
  }
});
</script>

<style>
.chatdata-toggle {
  margin-right: 3%;
  font-size: 17px;
}

.q-toggle__thumb {
  color:#34597e;
}

.q-toggle__track {
  color:#34597e;
}

.search-type-button {
  width: 150px;
  max-width: 150px;
  min-width: 150px;
  background-color: #34597e;
}

.tooltip {
  background-color: #34597e;
}
</style>