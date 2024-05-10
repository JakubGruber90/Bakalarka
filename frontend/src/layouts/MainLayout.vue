<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>

        <q-toolbar-title>
          ChatGPT RAG čet
        </q-toolbar-title>

        <q-btn class="layout-button" label="Výsledky testovania odpovedí" @click="resultDialog = true">
          <q-dialog v-model="resultDialog" maximized>
            <q-card>

              <q-card-actions align="right">
                <q-btn style="background-color: #91b6dc;" icon="close" fab-mini @click="resultDialog = false" />
              </q-card-actions>

              <q-card-section>
                <!--<span style="font-size: 20px" v-if="evalResults.length === 0">Nie sú otestované žiadne výsledky</span>-->
                <q-btn label="Ukázať graf" @click="showResults()" /><br>
                <canvas ref="my_chart" width="800" height="200"></canvas>
              </q-card-section>

            </q-card>
          </q-dialog>
        </q-btn>

        <q-btn class="layout-button" label="Nastavenia" icon="settings"> 
          <q-popup-proxy class="settings-menu"> 
            <q-card>

            <q-card-section> 
              <span><b>Nastavenia vyhľadávania</b></span><hr>

              <q-input outlined rounded label="Top n vrátených dokumentov" v-model.number="top_n_docs" type="number" /><br>
              <q-input outlined rounded label="Striktnosť" v-model.number="strictness" type="number" /><br>

              <span>Typ vyhľadávania v indexe:</span><br>
              <q-radio v-model="search_type" val="Fulltext" label="Plnotextové" />
              <q-radio v-model="search_type" val="Vector" label="Vektorové" />
              <q-radio v-model="search_type" val="Hybrid" label="Hybridné" /><br>

              <span>Četovať s vlasnými dátami:</span><br>
              <q-radio v-model="chat_with_data" val="true" label="Áno" />
              <q-radio v-model="chat_with_data" val="false" label="Nie" />

            </q-card-section>

            <hr style="height:1px;border:none;color:#333;background-color:#333;">

            <q-card-section>
              <span><b>Nastavenia generovania</b></span><hr>

              <q-input outlined rounded label="Teplota (hodnoty 0 - 2)" min="0" max="2" v-model.number="temperature" type="number"/><br>
              <q-input outlined rounded label="Prítomnostná penalizácia (hodnoty -2 - 2)" min="-2" max="2" v-model.number="presence_penalty" type="number"/><br>
              <q-input outlined rounded label="Frekvenčná penalizácia (hodnoty -2 - 2)" min="-2" max="2" v-model.number="frequence_penalty" type="number"/>

            </q-card-section>

            </q-card>
          </q-popup-proxy>
        </q-btn>

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
import { Question } from 'src/components/models';
import { Chart } from 'chart.js/auto';


export default defineComponent({
  name: 'MainLayout',

  data () {
    return {
      search_type: 'Fulltext',
      chat_with_data: 'true',
      top_n_docs: 5,
      strictness: 3,
      temperature: 1,
      presence_penalty: 0,
      frequence_penalty: 0,
      results: [],
      resultDialog: false,
      evalResults: [],
    }
  },

  methods: {
    async showResults() {
      try {
        const response = await fetch('http://127.0.0.1:5000/get-evaluated-questions', {
          method: 'GET'
        });

        if (!response.ok) {
          throw new Error('Failed to fetch evaluated questions from the backend');
        }

        const responseData = await response.json(); console.log(responseData);

        const dataByLabel = responseData.questions.reduce((accumulator: Record<string, Record<string, number[]>>, question: Question) => {
          const label = question.search_type;
          if (!accumulator[label]) {
            accumulator[label] = {
              faithfulness: [],
              relevancy: [],
              recall: [],
              precision: []
            };
          }
          accumulator[label].faithfulness.push(question.faithfulness);
          accumulator[label].relevancy.push(question.answer_relevancy);
          accumulator[label].recall.push(question.context_recall);
          accumulator[label].precision.push(question.context_precision);
          return accumulator;
        }, {});

        const labels = Object.keys(dataByLabel);
        const avgFaithfulnessData = labels.map(label => this.calculateAverage(dataByLabel[label].faithfulness));
        const avgRelevancyData = labels.map(label => this.calculateAverage(dataByLabel[label].relevancy));
        const avgRecallData = labels.map(label => this.calculateAverage(dataByLabel[label].recall));
        const avgPrecisionData = labels.map(label => this.calculateAverage(dataByLabel[label].precision));

        const ctx = (this.$refs.my_chart as HTMLCanvasElement).getContext('2d');

        if (ctx !== null) {
          new Chart(ctx, {
            type: 'bar',
            data: {
              labels: labels,
              datasets: [
                {
                  label: 'Faithfulness',
                  data: avgFaithfulnessData,
                  backgroundColor: 'rgba(75, 192, 192, 0.2)',
                  borderColor: 'rgba(75, 192, 192, 1)',
                  borderWidth: 1
                },
                {
                  label: 'Answer Relevancy',
                  data: avgRelevancyData,
                  backgroundColor: 'rgba(255, 99, 132, 0.7)',
                  borderColor: 'rgba(255, 99, 132, 1)',
                  borderWidth: 1
                },
                {
                  label: 'Context Recall',
                  data: avgRecallData,
                  backgroundColor: 'rgba(54, 162, 235, 0.7)',
                  borderColor: 'rgba(54, 162, 235, 1)',
                  borderWidth: 1
                },
                {
                  label: 'Context Precision',
                  data: avgPrecisionData,
                  backgroundColor: 'rgba(255, 206, 86, 0.7)',
                  borderColor: 'rgba(255, 206, 86, 1)',
                  borderWidth: 1
                }
              ]
            },
            options: {
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }
          });
        }
      } catch (error) {
        console.error('Error fetching or processing data:', error);
      }
    },

    calculateAverage(array: number[]) {
      return array.reduce((sum: number, value: number) => sum + value, 0) / array.length;
    }
  },

  mounted() {
    const store = useChatStore();

    watch(() => this.chat_with_data, (newValue) => {
      store.deleteAllMessages();

      switch (newValue) {
        case 'true':
          store.changeChatWithData(true)
          break;
        case 'false':
          store.changeChatWithData(false)
          break;
      }
    });

    watch(() => this.search_type, (newValue) => {
      switch (newValue) {
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
    });

    watch(() => this.top_n_docs, (newValue) => {
      if (typeof(newValue) === 'string') {newValue = 5; this.top_n_docs = 5}
      store.changeTopNDocs(newValue);
    });

    watch(() => this.strictness, (newValue) => {
      if (typeof(newValue) === 'string') {newValue = 3; this.strictness = 3}
      store.changeStrictness(newValue);
    });

    watch(() => this.temperature, (newValue) => {
      if (typeof(newValue) === 'string' || (newValue < 0 || newValue > 2)) {newValue = 1; this.temperature = 1}
      store.changeTemperature(newValue);
    });

    watch(() => this.presence_penalty, (newValue) => {
      if (typeof(newValue) === 'string' || (newValue < -2 || newValue > 2)) {newValue = 0; this.presence_penalty = 0}
      store.changePresencePenalty(newValue);
    });

    watch(() => this.frequence_penalty, (newValue) => {
      if (typeof(newValue) === 'string' || (newValue < -2 || newValue > 2)) {newValue = 0; this.frequence_penalty = 0}
      store.changeFrequencePenalty(newValue);
    });
  },
});
</script>

<style>

.layout-button {
  margin-right: 1%;
  background-color: #34597e;
}

.settings-menu {
  width: 20%;
  height: 70.1%;
}
</style>