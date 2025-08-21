import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// app.registerExtension({
//   name: "CBZ.DisplayTextNode",
//   async beforeRegisterNodeDef(nodeType, nodeData, app) {
//     if (nodeData.name !== "Display Text") return;

//     const onNodeCreated = nodeType.prototype.onNodeCreated;
//     nodeType.prototype.onNodeCreated = function () {
//       if (onNodeCreated) onNodeCreated.call(this);

//       // Create a multiline STRING widget
//       this.displayWidget = ComfyWidgets.STRING(this, "Output", ["STRING", { multiline: true }], app).widget;
//       this.displayWidget.inputEl.readOnly = true;

//       // Optional: Reset serialized value to avoid clutter in workflow save
//       this.displayWidget.serializeValue = async () => "";
//     };

//     const onExecuted = nodeType.prototype.onExecuted;
//     nodeType.prototype.onExecuted = function (message) {
//       if (onExecuted) onExecuted.call(this, message);

//       if (this.displayWidget && message?.text?.[0]) {
//         this.displayWidget.value = message.text[0];
//         console.debug("[Display Text Node] Received text:", message.text[0]);
//       } else {
//         console.warn("[Display Text Node] No text found in message:", message);
//       }
//     };
//   }
// });

// Utility constants
const LAYOUT_LABEL_TO_DATA = {
  "Left": { x: 0, y: 0.5 },
  "Right": { x: 1, y: 0.5 },
  "Top": { x: 0.5, y: 0 },
  "Bottom": { x: 0.5, y: 1 },
};

const LAYOUT_LABEL_OPPOSITES = {
  "Left": "Right",
  "Right": "Left",
  "Top": "Bottom",
  "Bottom": "Top",
};

function getConnectionPosForLayout(node, isInput, slotNumber, out) {
  const layout = node.properties?.connections_layout ?? ["Left", "Right"];
  const layoutIn = LAYOUT_LABEL_TO_DATA[layout[0]] ?? LAYOUT_LABEL_TO_DATA["Left"];
  const layoutOut = LAYOUT_LABEL_TO_DATA[layout[1]] ?? LAYOUT_LABEL_TO_DATA["Right"];

  const count = isInput ? node.inputs?.length : node.outputs?.length;
  const delta = 1 / (count || 1);
  const yOffset = delta * (slotNumber + 0.5);

  const x = isInput ? layoutIn.x : layoutOut.x;
  const y = isInput ? layoutIn.y : layoutOut.y;

  out[0] = node.pos[0] + x * node.size[0];
  out[1] = node.pos[1] + y * node.size[1];

  if ((isInput && layoutIn.y === 0.5) || (!isInput && layoutOut.y === 0.5)) {
    out[1] = node.pos[1] + yOffset * node.size[1];
  }

  return out;
}

function addMenuItem(nodeType, app, { name, property, subMenuOptions, prepareValue, callback }) {
  const origContextMenu = nodeType.prototype.getExtraMenuOptions;
  nodeType.prototype.getExtraMenuOptions = function (_, options) {
    if (origContextMenu) origContextMenu.call(this, _, options);

    options.push({
      content: name,
      has_submenu: true,
      submenu: subMenuOptions.map((option) => ({
        content: option,
        callback: () => {
          const prepared = prepareValue(option, this);
          this.properties = this.properties || {};
          this.properties[property] = prepared;
          callback?.(this);
        },
      })),
    });

    return options;
  };
}

function addConnectionLayoutSupport(node, app, options = [["Left", "Right"], ["Right", "Left"]], callback) {
  addMenuItem(node, app, {
    name: "Connections Layout",
    property: "connections_layout",
    subMenuOptions: options.map((option) => option[0] + (option[1] ? " -> " + option[1] : "")),
    prepareValue: (value, node) => {
      const values = String(value).split(" -> ");
      if (!values[1] && !node.outputs?.length) {
        values[1] = LAYOUT_LABEL_OPPOSITES[values[0]];
      }
      if (!LAYOUT_LABEL_TO_DATA[values[0]] || !LAYOUT_LABEL_TO_DATA[values[1]]) {
        throw new Error(`New Layout invalid: [${values[0]}, ${values[1]}]`);
      }
      return values;
    },
    callback: (node) => {
      callback && callback(node);
      node.graph?.setDirtyCanvas(true, true);
    },
  });

  node.prototype.getConnectionPos = function (isInput, slotNumber, out) {
    return getConnectionPosForLayout(this, isInput, slotNumber, out);
  };
  node.prototype.getInputPos = function (slotNumber) {
    return getConnectionPosForLayout(this, true, slotNumber, [0, 0]);
  };
  node.prototype.getOutputPos = function (slotNumber) {
    return getConnectionPosForLayout(this, false, slotNumber, [0, 0]);
  };
}

app.registerExtension({
  name: "cbz.PreviewAny",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name === "CBZ Preview Any") {
      const origCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        origCreated?.apply(this, []);
        this.showValueWidget = ComfyWidgets["STRING"](
          this,
          "output",
          ["STRING", { multiline: true }],
          app
        ).widget;
        this.showValueWidget.inputEl.readOnly = true;
        this.showValueWidget.serializeValue = async (node, index) => {
          if (node.widgets_values) {
            node.widgets_values[index] = "";
          }
          return "";
        };
      };

      nodeType.prototype.onExecuted = function (message) {
        this.showValueWidget.value = message.text?.[0] ?? "No Output";
      };

      addConnectionLayoutSupport(nodeType, app);
    }
  },
});
