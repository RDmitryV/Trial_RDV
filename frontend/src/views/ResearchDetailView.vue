<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useResearchStore } from '@/stores/research'
import { useAnalysisStore } from '@/stores/analysis'
import { useToast } from 'primevue/usetoast'
import AppLayout from '@/components/common/AppLayout.vue'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import { ResearchStatus, AnalysisType } from '@/types'

const route = useRoute()
const router = useRouter()
const researchStore = useResearchStore()
const analysisStore = useAnalysisStore()
const toast = useToast()

const researchId = computed(() => route.params.id as string)

onMounted(async () => {
  try {
    await researchStore.fetchById(researchId.value)
    await analysisStore.fetchResults(researchId.value)
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Не удалось загрузить исследование',
      life: 5000,
    })
    router.push({ name: 'dashboard' })
  }
})

const research = computed(() => researchStore.currentResearch)
const results = computed(() => analysisStore.results)

const getStatusSeverity = (status: ResearchStatus) => {
  const severityMap = {
    [ResearchStatus.DRAFT]: 'secondary',
    [ResearchStatus.IN_PROGRESS]: 'info',
    [ResearchStatus.COMPLETED]: 'success',
    [ResearchStatus.FAILED]: 'danger',
  }
  return severityMap[status] || 'secondary'
}

const getStatusLabel = (status: ResearchStatus) => {
  const labelMap = {
    [ResearchStatus.DRAFT]: 'Черновик',
    [ResearchStatus.IN_PROGRESS]: 'В процессе',
    [ResearchStatus.COMPLETED]: 'Завершено',
    [ResearchStatus.FAILED]: 'Ошибка',
  }
  return labelMap[status] || status
}

const getAnalysisTypeLabel = (type: AnalysisType) => {
  const labelMap = {
    [AnalysisType.TREND]: 'Анализ трендов',
    [AnalysisType.REGIONAL]: 'Региональный анализ',
    [AnalysisType.COMPETITIVE]: 'Конкурентный анализ',
    [AnalysisType.MARKET]: 'Рыночный анализ',
  }
  return labelMap[type] || type
}

const startAnalysis = async () => {
  try {
    await researchStore.startAnalysis(researchId.value)
    toast.add({
      severity: 'info',
      summary: 'Запущено',
      detail: 'Анализ запущен, это может занять несколько минут',
      life: 5000,
    })
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Не удалось запустить анализ',
      life: 5000,
    })
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <AppLayout>
    <div class="p-4">
      <div v-if="research" class="flex flex-column gap-4">
        <!-- Header -->
        <Card>
          <template #content>
            <div class="flex justify-content-between align-items-start">
              <div class="flex-1">
                <h1 class="text-3xl font-bold mb-2">{{ research.title }}</h1>
                <div class="flex gap-2 mb-3">
                  <Tag
                    :value="getStatusLabel(research.status)"
                    :severity="getStatusSeverity(research.status)"
                  />
                  <Tag :value="research.industry" icon="pi pi-tag" severity="info" />
                  <Tag :value="research.region" icon="pi pi-map-marker" severity="success" />
                </div>
                <p class="text-600">{{ research.description }}</p>
              </div>
              <div class="flex gap-2">
                <Button
                  label="Запустить анализ"
                  icon="pi pi-play"
                  @click="startAnalysis"
                  :disabled="research.status === ResearchStatus.IN_PROGRESS"
                />
                <Button
                  icon="pi pi-arrow-left"
                  outlined
                  @click="router.push({ name: 'dashboard' })"
                />
              </div>
            </div>
          </template>
        </Card>

        <!-- Details -->
        <TabView>
          <TabPanel header="Информация">
            <Card>
              <template #content>
                <div class="flex flex-column gap-3">
                  <div>
                    <h3 class="text-lg font-semibold mb-2">Описание продукта/услуги</h3>
                    <p class="text-600">{{ research.product_description }}</p>
                  </div>
                  <div class="flex gap-4">
                    <div>
                      <span class="text-600">Создано:</span>
                      <span class="ml-2">{{ formatDate(research.created_at) }}</span>
                    </div>
                    <div>
                      <span class="text-600">Обновлено:</span>
                      <span class="ml-2">{{ formatDate(research.updated_at) }}</span>
                    </div>
                  </div>
                </div>
              </template>
            </Card>
          </TabPanel>

          <TabPanel header="Результаты анализа">
            <Card v-if="results.length === 0">
              <template #content>
                <div class="text-center py-5">
                  <i class="pi pi-chart-line text-5xl text-400 mb-3"></i>
                  <p class="text-xl mb-3">Результаты анализа пока отсутствуют</p>
                  <p class="text-600 mb-4">Запустите анализ, чтобы получить результаты</p>
                  <Button
                    label="Запустить анализ"
                    icon="pi pi-play"
                    @click="startAnalysis"
                  />
                </div>
              </template>
            </Card>

            <div v-else class="flex flex-column gap-3">
              <Accordion :multiple="true">
                <AccordionTab
                  v-for="result in results"
                  :key="result.id"
                  :header="result.title"
                >
                  <div class="flex flex-column gap-3">
                    <div class="flex justify-content-between align-items-center">
                      <Tag :value="getAnalysisTypeLabel(result.analysis_type)" />
                      <span class="text-sm text-600">{{ formatDate(result.created_at) }}</span>
                    </div>
                    <div>
                      <h4 class="mb-2">Резюме</h4>
                      <p class="text-600">{{ result.summary }}</p>
                    </div>
                    <div v-if="result.confidence_score">
                      <span class="text-600">Уверенность: </span>
                      <span class="font-semibold">
                        {{ Math.round(result.confidence_score * 100) }}%
                      </span>
                    </div>
                    <div>
                      <h4 class="mb-2">Детальные результаты</h4>
                      <pre class="surface-100 p-3 border-round overflow-auto">{{
                        JSON.stringify(result.results, null, 2)
                      }}</pre>
                    </div>
                  </div>
                </AccordionTab>
              </Accordion>
            </div>
          </TabPanel>

          <TabPanel header="Экспорт">
            <Card>
              <template #content>
                <div class="text-center py-5">
                  <i class="pi pi-file-export text-5xl text-400 mb-3"></i>
                  <p class="text-xl mb-3">Экспорт отчетов</p>
                  <p class="text-600 mb-4">
                    Функция экспорта в PDF и DOCX будет доступна в следующей фазе разработки
                  </p>
                  <div class="flex gap-2 justify-content-center">
                    <Button label="PDF" icon="pi pi-file-pdf" disabled />
                    <Button label="DOCX" icon="pi pi-file-word" disabled />
                  </div>
                </div>
              </template>
            </Card>
          </TabPanel>
        </TabView>
      </div>

      <div v-else class="flex flex-column gap-3">
        <Skeleton height="10rem" />
        <Skeleton height="20rem" />
      </div>
    </div>
  </AppLayout>
</template>
