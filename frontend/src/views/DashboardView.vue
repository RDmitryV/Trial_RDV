<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useResearchStore } from '@/stores/research'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Card from 'primevue/card'
import Skeleton from 'primevue/skeleton'
import { ResearchStatus } from '@/types'

const router = useRouter()
const researchStore = useResearchStore()
const authStore = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

// Stats computed properties
const totalResearches = computed(() => researchStore.researches.length)
const draftCount = computed(() => researchStore.researches.filter(r => r.status === ResearchStatus.DRAFT).length)
const inProgressCount = computed(() => researchStore.researches.filter(r => r.status === ResearchStatus.IN_PROGRESS).length)
const completedCount = computed(() => researchStore.researches.filter(r => r.status === ResearchStatus.COMPLETED).length)

onMounted(() => {
  loadResearches()
})

const loadResearches = async () => {
  try {
    await researchStore.fetchAll()
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Не удалось загрузить исследования',
      life: 5000,
    })
  }
}

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

const viewResearch = (id: string) => {
  router.push({ name: 'research-detail', params: { id } })
}

const deleteResearch = (id: string, title: string) => {
  confirm.require({
    message: `Вы уверены, что хотите удалить исследование "${title}"?`,
    header: 'Подтверждение удаления',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await researchStore.remove(id)
        toast.add({
          severity: 'success',
          summary: 'Успешно',
          detail: 'Исследование удалено',
          life: 3000,
        })
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Ошибка',
          detail: 'Не удалось удалить исследование',
          life: 5000,
        })
      }
    },
  })
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<template>
    <div class="p-4">
      <!-- Statistics Widgets -->
      <div class="grid mb-4">
        <div class="col-12 lg:col-6 xl:col-3">
          <div class="card mb-0">
            <div class="flex justify-content-between mb-3">
              <div>
                <span class="block text-500 font-medium mb-3">Всего исследований</span>
                <div class="text-900 font-medium text-xl">{{ totalResearches }}</div>
              </div>
              <div class="flex align-items-center justify-content-center bg-blue-100 border-round" style="width: 2.5rem; height: 2.5rem">
                <i class="pi pi-chart-bar text-blue-500 text-xl"></i>
              </div>
            </div>
            <span class="text-green-500 font-medium">{{ authStore.user?.full_name || 'Пользователь' }}</span>
          </div>
        </div>
        <div class="col-12 lg:col-6 xl:col-3">
          <div class="card mb-0">
            <div class="flex justify-content-between mb-3">
              <div>
                <span class="block text-500 font-medium mb-3">Черновики</span>
                <div class="text-900 font-medium text-xl">{{ draftCount }}</div>
              </div>
              <div class="flex align-items-center justify-content-center bg-orange-100 border-round" style="width: 2.5rem; height: 2.5rem">
                <i class="pi pi-file-edit text-orange-500 text-xl"></i>
              </div>
            </div>
            <span class="text-500">Ожидают запуска</span>
          </div>
        </div>
        <div class="col-12 lg:col-6 xl:col-3">
          <div class="card mb-0">
            <div class="flex justify-content-between mb-3">
              <div>
                <span class="block text-500 font-medium mb-3">В процессе</span>
                <div class="text-900 font-medium text-xl">{{ inProgressCount }}</div>
              </div>
              <div class="flex align-items-center justify-content-center bg-cyan-100 border-round" style="width: 2.5rem; height: 2.5rem">
                <i class="pi pi-spin pi-spinner text-cyan-500 text-xl"></i>
              </div>
            </div>
            <span class="text-500">Анализ данных</span>
          </div>
        </div>
        <div class="col-12 lg:col-6 xl:col-3">
          <div class="card mb-0">
            <div class="flex justify-content-between mb-3">
              <div>
                <span class="block text-500 font-medium mb-3">Завершено</span>
                <div class="text-900 font-medium text-xl">{{ completedCount }}</div>
              </div>
              <div class="flex align-items-center justify-content-center bg-green-100 border-round" style="width: 2.5rem; height: 2.5rem">
                <i class="pi pi-check-circle text-green-500 text-xl"></i>
              </div>
            </div>
            <span class="text-green-500 font-medium">Готово к скачиванию</span>
          </div>
        </div>
      </div>

      <Card>
        <template #title>
          <div class="flex justify-content-between align-items-center">
            <span>Мои исследования</span>
            <Button
              label="Новое исследование"
              icon="pi pi-plus"
              @click="router.push({ name: 'research-create' })"
            />
          </div>
        </template>
        <template #content>
          <DataTable
            v-if="!researchStore.loading"
            :value="researchStore.researches"
            :rows="10"
            :paginator="true"
            :loading="researchStore.loading"
            responsive-layout="scroll"
          >
            <template #empty>
              <div class="text-center py-5">
                <p class="text-xl mb-3">У вас пока нет исследований</p>
                <Button
                  label="Создать первое исследование"
                  icon="pi pi-plus"
                  @click="router.push({ name: 'research-create' })"
                />
              </div>
            </template>

            <Column field="title" header="Название" :sortable="true">
              <template #body="{ data }">
                <div class="font-semibold">{{ data.title }}</div>
                <div class="text-sm text-600">{{ data.industry }}</div>
              </template>
            </Column>

            <Column field="region" header="Регион" :sortable="true" />

            <Column field="status" header="Статус" :sortable="true">
              <template #body="{ data }">
                <Tag :value="getStatusLabel(data.status)" :severity="getStatusSeverity(data.status)" />
              </template>
            </Column>

            <Column field="created_at" header="Создано" :sortable="true">
              <template #body="{ data }">
                {{ formatDate(data.created_at) }}
              </template>
            </Column>

            <Column header="Действия">
              <template #body="{ data }">
                <div class="flex gap-2">
                  <Button
                    icon="pi pi-eye"
                    size="small"
                    outlined
                    @click="viewResearch(data.id)"
                  />
                  <Button
                    icon="pi pi-trash"
                    size="small"
                    severity="danger"
                    outlined
                    @click="deleteResearch(data.id, data.title)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>

          <div v-else class="flex flex-column gap-3">
            <Skeleton height="4rem" v-for="i in 5" :key="i" />
          </div>
        </template>
      </Card>
    </div>
</template>
