import DetailsView from "@/components/QuestionDetailsView.vue";
import ListView from "@/components/QuestionListView.vue";
import SSEChatBox from "@/components/SSEChatBox.vue";
import { createRouter, createWebHashHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Home",
    component: ListView,
  },
  {
    path: "/details",
    name: "Details",
    component: DetailsView,
  },
  {
    path: "/chat",
    name: "Chat",
    component: SSEChatBox,
  }
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  trailingSlash: false,
});

export default router;
