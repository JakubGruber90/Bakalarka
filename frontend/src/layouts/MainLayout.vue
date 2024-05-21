<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>

        <q-toolbar-title> <!--názov aplikácie-->
          ChatGPT RAG čet
        </q-toolbar-title>

        <q-btn class="layout-button" label="Výsledky testovania odpovedí" @click="showResults()"> <!--tlačidlo na otvorenie dialógu s výsledkami testovania-->
          <q-dialog v-model="resultDialog" maximized> <!--dialóg s výsledkami testovania-->
            <q-card>

              <q-card-actions align="right">

                <q-btn style="background-color: #91b6dc;" icon="help" fab-mini @click="graphHelp = true"> <!--tlačidlo na zobrazenie vysvetliviek ku grafu-->
                  <q-dialog v-model="graphHelp">
                    <q-card>
                      <q-card-section>
                        <span>Na grafe sa zobrazujú priemery metrík <b>vierohodnosť (faithfulness)</b>, <b>relevantnosť odpovede (answer_relevancy)</b>, <b>vyvolanie kontextu (context_recall)</b> a <b>presnosť kontextu (context_precision)</b> vypočítaných pomocou frameworku RAGAS rozdelené na skupiny podľa typu vyhľadávania v indexe.</span>
                      </q-card-section>

                      <q-card-actions align="center">
                        <q-btn style="background-color: #91b6dc;" label="OK" @click="graphHelp = false" />
                      </q-card-actions>
                    </q-card>
                    </q-dialog>
                </q-btn>

                <q-btn style="background-color: #91b6dc;" icon="close" fab-mini @click="resultDialog = false" />
              </q-card-actions>

              <q-card-section>
                <span style="font-size: 20px;" v-if="!evalQuestions">Nie sú vyhodnotené žiadne metriky otázok</span>
                <canvas v-else class="graph_canvas" ref="my_chart" width="100vw" height="35vh"></canvas> <!--canvas na graf z knižnice Chart.js-->
              </q-card-section>

            </q-card>
          </q-dialog>
        </q-btn>

        <q-btn class="layout-button" label="Nastavenia" icon="settings"> <!--tlačidlo na otvorenie nastavení-->
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
              <q-input outlined rounded label="Frekvenčná penalizácia (hodnoty -2 - 2)" min="-2" max="2" v-model.number="frequence_penalty" type="number"/><br>
              <q-input outlined rounded label="Maximum tokenov" v-model.number="max_tokens" type="number"/>

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

  data () { //premenné, slúžiace na zobrazovanie jednotlivých komponentov a ukladanie dočasných údajov za behu aplikácie
    return {
      search_type: 'Fulltext', //premenná nastavenia typu vyhľadávania v indexe, základná hodnota je Fulltext
      chat_with_data: 'true', //premenná nastavenia konverzácie s vlastnými dátami alebo bez nich, základná hodnota je true
      top_n_docs: 5, //premenná nastavenia počtu vrátených dokumentov z indexu, základná hodnota je 5 
      strictness: 3, //premenná nastavenia striktnosti posudzovania skóre dokuemntov, ktoré majú byť vrátené z indexu, základná hodnota je 3
      temperature: 1, //premenná nastavenia teploty pri generovaní odpovede, základná hodnota je 1
      presence_penalty: 0, //premenná nastavenia penalizácie nových tokenov, základná hodnota je 0
      frequence_penalty: 0, //premenná nastavenia penalizácie opakujúcich sa tokenov, základná hodnota je 0
      max_tokens: 3000, //premenná nastavenia množstva tokenov odpovede vygenerovanej jazykovým modelom, základná hodnota je 3000
      resultDialog: false, //premenná na otváranie/zatváranie dialógu s výsledkami testovania
      evalQuestions: false, //premenná na zistenie, či sú v databáze nejaké vyhodnotené otázky
      graphHelp: false, //premenná na otváranie/zatváranie dialógu s vysvetôivkami grafu
      //evalResults: [],
      //results: [], 
    }
  },

  methods: {
    async showResults() { //funkcia na zobrazenie dialógového okna s výsledkami 
      this.resultDialog = true; 
      
      try {
        const response = await fetch('http://127.0.0.1:5000/get-evaluated-questions', { //požiadavka na backkend navyžiadanie vyhodnotených otázok
          method: 'GET'
        });

        if (!response.ok) {
          throw new Error('Failed to fetch evaluated questions from the backend');
        }

        const responseData = await response.json();

        if (responseData.questions.length === 0) {
          this.evalQuestions = false;
          return
        } else {
          this.evalQuestions = true;
        }

        const dataByLabel = responseData.questions.reduce((accumulator: Record<string, Record<string, number[]>>, question: Question) => { 
          //priradenie označenia vyhodnoteným otázkam tak, že ich rozdelí na 3 skupiny podľa search_type
          let label = '';
          switch (question.search_type) { 
            case 'simple':
              label = 'Plnotextové vyhľadávanie';
              break;
            case 'vector':
              label = 'Vektorové vyhľadávanie'
              break;
            case 'vector_simple_hybrid':
              label = 'Hybridné vyhľadávanie';
              break;
          }

          if (!accumulator[label]) { //akumulátor v sebe postupne v každom cykle zbiera hodnoty jednotlivých metrík
            accumulator[label] = {
              faithfulness: [],
              relevancy: [],
              recall: [],
              precision: []
            };
          }
          accumulator[label].faithfulness.push(question.faithfulness); //vloženie hodnoty do príslušného poľa metriky a konkrétneho označenia
          accumulator[label].relevancy.push(question.answer_relevancy);
          accumulator[label].recall.push(question.context_recall);
          accumulator[label].precision.push(question.context_precision);
          return accumulator;
        }, {});

        const labels = Object.keys(dataByLabel);
        const avgFaithfulnessData = labels.map(label => this.calculateAverage(dataByLabel[label].faithfulness)); //vypočítanie priemerov pre jednotlivé metriky daného označenia
        const avgRelevancyData = labels.map(label => this.calculateAverage(dataByLabel[label].relevancy));
        const avgRecallData = labels.map(label => this.calculateAverage(dataByLabel[label].recall));
        const avgPrecisionData = labels.map(label => this.calculateAverage(dataByLabel[label].precision));

        this.$nextTick(() => { //počkanie na vykreslenie canvasu grafu, aby sa k nemu dalo pristupovať 
          const ctx = (this.$refs.my_chart as HTMLCanvasElement).getContext('2d');

          if (ctx !== null) {
            new Chart(ctx, { //naplnenie Chart.js stĺpcového grafu priemermy metrík zoskupených podľa typu vyhľadávania
              type: 'bar',
              data: {
                labels: labels,
                datasets: [
                  {
                    label: 'Vierohodnosť',
                    data: avgFaithfulnessData,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                  },
                  {
                    label: 'Relevantnosť odpovede',
                    data: avgRelevancyData,
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                  },
                  {
                    label: 'Vyvolanie kontextu',
                    data: avgRecallData,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                  },
                  {
                    label: 'Presnosť kontextu',
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
        });
      } catch (error) {
        console.error('Error fetching or processing data:', error);
      }
    },

    calculateAverage(array: number[]) { //pomocná funkcia na výpočet priemeru poľa hodnôt
      return array.reduce((sum: number, value: number) => sum + value, 0) / array.length;
    }
  },

  mounted() {
    const store = useChatStore();

    watch(() => this.chat_with_data, (newValue) => { //ak sa prepína medzi konverzáciou s dátami a bez, tak sa premaže história, aby sa mohla tvoriť nanovo
      store.deleteAllMessages();

      switch (newValue) { //zmena hodnoty changeChatWithData v store
        case 'true':
          store.changeChatWithData(true)
          break;
        case 'false':
          store.changeChatWithData(false)
          break;
      }
    });

    watch(() => this.search_type, (newValue) => {
      switch (newValue) { //zmena typu vyhľadávania v store
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

    watch(() => this.top_n_docs, (newValue) => { //ak je pole nastavení Top n dokumentov prázdne, tak ostane základná hodnota 5, inak sa zmení
      if (typeof(newValue) === 'string') {newValue = 5; this.top_n_docs = 5}
      store.changeTopNDocs(newValue);
    });

    watch(() => this.strictness, (newValue) => { //ak je pole stiktnosti prázdne ostane základná hodnota 3, inak sa zmení
      if (typeof(newValue) === 'string') {newValue = 3; this.strictness = 3}
      store.changeStrictness(newValue);
    });

    watch(() => this.temperature, (newValue) => { //ak je pole teploty prázdne alebo hodnota nie je v požadovanom rozmedzí ostane základná hodnota 1, inak sa zmení
      if (typeof(newValue) === 'string' || (newValue < 0 || newValue > 2)) {newValue = 1; this.temperature = 1}
      store.changeTemperature(newValue);
    });

    watch(() => this.presence_penalty, (newValue) => { //ak je pole prítomnostnej penalizácie prázdne alebo hodnota nie je v požadovanom rozmedzí ostane základná hodnota 0, inak sa zmení
      if (typeof(newValue) === 'string' || (newValue < -2 || newValue > 2)) {newValue = 0; this.presence_penalty = 0}
      store.changePresencePenalty(newValue);
    });

    watch(() => this.frequence_penalty, (newValue) => { //ak je pole frekvenčnej penalizácie prázdne alebo hodnota nie je v požadovanom rozmedzí ostane základná hodnota 0, inak sa zmení
      if (typeof(newValue) === 'string' || (newValue < -2 || newValue > 2)) {newValue = 0; this.frequence_penalty = 0}
      store.changeFrequencePenalty(newValue);
    });

    watch(() => this.max_tokens, (newValue) => { //ak je pole maxima tokenov prázdne ostane základná hodnota 3, inak sa zmení
      if (typeof(newValue) === 'string') {newValue = 3000; this.max_tokens = 3000}
      store.changeMaxTokens(newValue);
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
  height: 75.8%;
}
</style>