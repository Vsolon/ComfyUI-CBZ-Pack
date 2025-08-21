import { app } from '@/scripts/app'
import { ComfyWidgets } from '@/scripts/widgets'

app.registerExtension({
  name: 'Comfy.DirToCBZPassthrough',
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === 'DirToCBZPassthrough') {
      console.log('[DirToCBZPassthrough] Hooking into node:', nodeData.name)

      const onNodeCreated = nodeType.prototype.onNodeCreated
      nodeType.prototype.onNodeCreated = function () {
        console.log('[DirToCBZPassthrough] onNodeCreated')

        if (onNodeCreated) {
          onNodeCreated.apply(this, [])
        }

        const widgetConfig = ['STRING', { multiline: true }]
        const result = ComfyWidgets['STRING'](this, 'preview', widgetConfig, app)
        const previewWidget = result?.widget

        if (previewWidget) {
          console.log('[DirToCBZPassthrough] Preview widget created')
          previewWidget.element.readOnly = true
          previewWidget.serialize = false
        } else {
          console.warn('[DirToCBZPassthrough] Failed to create preview widget')
        }

        if (this.addCustomWidget && previewWidget) {
          this.addCustomWidget(previewWidget)
        }
      }

      const onExecuted = nodeType.prototype.onExecuted
      nodeType.prototype.onExecuted = function (message) {
        console.log('[DirToCBZPassthrough] onExecuted message:', message)

        if (onExecuted) {
          onExecuted.apply(this, [message])
        }

        const previewWidget = this.widgets?.find(w => w.name === 'preview')
        if (previewWidget) {
          const text = message?.text?.[0] ?? '[No text returned from backend]'
          previewWidget.value = text
          console.log('[DirToCBZPassthrough] Updated preview text:', text)
        } else {
          console.warn('[DirToCBZPassthrough] Preview widget not found')
        }
      }
    }
  }
})
