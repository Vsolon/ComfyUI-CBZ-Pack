// DisplayTextNode.ts
import { app } from '@/scripts/app'
import { DOMWidget } from '@/scripts/domWidget'
import { ComfyWidgets } from '@/scripts/widgets'
import { useExtensionService } from '@/services/extensionService'

useExtensionService().registerExtension({
  name: 'Comfy.DirToCBZPassthrough',
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === 'DirToCBZPassthrough') {
      const onNodeCreated = nodeType.prototype.onNodeCreated
      nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, [])

        const showValueWidget = ComfyWidgets['STRING'](
          this,
          'preview',
          ['STRING', { multiline: true }],
          app
        ).widget as DOMWidget

        showValueWidget.element.readOnly = true
        showValueWidget.serialize = false
      }

      const onExecuted = nodeType.prototype.onExecuted
      nodeType.prototype.onExecuted = function (message) {
        onExecuted?.apply(this, [message])

        const previewWidget = this.widgets?.find((w) => w.name === 'preview')
        if (previewWidget && message?.text?.[0]) {
          previewWidget.value = message.text[0]
        }
      }
    }
  },
})
