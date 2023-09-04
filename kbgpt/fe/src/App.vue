<template>
  <div id="app">
    <el-header>
      <el-row type="flex" justify="space-between">
        <el-col :span="4">
          <el-link @click="goHome">Data Labeling Center </el-link></el-col
        >
        <el-col :span="4">
          <span>Your User Name:</span>
          <el-select
            v-model="selectedRater"
            placeholder="Select Your User Name:"
          >
            <el-option
              v-for="item in raters"
              :key="item.name"
              :label="item.name"
              :value="item.name"
            >
              {{ item.name }}
            </el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
        <span>Filter:</span>
        <el-radio-group v-model="showRatings">
          <el-radio label="all">All</el-radio>
          <el-radio label="unrated">Unrated</el-radio>
          <el-radio label="rated">Rated</el-radio>
        </el-radio-group>
      </el-col>
        <el-col :span="4">
          <el-link type="primary" @click="dialogVisible = true"
            >Create New User</el-link
          >
        </el-col>
      </el-row>
    </el-header>
    <el-dialog title="Create New User" v-model="dialogVisible">
      <el-input v-model="newRater" placeholder="Enter new user name"></el-input>

      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="addRater">Create</el-button>
      </template>
    </el-dialog>
    <router-view />
  </div>
</template>

<script>
import { get_base_url } from "@/utils/utils";

// const dialogFormVisible = ref(false)
export default {
  name: "App",
  data() {
    return {
      showRatings: "all",
      raters: [],
      selectedRater: null,
      newRater: "",
      dialogVisible: false,
    };
  },
  mounted: async function () {
    await this.fetchRaters();
  },
  watch: {
    showRatings(newVal) {
      const query = this.$route.query;
      this.$router.push({ name: "Home", query: { ...query, rating: newVal } });
    },
    selectedRater(newVal) {
      const query = this.$route.query;
      if (newVal) {
        this.$router.push({
          name: "Home",
          query: { ...query, rater: newVal, page: 1 },
        });
      }
    },
  },
  methods: {
    goHome(){
      const query = this.$route.query;
      console.log(query);
      this.$router.push({
        name: "Home",
        query: { ...query },
      });
    },
    addRater() {
      if (!this.newRater) {
        return;
      }
      fetch(`${get_base_url()}/api/v1/tune/rate/rater`, {
        method: "PUT",
        headers: {
          "Content-Type": "APPLICATION/JSON",
        },
        body: JSON.stringify({ name: this.newRater }),
      })
        .then(() => {
          this.$nextTick(() => {
            this.selectedRater = this.newRater;
            this.dialogVisible = false;
          });
        })
        .catch((error) => alert(`create rater caught error ${error}`));
    },
    async fetchRaters() {
      const resp = await fetch(`${get_base_url()}/api/v1/tune/rate/list_rater`);
      if (!resp.ok) {
        alert(
          `fetching rater list failed with ${resp.status} ${resp.statusText}`
        );
      } else {
        const data = await resp.json();
        if (data.raters) {
          this.raters = data.raters;
          const raters = this.raters.map(function (item) {
            return item.name;
          });
          const defaultRater = raters[0];
          if (this.$route.query) {
            if (this.$route.query.rater) {
              if (raters.includes(this.$route.query.rater)) {
                this.selectedRater = this.$route.query.rater;
                return;
              }
            }
          }
          this.selectedRater = defaultRater;
        }
      }
    },
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
}
</style>