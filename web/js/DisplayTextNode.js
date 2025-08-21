import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
  name: "CBZ.DisplayTextNode",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name !== "Display Text") return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      if (onNodeCreated) onNodeCreated.call(this);

      // Create a multiline STRING widget
      this.displayWidget = ComfyWidgets.STRING(this, "Output", ["STRING", { multiline: true }], app).widget;
      this.displayWidget.inputEl.readOnly = true;

      // Optional: Reset serialized value to avoid clutter in workflow save
      this.displayWidget.serializeValue = async () => "";
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      if (onExecuted) onExecuted.call(this, message);

      if (this.displayWidget && message?.text?.[0]) {
        this.displayWidget.value = message.text[0];
        console.debug("[Display Text Node] Received text:", message.text[0]);
      } else {
        console.warn("[Display Text Node] No text found in message:", message);
      }
    };
  }
});
