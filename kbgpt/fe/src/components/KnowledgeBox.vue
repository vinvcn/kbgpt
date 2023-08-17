<template>
  <div>
    <div class="uploadPanel">
      <div>
        Choose the files to upload:
        <input
          type="file"
          multiple
          accept=".kb.txt,.txt,.doc,.docx"
          @change="handleFileUpload"
        />
        <button @click="uploadFile">Upload</button>
      </div>
      <div class="controls">
        <label>
          <input type="radio" value="qa" v-model="business_type" />
          Q/A Knowledge Base
        </label>
        <label>
          <input type="radio" value="product" v-model="business_type" />
          Product Category
        </label>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "KnowledgeBox",
  data() {
    return {
      business_type: "qa",
      files: [],
    };
  },
  methods: {
    loadQAIndexVerstion() {
      
    },
    handleFileUpload(event) {
      this.files = Array.from(event.target.files);
    },
    uploadFile() {
      const formData = new FormData();
      this.files.forEach((file) => {
        formData.append("file", file);
      });
      formData.set("business_type", this.business_type);

      fetch(`${window.location.origin}/api/v1/aigc/qa/process_file`, {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          // Handle response
          console.log(data);
        })
        .catch((error) => {
          // Handle error
          console.error(error);
        });
    },
  },
};
</script>
<style>
.uploadPanel {
  border: 1px solid #ccc;
  background-color: #fff;
  padding: 20px;
  width: 600px;
}
</style>