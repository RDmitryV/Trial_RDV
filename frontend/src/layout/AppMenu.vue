<script setup>
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppMenuItem from './AppMenuItem.vue';

const authStore = useAuthStore();

const model = computed(() => {
    const items = [
        {
            label: 'Главная',
            items: [
                {
                    label: 'Dashboard',
                    icon: 'pi pi-fw pi-home',
                    to: '/dashboard'
                }
            ]
        },
        {
            label: 'Исследования',
            items: [
                {
                    label: 'Мои исследования',
                    icon: 'pi pi-fw pi-list',
                    to: '/dashboard'
                },
                {
                    label: 'Новое исследование',
                    icon: 'pi pi-fw pi-plus',
                    to: '/research/new'
                }
            ]
        }
    ];

    // Add admin section if user is admin
    if (authStore.isAdmin) {
        items.push({
            label: 'Администрирование',
            items: [
                {
                    label: 'Пользователи',
                    icon: 'pi pi-fw pi-users',
                    to: '/admin'
                }
            ]
        });
    }

    return items;
});
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
            <li v-if="item.separator" class="menu-separator"></li>
        </template>
    </ul>
</template>

<style lang="scss" scoped></style>
