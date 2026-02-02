<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/common/AppLayout.vue'
import Card from 'primevue/card'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Message from 'primevue/message'

const systemStats = ref({
  totalUsers: 0,
  activeResearches: 0,
  completedResearches: 0,
  systemUptime: '99.9%',
})
</script>

<template>
  <AppLayout>
    <div class="p-4">
      <Card>
        <template #title>Административная панель</template>
        <template #content>
          <TabView>
            <TabPanel header="Статистика">
              <div class="grid">
                <div class="col-12 md:col-6 lg:col-3">
                  <Card>
                    <template #content>
                      <div class="flex flex-column align-items-center">
                        <i class="pi pi-users text-4xl text-primary mb-2"></i>
                        <span class="text-2xl font-bold">{{ systemStats.totalUsers }}</span>
                        <span class="text-600">Всего пользователей</span>
                      </div>
                    </template>
                  </Card>
                </div>
                <div class="col-12 md:col-6 lg:col-3">
                  <Card>
                    <template #content>
                      <div class="flex flex-column align-items-center">
                        <i class="pi pi-sync text-4xl text-blue-500 mb-2"></i>
                        <span class="text-2xl font-bold">{{ systemStats.activeResearches }}</span>
                        <span class="text-600">Активных исследований</span>
                      </div>
                    </template>
                  </Card>
                </div>
                <div class="col-12 md:col-6 lg:col-3">
                  <Card>
                    <template #content>
                      <div class="flex flex-column align-items-center">
                        <i class="pi pi-check-circle text-4xl text-green-500 mb-2"></i>
                        <span class="text-2xl font-bold">{{
                          systemStats.completedResearches
                        }}</span>
                        <span class="text-600">Завершенных исследований</span>
                      </div>
                    </template>
                  </Card>
                </div>
                <div class="col-12 md:col-6 lg:col-3">
                  <Card>
                    <template #content>
                      <div class="flex flex-column align-items-center">
                        <i class="pi pi-server text-4xl text-purple-500 mb-2"></i>
                        <span class="text-2xl font-bold">{{ systemStats.systemUptime }}</span>
                        <span class="text-600">Uptime системы</span>
                      </div>
                    </template>
                  </Card>
                </div>
              </div>
            </TabPanel>

            <TabPanel header="Пользователи">
              <Message severity="info">
                Управление пользователями будет реализовано в следующей версии
              </Message>
            </TabPanel>

            <TabPanel header="Мониторинг">
              <Message severity="info">
                Инструменты мониторинга будут добавлены в следующей версии
              </Message>
            </TabPanel>

            <TabPanel header="Настройки">
              <Message severity="info">
                Настройки системы будут добавлены в следующей версии
              </Message>
            </TabPanel>
          </TabView>
        </template>
      </Card>
    </div>
  </AppLayout>
</template>
