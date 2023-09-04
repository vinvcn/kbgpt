<template>
  <div class="details-view">
    <el-page-header @back="goBack">
      <template #content>
        <span class="text-large font-600 mr-3">
          Question #{{ item.id }}: {{ item.question }}
        </span>
      </template>
    </el-page-header>
    <el-row>
      <el-col :span="6"><div class="grid-content ep-bg-purple" /></el-col>
    </el-row>
    <el-row>
      <el-col :span="1">
        <el-button class="prev-btn" @click="prev">
          <el-icon :size="40"><ArrowLeftBold /></el-icon>
        </el-button>
      </el-col>
      <el-col :span="11">
        <el-card shadow="never" class="box-card">
          <div>
            <div v-for="(step, index) in item.steps" :key="index">
              <p>#{{ index }} : {{ step.node_id }}</p>
              <p>{{ step.result }}</p>
              <el-radio-group
                v-model="ratings[index]"
                @change="saveOptions(index)"
              >
                <el-radio label="0">Bad</el-radio>
                <el-radio label="1">Good</el-radio>
              </el-radio-group>
              <el-divider border-style="dashed" />
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="1">
        <el-button class="prev-btn" @click="next">
          <el-icon :size="40"><ArrowRightBold /></el-icon>
        </el-button>
      </el-col>
    </el-row>
  </div>
  <el-dialog v-model="showPrompt" :show-close="false">
    <template #header="{ close, titleId, titleClass }">
      <div class="my-header">
        <h4 :id="titleId" :class="titleClass">{{ showPromptHeader }}</h4>
        <el-button type="confirm" @click="close">
          <el-icon class="el-icon--left"><CircleCloseFilled /></el-icon>
          Close
        </el-button>
      </div>
    </template>
    {{ showPromptContent }}
  </el-dialog>
</template>


  <script>
import { get_base_url } from "@/utils/utils";
export default {
  name: "DetailsView",
  data() {
    return {
      question_id: "",
      item: {}, // Fill with your data based on the id from route params.
      selectedOption: null,
      comment: "",
      ratings: [],
      showPrompt: false,
      showPromptHeader: "",
      showPromptContent: ""
    };
  },
  mounted() {
    this.$nextTick(() => {
      this.question_id = this.$route.query.id;
    });
  },
  watch: {
    "$route.query": "queryChange",
    question_id(newVal) {
      const rater = this.$route.query.rater;
      fetch(`${get_base_url()}/api/v1/tune/rate/rating/${newVal}/${rater}`)
        .then((resp) => resp.json())
        .then((data) => {
          this.item = data;
          const newRatings = this.item.steps.map(function (item) {
            if (item.rating === undefined) {
              return "";
            } else {
              return item.rating.toString();
            }
          });
          for (let i = 0; i < newRatings.length; i++) {
            this.ratings[i] = newRatings[i];
          }
        });
    },
  },
  methods: {
    handleShowPrompt(index){
      this.showPromptHeader = this.item.steps[index].node_id
      this.showPromptContent = this.item.steps[index].prompt
    },
    goBack() {
      const query = this.$route.query;
      console.log(query);
      this.$router.push({
        name: "Home",
        query: { ...query },
      });
    },
    queryChange() {
      this.turn({ question_id: this.$route.query.id });
    },
    turn(data) {
      if (data.question_id) {
        this.question_id = data.question_id;
        this.$router.push({
          name: "Details",
          query: { ...this.$route.query, id: data.question_id },
        });
      }
    },
    next() {
      fetch(
        `${get_base_url()}/api/v1/tune/rate/next_rating?` +
          new URLSearchParams({ ...this.$route.query })
      )
        .then((resp) => resp.json())
        .then((data) => {
          this.turn(data);
        });
    },
    prev() {
      fetch(
        `${get_base_url()}/api/v1/tune/rate/prev_rating?` +
          new URLSearchParams({ ...this.$route.query })
      )
        .then((resp) => resp.json())
        .then((data) => {
          this.turn(data);
        });
    },
    saveOptions(index) {
      fetch(`${get_base_url()}/api/v1/tune/rate/rating`, {
        method: "PUT",
        headers: {
          "Content-Type": "APPLICATION/JSON",
        },
        body: JSON.stringify({
          question_id: this.question_id,
          rater: this.$route.query.rater,
          invoke_id: this.item.invoke_id,
          node_id: this.item.steps[index].node_id,
          rating: this.ratings[index],
        }),
      }).catch((error) => alert(error));
      // Handle the user's selected option here.
    },
  },
};
</script>
  
<style scoped>
.button-row {
  display: flex;
  justify-content: space-between;
}
.prev-btn {
  width: 100%;
  height: 100%;
  border: none;
}
</style>