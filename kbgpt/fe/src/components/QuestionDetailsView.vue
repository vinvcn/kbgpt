<template>
  <div class="details-view">
    <el-page-header @back="goBack">
      <template #content>
        <span class="text-large font-600 mr-3">
          Question #{{ this.questionIndex }} (ID {{ item.id }}):
          {{ item.question }}
        </span>
      </template>
    </el-page-header>
    <el-row justify="center">
      <el-col :span="6"> </el-col>
    </el-row>
    <el-row>
      <el-col :span="1">
        <el-button class="prev-btn" @click="prev">
          <el-icon :size="40"><ArrowLeftBold /></el-icon>
        </el-button>
      </el-col>
      <el-col :span="11">
        <!-- <el-row justify="center">
          <div class="button-row">
            <span v-for="number in this.validQuestionIds" :key="number">
              <el-link v-if="number == $route.query.id" type="primary" disabled
                >[{{ number }}]</el-link
              >
              <el-link
                @click="goToPage(number)"
                v-else-if="
                  number == $route.query.minId || number == $route.query.maxId
                "
                >{{ number }}</el-link
              >
              <el-link v-else>{{ number }}</el-link>
            </span>
          </div>
        </el-row> -->
        <el-row justify="center">
          <el-card shadow="never" class="box-card" style="width: 100%">
            <div>
              <div v-for="(step, index) in item.steps" :key="index">
                <p>Step #{{ index }} : {{ step.node_id }}</p>
                <p>{{ step.result }}</p>
                <div class="link-wrapper">
                  <el-link type="primary" @click="debugPromptDialog(index)"
                    >Debug Prompt >></el-link
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
                    <el-input
                      autosize
                      v-model="forms[index].comment"
                      type="textarea"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="onSaveRating(index)"
                      >Save</el-button
                    >
                  </el-form-item>
                </el-form>

                <el-divider border-style="dashed" />
              </div>
            </div> </el-card
        ></el-row>
      </el-col>
      <el-col :span="1">
        <el-button class="prev-btn" @click="next">
          <el-icon :size="40"><ArrowRightBold /></el-icon>
        </el-button>
      </el-col>
      <el-col :span="1">
        <p>Question List:</p>
        <el-scrollbar height="600px" ref="questionIndexScrollBar">
          <el-row
            v-for="(idx, rindex) in genRange(
              0,
              this.validQuestionIds.length / 2
            )"
            :key="rindex"
          >
            <span
              class="noMargin"
              v-for="cindex in genRange(1, 3)"
              :key="cindex"
            >
              <el-link
                v-if="idx * 2 + cindex == this.questionIndex"
                type="primary"
                disabled
                ref="activeQuestionIndex"
              >
                [{{ idx * 2 + cindex }}]
              </el-link>
              <el-link
                v-else-if="idx * 2 + cindex <= this.validQuestionIds.length"
                @click="
                  turn({
                    question_id: this.validQuestionIds[idx * 2 + cindex - 1],
                  })
                "
                >{{ idx * 2 + cindex }}</el-link
              >
            </span>
          </el-row>
        </el-scrollbar>
      </el-col>
    </el-row>
  </div>
  <el-dialog v-model="debugPrompt.visible" :show-close="true" align-center>
    <template #header>
      <div class="my-header">
        Step #{{ debugPrompt.promptIndex }} : {{ debugPrompt.content.node_id }}
      </div>
    </template>

    <el-form>
      <p>Baseline Result:</p>
      <pre
        >{{ item.steps[debugPrompt.promptIndex].result }}
    </pre
      >
      <p>Prompt Content:</p>
      <el-form-item>
        <el-input
          :autosize="{ minRows: 10, maxRows: 20 }"
          v-model="editingPrompt"
          type="textarea"
        />
      </el-form-item>
    </el-form>
    <p>Run Result:</p>
    <pre>{{ editingResult }}</pre>
    <!-- <p class="guide-wrapper">
      Guide: Copy and paste the new prompt and save it as comment.
    </p> -->
    <template #footer>
      <span class="dialog-footer">
        <el-select v-model="debugModel" placeholder="Select Your User Name:">
          <el-option
            v-for="item in openaiModels"
            :key="item"
            :label="item"
            :value="item"
          >
            {{ item }}
          </el-option>
        </el-select>
        <el-button
          v-loading.fullscreen.lock="fullscreenLoading"
          element-loading-background="rgba(0, 0, 0, 0.7)"
          ref="runBtn"
          type="primary"
          @click="forwardPrompt()"
        >
          Run
        </el-button>
        <el-button @click="onSavePrompt()"> Save </el-button>
        <el-button @click="debugPrompt.visible = false"> Close </el-button>
      </span>
    </template>
  </el-dialog>
</template>


  <script>
import { get_base_url } from "@/utils/utils";
import { ElMessage } from "element-plus";

