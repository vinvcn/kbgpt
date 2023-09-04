<template>
  <div>

    <el-menu class="el-menu-question-list" @select="handleSelect">
      <el-menu-item
        v-for="(item, index) in items"
        :key="index"
        @click="goToDetailsPage(item.id)"
      >
        <div class="menu-item-content">
          {{ item.id }} - {{ item.question }}
        </div>
      </el-menu-item>
    </el-menu>
    <el-row justify="center">
      <div class="button-row">
        <el-button type="primary" :icon="ArrowLeft" @click="backwardPage">
          <el-icon><ArrowLeftBold /></el-icon>
          Previous Page
        </el-button>
        <el-button type="primary" @click="forwardPage">
          Next Page <el-icon><ArrowRightBold /></el-icon
        ></el-button>
      </div>
    </el-row>
  </div>
</template>
  
<script>
import { get_base_url } from "@/utils/utils";
export default {
  name: "ListView",
  data: function () {
    return {
      items: [{ id: 1, question: "questions" }],
      maxPage: 0,
    };
  },
  watch: {
    "$route.query": "fetchPage",
  },
  created: async function () {
    this.fetchPage();
    await this.fetchMaxPage();
  },
  methods: {
    goToDetailsPage(id) {
      this.$router.push({
        name: "Details",
        query: { id: id, ...this.$route.query },
      });
    },
    forwardPage() {
      const page = Number(this.$route.query.page);
      if (page + 1 > this.maxPage) {
        return;
      } else {
        this.$router.push({
          name: "Home",
          query: { ...this.$route.query.page, page: page + 1 },
        });
      }
    },
    backwardPage() {
      const page = Number(this.$route.query.page);
      if (page - 1 <= 0) {
        return;
      } else {
        this.$router.push({
          name: "Home",
          query: { ...this.$route.query.page, page: page - 1 },
        });
      }
    },
    fetchMaxPage: async function () {
      const resp = await fetch(`${get_base_url()}/api/v1/tune/rate/max_page`);
      if (!resp.ok) {
        alert(
          `fetching max page failed with ${resp.status} ${resp.statusText}`
        );
      } else {
        const data = await resp.json();
        this.maxPage = data.max_page;
      }
    },
    fetchPage() {
      console.log(this.$route.query)
      fetch(
        `${get_base_url()}/api/v1/tune/rate/list_rating?` +
          new URLSearchParams({
            ...this.$route.query,
          }),
        {
          method: "GET",
        }
      )
        .then((resp) => resp.json())
        .then((data) => {
          if (data && data.questions) {
            this.items = data.questions;
          } else {
            this.items = []
          }
        })
        .catch((err) => alert("fetch error " + err));
    },
  },
};
</script>
  
<style>
.el-menu-question-list {
  background-color: #eeee;
  color: #999;
}
.el-menu-question-list :active {
  background-color: #999;
  /* color: #ffd04b */
}
.el-menu-question-list :hover {
  background-color: #ddd;
}
.menu-item-content {
  display: flex;
  align-items: center;
}

.tag-section {
  margin-left: auto;
}
</style>