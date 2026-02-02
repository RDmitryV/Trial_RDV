<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useResearchStore } from '@/stores/research'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import AppLayout from '@/components/common/AppLayout.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Card from 'primevue/card'
import Skeleton from 'primevue/skeleton'
import { ResearchStatus } from '@/types'

const router = useRouter()
const researchStore = useResearchStore()
const toast = useToast()
const confirm = useConfirm()

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
  <AppLayout>
    <div class="p-4">
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
  </AppLayout>
</template>