export default {
  name: "DetailsView",
  data() {
    return {
      fullscreenLoading: false,
      validQuestionIds: [],
      pageIndex: "",
      question_id: "",
      item: {}, // Fill with your data based on the id from route params.
      selectedOption: null,
      comment: "",
      forms: [],
      debugPrompt: {
        visible: false,
        promptIndex: "",
        content: {},
      },
      openaiModels: ["gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
    };
  },
  computed: {
    // page: {
    //   get() {
    //     return this.$route.query.id - this.$route.query.minId + 1;
    //   },
    //   set(newVal) {
    //     const newId = Number(this.$route.query.minId) + Number(newVal) - 1;
    //     console.log(newId);
    //     this.turn({ question_id: newId });
    //   },
    // },
    questionIndex: function () {
      return this.validQuestionIds.indexOf(this.item.id) + 1;
    },
    editingPrompt: {
      get() {
        if (this.debugPrompt.content.rater_prompt) {
          return this.debugPrompt.content.rater_prompt;
        } else {
          return this.item.steps[this.debugPrompt.promptIndex].prompt;
        }
      },
      set(newValue) {
        this.debugPrompt.content.rater_prompt = newValue;
      },
    },
    editingResult: {
      get() {
        console.log(this.debugPrompt.content);
        return this.debugPrompt.content.rater_result
          ? this.debugPrompt.content.rater_result
          : this.item.steps[this.debugPrompt.promptIndex].result;
      },
      set(newValue) {
        this.debugPrompt.content.rater_result = newValue;
      },
    },
    debugModel: {
      get() {
        return this.debugPrompt.content.debug_model
          ? this.debugPrompt.content.debug_model
          : this.openaiModels[0];
      },
      set(newVal) {
        this.debugPrompt.content.debug_model = newVal;
      },
    },
  },
  created() {
    fetch(
      `${get_base_url()}/api/v1/tune/rate/all_questions?` +
        new URLSearchParams({
          ...this.$route.query,
        }),
      {
        method: "GET",
      }
    )
      .then((resp) => resp.json())
      .then((data) => (this.validQuestionIds = data))
      .catch((err) => alert(`fetching all questions got error ${err}`));
  },
  updated(){
    this.$nextTick(() => {
    })
  },
  mounted() {
    this.$nextTick(() => {
      this.question_id = this.$route.query.id;
      // this.$refs.activeQuestionIndex.scrollIntoView({behavior: 'smooth'});
    });
  },
  watch: {
    "$route.query": "queryChange",
    "debugPrompt.promptIndex": function (newVal, oldVal) {
      console.log(oldVal);
      console.log(newVal);
      const content = {
        question_id: this.$route.query.id,
        rater: this.$route.query.rater,
        invoke_id: this.item.steps[newVal].invoke_id,
        node_id: this.item.steps[newVal].node_id,
      };
      this.debugPrompt.content = content;

      fetch(`${get_base_url()}/api/v1/tune/rate/prompt`, {
        method: "POST",
        headers: {
          "Content-Type": "APPLICATION/JSON",
        },
        body: JSON.stringify({
          ...content,
        }),
      })
        .then((resp) => resp.json())
        .then((data) => {
          if (data.success) {
            this.debugPrompt.content = data;
          }
        })
        .catch((err) =>
          alert(`fetching rater editing prompt got error ${err}`)
        );
    },
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
            rst.rater_prompt = item.rater_prompt;
            rst.rater_result = item.rater_result;
            return rst;
          });
          this.forms = forms;
        });
    },
  },
  methods: {
    genRange(start, end) {
      return Array(Math.ceil(end) - Math.ceil(start))
        .fill()
        .map((_, idx) => start + idx);
    },
    debugPromptDialog(index) {
      this.debugPrompt.visible = true;
      this.debugPrompt.promptIndex = index;
    },
    forwardPrompt() {
      this.fullscreenLoading = true;
      const prompt = this.editingPrompt;
      fetch(`${get_base_url()}/api/v1/tune/rate/forward_prompt`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: prompt,
          model: this.debugModel,
        }),
      })
        .then((resp) => resp.json())
        .then((data) => {
          this.editingResult = data.result;
          this.$refs.runBtn.disabled = !this.$refs.runBtn.disabled;
        })
        .catch((err) => {
          alert(`forwarding prompt got error ${err}`);
        })
        .finally(() => {
          this.fullscreenLoading = false;
        });
      this.$refs.runBtn.disabled = !this.$refs.runBtn.disabled;
    },
    onSavePrompt() {
      fetch(`${get_base_url()}/api/v1/tune/rate/prompt`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...this.debugPrompt.content,
        }),
      })
        .then((resp) => resp.json())
        .then(() => {
          ElMessage({
            showClose: true,
            message: "Prompt Saved",
            type: "success",
          });
        })
        .catch((err) => alert(`saving prompt got error ${err}`))
        .finally(() => {});
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
    onSaveRating(index) {
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
        .then(() => {
          ElMessage({
            showClose: true,
            message: "Rating Saved",
            type: "success",
          });
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
span.noMargin {
  margin-right: 10px;
}
</style>