import { createRouter, createWebHistory } from 'vue-router'

import AdminDashboardView from '@/views/AdminDashboardView.vue'
import GuardConsoleView from '@/views/GuardConsoleView.vue'
import GuestManagementView from '@/views/GuestManagementView.vue'
import PassManagementView from '@/views/PassManagementView.vue'
import UserManagementView from '@/views/UserManagementView.vue'
import VehicleManagementView from '@/views/VehicleManagementView.vue'
import MyPassView from '@/views/MyPassView.vue'
import FaceEnrollmentView from '@/views/FaceEnrollmentView.vue'
import GateManagementView from '@/views/GateManagementView.vue'
import RoleUpgradeReviewView from '@/views/RoleUpgradeReviewView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/guard' },
    { path: '/guard', component: GuardConsoleView, meta: { title: 'Guard Console' } },
    { path: '/admin/dashboard', component: AdminDashboardView, meta: { title: 'Admin Dashboard' } },
    { path: '/admin/users', component: UserManagementView, meta: { title: 'Users' } },
    { path: '/admin/vehicles', component: VehicleManagementView, meta: { title: 'Vehicles' } },
    { path: '/admin/passes', component: PassManagementView, meta: { title: 'Passes' } },
    { path: '/admin/face', component: FaceEnrollmentView, meta: { title: 'Face Enrollment' } },
    { path: '/admin/gates', component: GateManagementView, meta: { title: 'Gates' } },
    { path: '/admin/upgrades', component: RoleUpgradeReviewView, meta: { title: 'Role Upgrades' } },
    { path: '/admin/guest', component: GuestManagementView, meta: { title: 'Guest Management' } },
    { path: '/portal/mypass', component: MyPassView, meta: { title: 'My Pass' } },
  ],
})

router.afterEach((to) => {
  if (to.meta?.title) {
    document.title = 'SmartGate | ' + String(to.meta.title)
  }
})

export default router
