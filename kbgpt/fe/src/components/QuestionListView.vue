<template>
  <div>
    <el-menu class="el-menu-question-list" @select="handleSelect">
      <el-menu-item
        v-for="(item, index) in items"
        :key="index"
        @click="goToDetailsPage(item.id)"
      >
        <div class="menu-item-content">{{ item.id }} - {{ item.question }}</div>
      </el-menu-item>
    </el-menu>
    <el-row justify="center">
      <div class="button-row">
        <span v-for="number in getRange()" :key="number">
          <el-link v-if="number == $route.query.page" type="primary" disabled
            >[{{ number }}]</el-link
          >
          <el-link
            @click="goToPage(number)"
            v-else-if="number == 1 || number == maxPage"
            >{{ number }}</el-link
          >
          <el-link v-else>{{ number }}</el-link>
        </span>
      </div>
    </el-row>
    <el-row justify="center">
      <div class="button-row">
        <el-button type="primary" :icon="ArrowLeft" @click="backwardPage">
          <el-icon><ArrowLeftBold /></el-icon>
          Prev Page
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

  mounted: async function () {
    this.fetchPage();
  },
  methods: {
    getRange() {
      const start = 1;
      const end = this.maxPage;
      const totalArr = Array(end - start + 1)
        .fill()
        .map((_, idx) => start + idx);
      const showingArr = totalArr.filter(
        (item) =>
          item == 1 || item == this.maxPage || item == this.$route.query.page
      );
      const resultArr = [...showingArr];
      switch (resultArr.length) {
        case 0:
        case 1:
          return resultArr;
        case 2:
          if (resultArr[0] + 1 < resultArr[1]) {
            resultArr.splice(1, 0, "...");
          }
          return resultArr;
        default:
          if (resultArr[1] + 1 < resultArr[2]) {
            resultArr.splice(2, 0, "...");
          }
          if (resultArr[0] + 1 < resultArr[1]) {
            resultArr.splice(1, 0, "...");
          }
          return resultArr;
      }
    },
    goToDetailsPage(id) {
      this.$router.push({
        name: "Details",
        query: { ...this.$route.query, id: id },
      });
    },
    goToPage(page) {
      if (page <= 0 || page > this.maxPage) {
        return;
      } else {
        this.$router.push({
          name: "Home",
          query: { ...this.$route.query, page: page },
        });
      }
    },
    forwardPage() {
      const page = Number(this.$route.query.page);
      if (page + 1 > this.maxPage) {
        return;
      } else {
        this.$router.push({
          name: "Home",
          query: { ...this.$route.query, page: page + 1 },
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
          query: { ...this.$route.query, page: page - 1 },
        });
      }
    },
    fetchMaxPage: async function () {
      const resp = await fetch(
        `${get_base_url()}/api/v1/tune/rate/max_page/${
          this.$route.query.rater
        }/${this.$route.query.rating}`
      );
      if (!resp.ok) {
        alert(
          `fetching max page failed with ${resp.status} ${resp.statusText}`
        );
      } else {
        const data = await resp.json();
        this.maxPage = data.max_page;
        this.$route.query.maxId = data.max_id;
        this.$route.query.minId = data.min_id;
        this.$route.query.qcount = data.cnt;
      }
    },
    fetchPage: async function() {
      console.log(this.$route.query);
      await this.fetchMaxPage()
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
            this.items = [];
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
div.button-row a {
  margin-right: 10px;
}
/* div.button-row el-button{
  margin-right: 10px;
} */
.tag-section {
  margin-left: auto;
}
p.noMargin {
  margin: 0;
}
</style>