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
              <p>Step #{{ index }} : {{ step.node_id }}</p>
              <p>{{ step.result }}</p>
              <div class="link-wrapper">
                <el-link type="primary" @click="debugPromptDialog(index)"
                  >Show Prompt >></el-link
                >
              </div>
              <el-form :model="forms[index]">
                <el-form-item label="Rating:">
                  <el-radio-group v-model="forms[index].rating">
                    <el-radio label="0">Bad</el-radio>
                    <el-radio label="1">Good</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="Comment:">
                  <el-input v-model="forms[index].comment" type="textarea" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="onSubmit(index)"
                    >Save</el-button
                  >
                </el-form-item>
              </el-form>

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
  <el-dialog v-model="debugPrompt" :show-close="true" align-center>
    <template #header>
      <div class="my-header">
        Step #{{ promptIndex }} : {{ item.steps[promptIndex].node_id }}
      </div>
    </template>

    <el-form>
      <p>Baseline Result:</p>
      <pre
        >{{ item.steps[promptIndex].result }}
    </pre
      >
      <p>Prompt Content:</p>
      <el-form-item>
        <el-input
          :autosize="{ minRows: 10, maxRows: 20 }"
          v-model="item.steps[promptIndex].prompt"
          type="textarea"
        />
      </el-form-item>

    </el-form>
    <p>Run Result:</p>
    <pre>{{ item.steps[promptIndex].debugResult }}</pre>
    <!-- <p class="guide-wrapper">
      Guide: Copy and paste the new prompt and save it as comment.
    </p> -->
    <template #footer>
      <span class="dialog-footer">
        <el-select
            v-model="debugModel"
            placeholder="Select Your User Name:"
          >
            <el-option
              v-for="item in openaiModels"
              :key="item"
              :label="item"
              :value="item"
            >
              {{ item }}
            </el-option>
          </el-select>
        <el-button ref="runBtn" type="primary" @click="forwardPrompt(promptIndex)"> Run </el-button>
        <el-button @click="debugPrompt = false"> Close </el-button>
      </span>
    </template>
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
      forms: [],
      debugPrompt: false,
      promptIndex: "",
      debugModel: "gpt-4",
      openaiModels: ["gpt-4","gpt-3.5-turbo","gpt-3.5-turbo-16k"]
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
          const forms = this.item.steps.map(function (item) {
            const rst = {};
            if (item.rating === undefined) {
              rst.rating = "";
            } else {
              rst.rating = item.rating.toString();
            }
            rst.comment = item.comment;
            return rst;
          });
          this.forms = forms;
          // for (let i = 0; i < forms.length; i++) {
          //   this.ratings[i] = forms[i];
          // }
        });
    },
  },
  methods: {
    debugPromptDialog(index) {
      this.debugPrompt = true;
      this.promptIndex = index;
    },
    forwardPrompt(promptIndex) {
      const prompt = this.item.steps[promptIndex].prompt
      fetch(`${get_base_url()}/api/v1/tune/rate/forward_prompt`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(
          {
            prompt:prompt,
            model:this.debugModel,
          }
        )
      }).then((resp) => resp.json())
      .then(data => {
        this.item.steps[promptIndex].debugResult = data.result
        this.$refs.runBtn.disabled = !(this.$refs.runBtn.disabled)
      }).catch(err => {
        alert(`forwarding prompt got error ${err}`)
      });
      this.$refs.runBtn.disabled = !(this.$refs.runBtn.disabled)
    },

    handledebugPrompt(index) {
      this.debugPromptHeader = this.item.steps[index].node_id;
      this.debugPromptContent = this.item.steps[index].prompt;
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
    onSubmit(index) {
      console.log(this.forms);
      console.log(this.forms[index]);
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
          rating:
            this.forms[index].rating === undefined
              ? ""
              : this.forms[index].rating,
          comment:
            this.forms[index].comment === undefined
              ? ""
              : this.forms[index].comment,
        }),
      })
        .then((resp) => resp.json())
        .then((data) => {
          if (data.success) {
            this.forms[index].success = true;
          }
        })
        .catch((error) => alert(error));
      // Handle the user's selected option here.
    },
  },
};
</script>
  
<style scoped>
pre {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  overflow-x: auto;
  white-space: pre-wrap;
  white-space: -moz-pre-wrap;
  white-space: -pre-wrap;
  white-space: -o-pre-wrap;
  word-wrap: break-word;
}
.guide-wrapper {
  display: flex;
  justify-content: flex-start;
}

.link-wrapper {
  display: flex;
  justify-content: flex-end;
}
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