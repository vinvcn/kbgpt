<template>
  <div class="container" style="display: flex">
    <div>
      Chat
      <SSEChatBox></SSEChatBox>
    </div>
    <!-- <div>
      Knowledge Base
      <KnowledgeBox></KnowledgeBox>
    </div> -->
  </div>
</template>

<script>
// import KnowledgeBox from "./components/KnowledgeBox.vue";
import SSEChatBox from "./components/SSEChatBox.vue";

export default {
  name: "App",
  components: {
    SSEChatBox,
    // KnowledgeBox,
  },
};
</script>

<style>
div.container {
  font-family: Arial, sans-serif;
}
</style>